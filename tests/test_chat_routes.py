import app.api.routes.chat as chat_module
from app.llm.generation import Result, TextDelta
from app.llm.schemas import AnalysisType


def _fake_stream(events):
    async def gen(provider, query, context=""):
        for ev in events:
            yield ev

    return gen


def test_streams_generating_and_code_ready(client, monkeypatch):
    events = [
        TextDelta("Analyzing "),
        TextDelta("AS3356 ..."),
        Result(script="print('x')", analysis_type=AnalysisType.prefix),
    ]
    monkeypatch.setattr(chat_module, "stream_chat", _fake_stream(events))

    resp = client.get("/api/chat/bgp_gpt?query=hi")
    assert resp.status_code == 200
    body = resp.text
    assert '"status": "generating_started"' in body
    assert '"status": "generating"' in body
    assert '"status": "code_ready"' in body
    assert "print('x')" in body


def test_no_code_found(client, monkeypatch):
    events = [TextDelta("just prose"), Result(script=None, analysis_type=AnalysisType.knowledge)]
    monkeypatch.setattr(chat_module, "stream_chat", _fake_stream(events))

    resp = client.get("/api/chat/bgp_llama?query=hi")
    assert resp.status_code == 200
    assert '"status": "no_code_found"' in resp.text


def test_error_event_on_upstream_failure(client, monkeypatch):
    async def boom(provider, query, context=""):
        raise RuntimeError("upstream down")
        yield  # pragma: no cover - makes this an async generator

    monkeypatch.setattr(chat_module, "stream_chat", boom)

    resp = client.get("/api/chat/bgp_gpt?query=hi")
    assert resp.status_code == 200  # SSE opened, error delivered as an event
    assert '"status": "error"' in resp.text
    assert "upstream down" in resp.text


def test_empty_query_rejected(client):
    assert client.get("/api/chat/bgp_gpt?query=").status_code == 400


def test_missing_query_is_422(client):
    assert client.get("/api/chat/bgp_gpt").status_code == 422
