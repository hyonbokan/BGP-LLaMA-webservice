from app.core.config import Settings


def test_cors_origins_splits_and_trims_csv():
    s = Settings(_env_file=None, cors_allowed_origins="http://a, http://b ,, http://c")
    assert s.cors_origins == ["http://a", "http://b", "http://c"]


def test_cors_origins_single_value():
    s = Settings(_env_file=None, cors_allowed_origins="http://only")
    assert s.cors_origins == ["http://only"]


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
