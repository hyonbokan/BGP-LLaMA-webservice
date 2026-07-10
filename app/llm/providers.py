from dataclasses import dataclass, field
from typing import Optional

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class ProviderConfig:
    """Connection + sampling settings for one OpenAI-compatible backend."""

    model: str
    api_key: str
    base_url: Optional[str] = None  # None => OpenAI's default (api.openai.com/v1)
    temperature: float = 0.7
    max_tokens: int = 2000
    # "chat" hits /v1/chat/completions (system+user, chat template applied
    # server-side). "completion" hits /v1/completions with one raw prompt —
    # matches how the fine-tuned LLaMA was trained (no chat template).
    mode: str = "chat"
    # Extra sampling params the OpenAI schema doesn't cover (e.g. vLLM's
    # repetition_penalty), forwarded verbatim via the request's extra_body.
    extra_body: dict = field(default_factory=dict)


def _openai_provider(s: Settings) -> ProviderConfig:
    return ProviderConfig(
        model=s.openai_model,
        api_key=s.openai_api_key,
        base_url=s.openai_base_url or None,
        temperature=s.gpt_temperature,
        max_tokens=s.gpt_max_tokens,
        mode="chat",
    )


def _llama_provider(s: Settings) -> ProviderConfig:
    return ProviderConfig(
        model=s.llama_model,
        api_key=s.llama_api_key,
        base_url=s.llama_base_url,
        temperature=s.llama_temperature,
        max_tokens=s.llama_max_tokens,
        mode=s.llama_api_mode,
        extra_body={"repetition_penalty": s.llama_repetition_penalty},
    )


_PROVIDERS = {"gpt": _openai_provider, "llama": _llama_provider}


def get_provider(name: str) -> ProviderConfig:
    factory = _PROVIDERS.get(name)
    if factory is None:
        raise ValueError(f"Unknown LLM provider {name!r}; expected one of {sorted(_PROVIDERS)}")
    return factory(get_settings())
