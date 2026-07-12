from app.core.config import Settings


def test_list_field_defaults_are_lists():
    s = Settings(_env_file=None)
    assert s.cors_allowed_origins == ["http://localhost:3000"]
    assert s.agent_tools == ["Bash", "Read", "Write"]


def test_list_fields_from_init_kwargs():
    s = Settings(
        _env_file=None,
        cors_allowed_origins=["http://a", "http://b"],
        agent_tools=["Bash"],
    )
    assert s.cors_allowed_origins == ["http://a", "http://b"]
    assert s.agent_tools == ["Bash"]


def test_list_fields_parse_json_array_from_env(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", '["http://x", "http://y"]')
    monkeypatch.setenv("AGENT_TOOLS", '["Read", "Write"]')
    s = Settings(_env_file=None)
    assert s.cors_allowed_origins == ["http://x", "http://y"]
    assert s.agent_tools == ["Read", "Write"]


def test_defaults():
    s = Settings(_env_file=None)
    assert s.log_level == "INFO"
    assert s.llama_api_mode == "completion"
    assert s.openai_base_url is None
    assert s.llm_request_timeout == 120


def test_classifier_defaults():
    s = Settings(_env_file=None)
    assert s.classifier_enabled is True
    assert s.classifier_model is None
