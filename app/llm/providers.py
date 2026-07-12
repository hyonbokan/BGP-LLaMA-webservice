from dataclasses import dataclass, field

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class ProviderConfig:
    """Connection + sampling settings for one OpenAI-compatible backend."""

    model: str
    api_key: str
    base_url: str | None = None  # None => OpenAI's default (api.openai.com/v1)
    # None => omit from the request. Reasoning models (GPT) ignore these, so the
    # GPT provider leaves them unset; the fine-tuned LLaMA still sets both.
    temperature: float | None = None
    max_tokens: int | None = None
    # "chat" hits /v1/chat/completions (system+user, chat template applied
    # server-side). "completion" hits /v1/completions with one raw prompt —
    # matches how the fine-tuned LLaMA was trained (no chat template).
    mode: str = "chat"
    # Extra sampling params the OpenAI schema doesn't cover (e.g. vLLM's
    # repetition_penalty), forwarded verbatim via the request's extra_body.
    extra_body: dict = field(default_factory=dict)
    # Estimated-token budget for threaded conversation history before older
    # turns are summarized away. Sized to the backend's context window.
    history_max_tokens: int = 100_000


def _openai_provider(s: Settings) -> ProviderConfig:
    return ProviderConfig(
        model=s.openai_model,
        api_key=s.openai_api_key,
        base_url=s.openai_base_url or None,
        # No temperature/max_tokens: reasoning models ignore them (left as None => not sent).
        mode="chat",
        history_max_tokens=s.gpt_history_max_tokens,
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
        history_max_tokens=s.llama_history_max_tokens,
    )


_PROVIDERS = {"gpt": _openai_provider, "llama": _llama_provider}


def get_provider(name: str) -> ProviderConfig:
    factory = _PROVIDERS.get(name)
    if factory is None:
        raise ValueError(f"Unknown LLM provider {name!r}; expected one of {sorted(_PROVIDERS)}")
    return factory(get_settings())
