from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.llm.providers import get_provider
from prompts.gpt_prompt_utils import GPT_REAL_TIME_SYSTEM_PROMPT
from prompts.llama_prompt_local_run import (
    BASE_SETUP,
    LOCAL_AS_PATH_ANALYSYS,
    LOCAL_DEFAULT,
    LOCAL_HIJACKING,
    LOCAL_OUTAGE,
)

logger = get_logger(__name__)


@lru_cache(maxsize=4)
def _client(base_url: Optional[str], api_key: str) -> AsyncOpenAI:
    """Cached AsyncOpenAI client per (base_url, key) so connections pool.

    max_retries=0 — the SSE routes surface failures to the client as an error
    event rather than silently retrying mid-stream.
    """
    return AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=get_settings().llm_request_timeout,
        max_retries=0,
    )


def _gpt_system_prompt(query: str) -> str:
    q = query.lower()
    if "real-time" in q:
        return GPT_REAL_TIME_SYSTEM_PROMPT
    if "hijacking" in q:
        return LOCAL_HIJACKING
    if "outage" in q:
        return LOCAL_OUTAGE
    if "as path" in q:
        return LOCAL_AS_PATH_ANALYSYS
    return LOCAL_DEFAULT


def select_system_prompt(provider: str, query: str) -> str:
    """Pick the system prompt for a provider. GPT routes by query intent; the
    fine-tuned LLaMA uses its training-time setup prompt."""
    if provider == "gpt":
        return _gpt_system_prompt(query)
    return BASE_SETUP


async def _stream_chat_completions(client, cfg, system_prompt, user_content):
    stream = await client.chat.completions.create(
        model=cfg.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        stream=True,
        **({"extra_body": cfg.extra_body} if cfg.extra_body else {}),
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        piece = getattr(chunk.choices[0].delta, "content", None)
        if piece:
            yield piece


async def _stream_text_completions(client, cfg, prompt):
    stream = await client.completions.create(
        model=cfg.model,
        prompt=prompt,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        stream=True,
        **({"extra_body": cfg.extra_body} if cfg.extra_body else {}),
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        piece = getattr(chunk.choices[0], "text", None)
        if piece:
            yield piece


async def stream_chat(provider: str, query: str, context: str = "") -> AsyncIterator[str]:
    """Stream assistant text for a provider ('gpt' or 'llama').

    Both hosted GPT and the local BGP-LLaMA (served by vLLM) speak the
    OpenAI-compatible API, so the only per-provider differences — base URL, key,
    model, sampling params, and chat-vs-completion mode — come from config.
    Yields text deltas.
    """
    cfg = get_provider(provider)
    system_prompt = select_system_prompt(provider, query)
    user_content = f"{context}\n\n{query}" if context else query
    logger.debug("stream provider=%s mode=%s model=%s", provider, cfg.mode, cfg.model)

    client = _client(cfg.base_url, cfg.api_key)
    if cfg.mode == "completion":
        # Fold the setup prompt and the user content into one raw prompt, the
        # way the fine-tune saw it at training time (no chat template).
        prompt = f"{system_prompt}\n\n{user_content}"
        gen = _stream_text_completions(client, cfg, prompt)
    else:
        gen = _stream_chat_completions(client, cfg, system_prompt, user_content)

    async for piece in gen:
        yield piece
