"""Conversation memory: estimate history size and compact it when it grows large.

History is threaded into every chat request so the model can refine across turns.
Once the running conversation exceeds a provider's token budget, the oldest turns
are summarized into a single briefing (Claude-Code-style compaction) while the
most recent turns are kept verbatim. Token counts are *estimated* from character
length (~4 chars/token) so the slim API image needs no tokenizer dependency.

Compaction is best-effort: if the summarization call fails or no OpenAI key is
configured, it degrades to plain truncation (drop the oldest turns, keep the
recent ones) rather than failing the request.
"""

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.clients import get_client
from app.llm.providers import ProviderConfig, get_provider
from app.llm.schemas import Turn
from prompts.loader import load_prompt

logger = get_logger(__name__)

_CHARS_PER_TOKEN = 4

# Compaction always summarizes through the hosted GPT provider (reliable, and it
# keeps the summarization off the small local model even on the LLaMA path).
_SUMMARIZER_PROVIDER = "gpt"
_COMPACT_SYSTEM = load_prompt("compact_system")


@dataclass
class Compaction:
    """The outcome of compacting history before a request.

    `turns` is what to send to the model (recent turns, oldest dropped when
    compacted). `summary` is the briefing for the turns that were removed, or
    None when nothing was compacted or summarization was unavailable.
    `dropped` is how many turns were removed.
    """

    turns: list[Turn]
    summary: str | None
    dropped: int


def approx_tokens(text: str) -> int:
    """Estimate the token count of a string (~4 characters per token)."""
    return len(text) // _CHARS_PER_TOKEN


def conversation_tokens(turns: list[Turn]) -> int:
    """Estimate the token count of a list of turns."""
    return sum(approx_tokens(t.content) for t in turns)


async def compact_history(history: list[Turn], provider: str) -> Compaction:
    """Shrink `history` to fit the provider's budget, summarizing the overflow.

    Returns the turns to send, a summary of any dropped turns, and the drop
    count. When history already fits, it is returned unchanged.
    """
    cfg = get_provider(provider)
    if conversation_tokens(history) <= cfg.history_max_tokens:
        return Compaction(turns=history, summary=None, dropped=0)

    keep = max(0, get_settings().history_keep_recent_turns)
    recent = history[-keep:] if keep else []
    older = history[: len(history) - len(recent)]
    if not older:
        return Compaction(turns=recent, summary=None, dropped=0)

    summary = await _summarize(older, cfg)
    logger.debug(
        "compacted history provider=%s dropped=%d summarized=%s",
        provider,
        len(older),
        summary is not None,
    )
    return Compaction(turns=recent, summary=summary, dropped=len(older))


def _transcript(turns: list[Turn]) -> str:
    """Render turns as a plain speaker-labelled transcript for summarization."""
    labels = {"user": "User", "assistant": "Assistant"}
    return "\n\n".join(f"{labels.get(t.role, t.role)}: {t.content}" for t in turns)


async def _summarize(turns: list[Turn], cfg: ProviderConfig) -> str | None:
    """Summarize turns into a briefing, or None if summarization is unavailable."""
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    try:
        summarizer = get_provider(_SUMMARIZER_PROVIDER)
        client = get_client(summarizer.base_url, summarizer.api_key)
        completion = await client.chat.completions.create(
            model=settings.classifier_model or settings.openai_model,
            messages=[
                {"role": "system", "content": _COMPACT_SYSTEM},
                {"role": "user", "content": _transcript(turns)},
            ],
            temperature=0,
        )
        return completion.choices[0].message.content
    except Exception:
        logger.warning("History summarization failed; truncating instead", exc_info=True)
        return None
