from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import get_settings


@lru_cache(maxsize=4)
def get_client(base_url: str | None, api_key: str) -> AsyncOpenAI:
    """Cached AsyncOpenAI client per (base_url, key) so connections pool.

    max_retries=0 — streaming routes surface failures to the caller as an error
    event rather than silently retrying mid-stream.
    """
    return AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=get_settings().llm_request_timeout,
        max_retries=0,
    )
