import pytest
from jinja2 import TemplateNotFound, UndefinedError

from app.llm.schemas import BgpIntent
from app.llm.service import build_prompt
from prompts.loader import load_prompt

FULL = {
    "target_asn": "3356",
    "prefixes": ["192.0.2.0/24"],
    "from_time": "2020-01-01 00:00:00",
    "until_time": "2020-01-02 00:00:00",
    "collectors": ["rrc00"],
    "collection_duration": 300,
}


def test_renders_params_into_template():
    out = load_prompt("hijacking", **FULL)
    assert 'asn = "3356"' in out
    assert "192.0.2.0/24" in out


def test_base_setup_included_in_type_template():
    out = load_prompt("prefix", **FULL)
    assert "pybgpstream" in out  # from the shared base setup
    assert 'target_asn = "3356"' in out


def test_unknown_template_raises():
    with pytest.raises(TemplateNotFound):
        load_prompt("does_not_exist", **FULL)


def test_missing_var_raises():
    with pytest.raises(UndefinedError):
        load_prompt("base_setup")  # references target_asn/from_time, none passed


def test_build_prompt_routes_by_provider():
    intent = BgpIntent(analysis_type="hijacking", target_asn="3356")
    assert "hijack" in build_prompt("gpt", intent).lower()
    # LLaMA always uses the shared base setup, regardless of analysis type
    llama = build_prompt("llama", intent)
    assert "pybgpstream" in llama
    assert "hijack" not in llama.lower()
