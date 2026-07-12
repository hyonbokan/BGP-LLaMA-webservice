"""Stream a BGP analysis as structured output.

The model returns a `BgpScript` — a natural-language `explanation` plus a
dedicated `script` field. `generate()` streams the `explanation` live (so the
user sees the analysis being written) and emits the parsed `script` at the end,
read straight off the structured object. No fenced-block regex.

It yields two event kinds: `TextDelta` for each new chunk of explanation text,
and a single terminal `Result` carrying the script and analysis type.

- GPT (chat mode) uses OpenAI structured-output streaming.
- LLaMA (completion mode) uses vLLM guided decoding (`guided_json`) over the raw
  completions endpoint, with the explanation extracted from the partial JSON.
  This path is unverified without a running vLLM and is off the fine-tune's
  training distribution — best-effort.
"""

import ast
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.clients import get_client
from app.llm.providers import ProviderConfig, get_provider
from app.llm.schemas import AnalysisType, BgpScript, Turn

logger = get_logger(__name__)

# The fine-tuned model reproduces the absolute data directory it was trained on
# (/home/<user>/ris_bgp_updates); this matches that prefix for any username so it
# can be rewritten to the configured data root before the script is returned.
_LEAKED_DATA_PATH = re.compile(r"/home/[\w.-]+/ris_bgp_updates")


def sanitize_script(script: str | None) -> str | None:
    """Rewrite a leaked personal data path in generated code to the configured root.

    Even when the prompt uses a neutral path, the fine-tuned model can emit the
    training directory baked into its weights; this keeps that path out of the
    returned script regardless of which model produced it.
    """
    if not script:
        return script
    return _LEAKED_DATA_PATH.sub(get_settings().bgp_data_root, script)


@dataclass
class TextDelta:
    """A newly produced chunk of the natural-language explanation."""

    text: str


@dataclass
class Compacted:
    """Signals that older conversation turns were compacted before this run."""

    dropped: int
    summarized: bool


@dataclass
class Result:
    """The terminal generation result: the script (or None) and the analysis type."""

    script: str | None
    analysis_type: AnalysisType


Event = TextDelta | Compacted | Result


def script_syntax_error(script: str | None) -> str | None:
    """Return a message if the script is not syntactically valid Python, else None.

    Parses only (never imports or runs), so it needs neither pybgpstream nor a
    network — it just catches truncated or malformed generations.
    """
    if not script:
        return None
    try:
        ast.parse(script)
    except SyntaxError as exc:
        return f"{exc.msg} (line {exc.lineno})"
    return None


async def generate(provider: str, system_prompt: str, turns: list[Turn]) -> AsyncIterator[Event]:
    """Stream `TextDelta`s of the explanation, then a terminal `Result`.

    `turns` is the conversation history plus the current query as the final
    user turn — the model sees prior turns so it can refine across the chat.
    """
    cfg = get_provider(provider)
    client = get_client(cfg.base_url, cfg.api_key)
    logger.debug("generate provider=%s mode=%s model=%s", provider, cfg.mode, cfg.model)

    if cfg.mode == "completion":
        gen = _generate_completion(client, cfg, system_prompt, turns)
    else:
        gen = _generate_chat(client, cfg, system_prompt, turns)
    async for event in gen:
        yield event


async def _generate_chat(
    client, cfg: ProviderConfig, system_prompt: str, turns: list[Turn]
) -> AsyncIterator[Event]:
    emitted = 0
    params: dict = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            *({"role": t.role, "content": t.content} for t in turns),
        ],
        "response_format": BgpScript,
    }
    # Only send sampling knobs when the provider set them — reasoning models (GPT)
    # leave them None and ignore/reject these. Chat models use `max_completion_tokens`,
    # not the legacy `max_tokens` (the vLLM completions path below still uses that).
    if cfg.temperature is not None:
        params["temperature"] = cfg.temperature
    if cfg.max_tokens is not None:
        params["max_completion_tokens"] = cfg.max_tokens
    async with client.beta.chat.completions.stream(**params) as stream:
        async for event in stream:
            if event.type != "content.delta":
                continue
            partial = getattr(event, "parsed", None)
            if isinstance(partial, dict):
                explanation = partial.get("explanation") or ""
                if len(explanation) > emitted:
                    yield TextDelta(explanation[emitted:])
                    emitted = len(explanation)
        final = await stream.get_final_completion()

    parsed = final.choices[0].message.parsed
    if parsed is None:
        logger.warning("Generation returned no parsed BgpScript")
        yield Result(script=None, analysis_type=AnalysisType.default)
        return
    if len(parsed.explanation) > emitted:
        yield TextDelta(parsed.explanation[emitted:])
    yield Result(script=sanitize_script(parsed.script), analysis_type=parsed.analysis_type)


async def _generate_completion(
    client, cfg: ProviderConfig, system_prompt: str, turns: list[Turn]
) -> AsyncIterator[Event]:
    # Fold setup + conversation into one raw prompt, the way the fine-tune saw
    # it, and constrain the output to the BgpScript schema via vLLM guided
    # decoding. A single-turn chat is just "{setup}\n\n{query}" as before.
    prompt = f"{system_prompt}\n\n{_flatten(turns)}"
    extra_body = dict(cfg.extra_body or {})
    extra_body["guided_json"] = BgpScript.model_json_schema()

    params: dict = {
        "model": cfg.model,
        "prompt": prompt,
        "stream": True,
        "extra_body": extra_body,
    }
    if cfg.temperature is not None:
        params["temperature"] = cfg.temperature
    if cfg.max_tokens is not None:
        params["max_tokens"] = cfg.max_tokens
    stream = await client.completions.create(**params)
    raw = ""
    emitted = 0
    async for chunk in stream:
        if not chunk.choices:
            continue
        piece = getattr(chunk.choices[0], "text", None)
        if not piece:
            continue
        raw += piece
        explanation = _partial_json_string(raw, "explanation")
        if explanation is not None and len(explanation) > emitted:
            yield TextDelta(explanation[emitted:])
            emitted = len(explanation)

    parsed = _safe_parse(raw)
    if parsed is None:
        yield Result(script=None, analysis_type=AnalysisType.default)
        return
    if len(parsed.explanation) > emitted:
        yield TextDelta(parsed.explanation[emitted:])
    yield Result(script=sanitize_script(parsed.script), analysis_type=parsed.analysis_type)


def _flatten(turns: list[Turn]) -> str:
    """Render conversation turns into one raw prompt block.

    A single user turn renders as just its content (the format the fine-tune was
    trained on); a multi-turn chat is rendered as a speaker-labelled transcript
    ending on the latest user turn.
    """
    if len(turns) == 1:
        return turns[0].content
    labels = {"user": "User", "assistant": "Assistant"}
    return "\n\n".join(f"{labels.get(t.role, t.role)}: {t.content}" for t in turns)


def _safe_parse(raw: str) -> BgpScript | None:
    """Parse the accumulated JSON into a `BgpScript`, or None if it is not valid."""
    try:
        return BgpScript.model_validate_json(raw)
    except ValueError:
        logger.warning("Could not parse structured generation output as BgpScript")
        return None


_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}


def _partial_json_string(raw: str, field: str) -> str | None:
    """Extract the value of a top-level string field from possibly-incomplete JSON.

    Returns the decoded characters available so far (the field's value may still
    be streaming), or None if the field's string has not started yet.
    """
    marker = f'"{field}"'
    start = raw.find(marker)
    if start == -1:
        return None
    colon = raw.find(":", start + len(marker))
    if colon == -1:
        return None
    i, n = colon + 1, len(raw)
    while i < n and raw[i] in " \t\r\n":
        i += 1
    if i >= n or raw[i] != '"':
        return None
    i += 1  # first content char

    out: list[str] = []
    while i < n:
        c = raw[i]
        if c == '"':
            break  # closing quote → string complete
        if c != "\\":
            out.append(c)
            i += 1
            continue
        # escape sequence
        if i + 1 >= n:
            break  # backslash still streaming
        nxt = raw[i + 1]
        if nxt in _ESCAPES:
            out.append(_ESCAPES[nxt])
            i += 2
        elif nxt == "u":
            if i + 6 > n:
                break  # \uXXXX still streaming
            try:
                out.append(chr(int(raw[i + 2 : i + 6], 16)))
            except ValueError:
                break
            i += 6
        else:
            break  # invalid escape
    return "".join(out)
