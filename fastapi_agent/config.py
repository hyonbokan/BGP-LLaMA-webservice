import os
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass(frozen=True)
class ProviderConfig:
    """Connection + sampling settings for one OpenAI-compatible backend."""

    model: str
    api_key: str
    base_url: Optional[str] = None  # None => OpenAI's default (api.openai.com/v1)
    temperature: float = 0.7
    max_tokens: int = 2000
    # "chat" hits /v1/chat/completions (system+user messages, chat template
    # applied server-side). "completion" hits /v1/completions with a single raw
    # prompt — matches how the fine-tuned LLaMA was trained (no chat template).
    mode: str = "chat"
    # Extra sampling params the OpenAI schema doesn't cover (e.g. vLLM's
    # repetition_penalty), forwarded verbatim via the request's extra_body.
    extra_body: dict = field(default_factory=dict)


# Shared HTTP timeout for both backends.
REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "120"))


def _openai_provider() -> ProviderConfig:
    """Hosted GPT via OpenAI (or any OpenAI-compatible gateway via OPENAI_BASE_URL)."""
    return ProviderConfig(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini-2026-03-17"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        temperature=float(os.getenv("GPT_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("GPT_MAX_TOKENS", "2000")),
    )


def _llama_provider() -> ProviderConfig:
    """Local fine-tuned BGP-LLaMA served by vLLM behind an OpenAI-compatible /v1 API.

    Self-hosted vLLM doesn't require an API key, but the OpenAI SDK still needs a
    non-empty placeholder, hence the "EMPTY" default.
    """
    return ProviderConfig(
        model=os.getenv("LLAMA_MODEL", "hyonbokan/bgp-llama-3.1-instruct-10kSteps-2kDataset"),
        api_key=os.getenv("LLAMA_API_KEY", "EMPTY"),
        base_url=os.getenv("LLAMA_BASE_URL", "http://host.docker.internal:8000/v1"),
        temperature=float(os.getenv("LLAMA_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", "912")),
        # Raw-completion by default so the served prompt matches the fine-tune's
        # training format; set LLAMA_API_MODE=chat if you serve with a chat template.
        mode=os.getenv("LLAMA_API_MODE", "completion"),
        extra_body={"repetition_penalty": float(os.getenv("LLAMA_REPETITION_PENALTY", "1.1"))},
    )


_PROVIDERS: Dict[str, Callable[[], ProviderConfig]] = {
    "gpt": _openai_provider,
    "llama": _llama_provider,
}


def get_provider(name: str) -> ProviderConfig:
    factory = _PROVIDERS.get(name)
    if factory is None:
        raise ValueError(f"Unknown LLM provider {name!r}; expected one of {sorted(_PROVIDERS)}")
    return factory()
