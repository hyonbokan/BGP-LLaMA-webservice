import asyncio

import app.llm.classifier as clf
from app.core.config import Settings
from app.llm.schemas import AnalysisType, BgpIntent


def _settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


class _FakeCompletions:
    """Stands in for client.beta.chat.completions with a stubbed parse()."""

    def __init__(self, result):
        self._result = result

    async def parse(self, **_kwargs):
        if isinstance(self._result, Exception):
            raise self._result
        message = type("Msg", (), {"parsed": self._result})()
        choice = type("Choice", (), {"message": message})()
        return type("Completion", (), {"choices": [choice]})()


class _FakeClient:
    def __init__(self, result):
        chat = type("Chat", (), {"completions": _FakeCompletions(result)})()
        self.beta = type("Beta", (), {"chat": chat})()


def test_heuristic_routing():
    assert clf._heuristic_intent("detect a hijacking").analysis_type is AnalysisType.hijacking
    assert clf._heuristic_intent("real-time monitor").analysis_type is AnalysisType.realtime
    assert clf._heuristic_intent("an outage happened").analysis_type is AnalysisType.outage
    assert clf._heuristic_intent("as path lengths").analysis_type is AnalysisType.as_path
    assert clf._heuristic_intent("something else").analysis_type is AnalysisType.default


def test_no_key_uses_heuristic(monkeypatch):
    monkeypatch.setattr(clf, "get_settings", lambda: _settings(openai_api_key=""))
    intent = asyncio.run(clf.classify_intent("detect a hijacking"))
    assert intent.analysis_type is AnalysisType.hijacking


def test_disabled_uses_heuristic(monkeypatch):
    monkeypatch.setattr(
        clf, "get_settings", lambda: _settings(openai_api_key="sk-x", classifier_enabled=False)
    )
    intent = asyncio.run(clf.classify_intent("an outage happened"))
    assert intent.analysis_type is AnalysisType.outage


def test_llm_success_returns_parsed_intent(monkeypatch):
    monkeypatch.setattr(clf, "get_settings", lambda: _settings(openai_api_key="sk-x"))
    want = BgpIntent(analysis_type="moas", target_asn="3356")
    monkeypatch.setattr(clf, "get_client", lambda *a, **k: _FakeClient(want))
    got = asyncio.run(clf.classify_intent("who else announces this prefix"))
    assert got.analysis_type is AnalysisType.moas
    assert got.target_asn == "3356"


def test_llm_failure_falls_back_to_heuristic(monkeypatch):
    monkeypatch.setattr(clf, "get_settings", lambda: _settings(openai_api_key="sk-x"))
    monkeypatch.setattr(clf, "get_client", lambda *a, **k: _FakeClient(RuntimeError("boom")))
    got = asyncio.run(clf.classify_intent("detect a hijacking"))
    assert got.analysis_type is AnalysisType.hijacking
