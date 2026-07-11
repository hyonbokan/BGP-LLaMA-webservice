import pytest

from app.core.config import Settings
from app.llm import providers
from app.llm.providers import get_provider


def test_openai_provider_maps_settings():
    s = Settings(
        _env_file=None,
        openai_model="m",
        openai_api_key="k",
        gpt_temperature=0.5,
        gpt_max_tokens=10,
    )
    cfg = providers._openai_provider(s)
    assert cfg.model == "m"
    assert cfg.api_key == "k"
    assert cfg.temperature == 0.5
    assert cfg.max_tokens == 10
    assert cfg.mode == "chat"
    assert cfg.base_url is None
    assert cfg.extra_body == {}


def test_llama_provider_carries_repetition_penalty():
    s = Settings(
        _env_file=None,
        llama_model="lm",
        llama_api_mode="completion",
        llama_repetition_penalty=1.2,
    )
    cfg = providers._llama_provider(s)
    assert cfg.model == "lm"
    assert cfg.mode == "completion"
    assert cfg.extra_body == {"repetition_penalty": 1.2}


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider("bogus")


def test_get_provider_dispatch(monkeypatch):
    monkeypatch.setattr(
        providers, "get_settings", lambda: Settings(_env_file=None, openai_model="x")
    )
    assert get_provider("gpt").model == "x"
    assert get_provider("llama").mode == "completion"
