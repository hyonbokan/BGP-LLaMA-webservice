import app.api.routes.chat as chat_module
from app.llm.generation import Compacted, Result, TextDelta
from app.llm.schemas import AnalysisType


def _fake_stream(events):
    async def gen(provider, query, history=None):
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

    resp = client.post("/api/chat/bgp_gpt", json={"query": "hi"})
    assert resp.status_code == 200
    body = resp.text
    assert '"status": "generating_started"' in body
    assert '"status": "generating"' in body
    assert '"status": "code_ready"' in body
    assert "print('x')" in body


def test_no_code_found(client, monkeypatch):
    events = [TextDelta("just prose"), Result(script=None, analysis_type=AnalysisType.knowledge)]
    monkeypatch.setattr(chat_module, "stream_chat", _fake_stream(events))

    resp = client.post("/api/chat/bgp_llama", json={"query": "hi"})
    assert resp.status_code == 200
    assert '"status": "no_code_found"' in resp.text


def test_compacted_event_emitted(client, monkeypatch):
    events = [
        Compacted(dropped=6, summarized=True),
        TextDelta("ok"),
        Result(script="print('x')", analysis_type=AnalysisType.prefix),
    ]
    monkeypatch.setattr(chat_module, "stream_chat", _fake_stream(events))

    resp = client.post("/api/chat/bgp_gpt", json={"query": "hi", "history": []})
    assert resp.status_code == 200
    assert '"status": "compacted"' in resp.text
    assert '"dropped": 6' in resp.text


def test_syntax_error_warns_but_ships_code(client, monkeypatch):
    events = [
        TextDelta("here"),
        Result(script="def broken(", analysis_type=AnalysisType.prefix),
    ]
    monkeypatch.setattr(chat_module, "stream_chat", _fake_stream(events))

    resp = client.post("/api/chat/bgp_gpt", json={"query": "hi"})
    assert resp.status_code == 200
    body = resp.text
    assert '"status": "code_ready"' in body
    assert '"warning"' in body


def test_history_is_forwarded(client, monkeypatch):
    seen = {}

    async def gen(provider, query, history=None):
        seen["history"] = history
        yield Result(script=None, analysis_type=AnalysisType.knowledge)

    monkeypatch.setattr(chat_module, "stream_chat", gen)

    resp = client.post(
        "/api/chat/bgp_gpt",
        json={
            "query": "and now for AS15169",
            "history": [
                {"role": "user", "content": "analyze AS3356"},
                {"role": "assistant", "content": "here is the analysis"},
            ],
        },
    )
    assert resp.status_code == 200
    assert [t.role for t in seen["history"]] == ["user", "assistant"]
    assert seen["history"][0].content == "analyze AS3356"


def test_error_event_on_upstream_failure(client, monkeypatch):
    async def boom(provider, query, history=None):
        raise RuntimeError("upstream down")
        yield  # pragma: no cover - makes this an async generator

    monkeypatch.setattr(chat_module, "stream_chat", boom)

    resp = client.post("/api/chat/bgp_gpt", json={"query": "hi"})
    assert resp.status_code == 200  # SSE opened, error delivered as an event
    assert '"status": "error"' in resp.text
    assert "upstream down" in resp.text


def test_empty_query_rejected(client):
    assert client.post("/api/chat/bgp_gpt", json={"query": "   "}).status_code == 400


def test_missing_query_is_422(client):
    assert client.post("/api/chat/bgp_gpt", json={}).status_code == 422
