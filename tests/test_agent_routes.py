import asyncio
from types import SimpleNamespace

import pytest

import app.api.routes.agent as agent_route
import app.llm.agent as agent_mod
from app.llm.agent import PodError, Running, RunResult, _to_result, _workspace_source
from app.llm.schemas import BgpIntent

# --------------------------------------------------------------------------- #
# Route: /api/agent/run re-streams the pod run as SSE (run_agent is faked).
# --------------------------------------------------------------------------- #


def _fake_run(events):
    async def gen(query, prior_findings=None):
        for ev in events:
            yield ev

    return gen


def test_streams_agent_started_running_and_result(client, monkeypatch):
    events = [
        Running(),
        Running(),
        RunResult(
            text="AS3356 looks clean",
            is_error=False,
            subtype="success",
            total_cost_usd=0.004,
            duration_ms=1500,
            num_turns=3,
            structured_output=None,
        ),
    ]
    monkeypatch.setattr(agent_route, "run_agent", _fake_run(events))

    resp = client.post("/api/agent/run", json={"query": "analyze AS3356"})
    assert resp.status_code == 200
    body = resp.text
    assert '"status": "agent_started"' in body
    assert '"status": "running"' in body
    assert '"status": "result"' in body
    assert "AS3356 looks clean" in body
    assert '"subtype": "success"' in body


def test_error_event_on_pod_failure(client, monkeypatch):
    async def boom(query, prior_findings=None):
        raise PodError("could not reach the agent pod")
        yield  # pragma: no cover - makes this an async generator

    monkeypatch.setattr(agent_route, "run_agent", boom)

    resp = client.post("/api/agent/run", json={"query": "hi"})
    assert resp.status_code == 200  # SSE opened, error delivered as an event
    assert '"status": "error"' in resp.text
    assert "could not reach the agent pod" in resp.text


def test_prior_findings_forwarded(client, monkeypatch):
    seen = {}

    async def gen(query, prior_findings=None):
        seen["query"], seen["prior"] = query, prior_findings
        yield RunResult("ok", False, "success", None, None, None, None)

    monkeypatch.setattr(agent_route, "run_agent", gen)

    resp = client.post(
        "/api/agent/run",
        json={"query": "and now AS15169", "prior_findings": "AS3356 was clean"},
    )
    assert resp.status_code == 200
    assert seen["query"] == "and now AS15169"
    assert seen["prior"] == "AS3356 was clean"


def test_empty_query_rejected(client):
    assert client.post("/api/agent/run", json={"query": "   "}).status_code == 400


def test_missing_query_is_422(client):
    assert client.post("/api/agent/run", json={}).status_code == 422


# --------------------------------------------------------------------------- #
# Client helpers: workspace pointer + result parsing (pure).
# --------------------------------------------------------------------------- #


def test_workspace_source_is_none_when_dir_absent():
    assert _workspace_source("/definitely/not/here/xyz") is None


def test_workspace_source_points_at_existing_dir(tmp_path):
    assert _workspace_source(str(tmp_path)) == f"file://{tmp_path.resolve()}"


def test_to_result_reads_opencode_payload():
    result = _to_result(
        {
            "text": "hi",
            "is_error": False,
            "subtype": "success",
            "total_cost_usd": 0.01,
            "duration_ms": 900,
            "num_turns": 2,
            "structured_output": {"a": 1},
        }
    )
    assert result.text == "hi"
    assert result.num_turns == 2
    assert result.structured_output == {"a": 1}


def test_to_result_defaults_on_sparse_payload():
    result = _to_result({})
    assert result.text == "" and result.is_error is False and result.subtype is None


def test_agent_system_prompt_is_autonomous_and_tool_driven():
    from app.llm.agent import _agent_system_prompt
    from app.llm.schemas import BgpIntent, TimeWindow

    prompt = _agent_system_prompt(
        BgpIntent(
            target_asn="15169",
            prefixes=["8.8.8.0/24"],
            time_window=TimeWindow(from_time="2026-07-11 00:00:00", until_time="2026-07-11 00:20:00"),
        )
    )
    low = prompt.lower()
    # Autonomous (no clarifying questions) and driven by the fetch tool, not hand-written pybgpstream.
    assert "bgp_fetch_bgp_updates" in prompt
    assert "not write pybgpstream" in low
    assert "never ask" in low and "autonomous" in low
    # Parsed parameters are threaded into the prompt.
    assert "8.8.8.0/24" in prompt and "AS15169" in prompt


def test_agent_system_prompt_omits_parameter_block_when_empty():
    from app.llm.agent import _agent_system_prompt
    from app.llm.schemas import BgpIntent

    prompt = _agent_system_prompt(BgpIntent())
    assert "Parameters parsed from the request" not in prompt
    assert "bgp_fetch_bgp_updates" in prompt


# --------------------------------------------------------------------------- #
# Client: run_agent builds the pod body and parses the pod's SSE (httpx faked).
# --------------------------------------------------------------------------- #


class _FakeStreamCtx:
    def __init__(self, status_code, lines):
        self.status_code = status_code
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def aread(self):
        return b"pod error detail"


class _FakeClientCtx:
    def __init__(self, status_code, lines, capture):
        self._status, self._lines, self._capture = status_code, lines, capture

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def stream(self, method, url, json=None, headers=None):
        self._capture.update(method=method, url=url, json=json, headers=headers)
        return _FakeStreamCtx(self._status, self._lines)


def _collect(query, prior_findings=None):
    async def run():
        return [ev async for ev in agent_mod.run_agent(query, prior_findings)]

    return asyncio.run(run())


# The pod frames keep-alive as ":" comments and payloads as event:/data: pairs;
# aiter_lines yields each line without terminators and a bare "" between frames.
_POD_STREAM = [
    ": keep-alive",
    "",
    "event: cost",
    'data: {"total_cost_usd": 0.003, "duration_ms": 1200}',
    "",
    "event: done",
    'data: {"text": "done analyzing", "is_error": false, "subtype": "success",'
    ' "total_cost_usd": 0.003, "duration_ms": 1200, "num_turns": 4, "structured_output": null}',
    "",
]


def test_run_agent_parses_pod_stream_and_builds_body(monkeypatch):
    capture: dict = {}

    settings = SimpleNamespace(
        agent_pod_token="tok",
        agent_pod_url="http://pod:8080/",
        agent_model="gpt-5.4-mini-2026-03-17",
        agent_tool_list=["Bash", "Read", "Write"],
        agent_max_budget_usd=None,
        agent_request_timeout=600,
        bgp_data_root="/definitely/not/here/xyz",
    )
    monkeypatch.setattr(agent_mod, "get_settings", lambda: settings)

    async def fake_classify(query):
        return BgpIntent()

    monkeypatch.setattr(agent_mod, "classify_intent", fake_classify)
    monkeypatch.setattr(agent_mod, "_agent_system_prompt", lambda intent: "SYSTEM")
    monkeypatch.setattr(
        agent_mod.httpx, "AsyncClient", lambda *a, **k: _FakeClientCtx(200, _POD_STREAM, capture)
    )

    events = _collect("analyze AS3356")

    # A keep-alive tick then the terminal result.
    assert [type(e).__name__ for e in events] == ["Running", "RunResult"]
    result = events[-1]
    assert result.text == "done analyzing"
    assert result.num_turns == 4 and result.subtype == "success"

    # The body carries the rendered task, the tool allow-list, and the bearer token;
    # the URL joins cleanly and no workspace is sent when the data root is absent.
    assert capture["url"] == "http://pod:8080/agent/run"
    assert capture["headers"]["Authorization"] == "Bearer tok"
    body = capture["json"]
    assert body["model"] == "gpt-5.4-mini-2026-03-17"
    assert body["tools"] == ["Bash", "Read", "Write"]
    assert body["prompt"] == "analyze AS3356"
    assert body["system_prompt"] == "SYSTEM"
    assert "workspace" not in body


def test_run_agent_includes_workspace_when_data_root_exists(monkeypatch, tmp_path):
    capture: dict = {}
    settings = SimpleNamespace(
        agent_pod_token="tok",
        agent_pod_url="http://pod:8080",
        agent_model="gpt-5.4-mini-2026-03-17",
        agent_tool_list=["Bash", "Read", "Write"],
        agent_max_budget_usd=None,
        agent_request_timeout=600,
        bgp_data_root=str(tmp_path),
    )
    monkeypatch.setattr(agent_mod, "get_settings", lambda: settings)

    async def fake_classify(query):
        return BgpIntent()

    monkeypatch.setattr(agent_mod, "classify_intent", fake_classify)
    monkeypatch.setattr(agent_mod, "_agent_system_prompt", lambda intent: "SYSTEM")
    monkeypatch.setattr(
        agent_mod.httpx, "AsyncClient", lambda *a, **k: _FakeClientCtx(200, _POD_STREAM, capture)
    )

    _collect("analyze AS3356")
    assert capture["json"]["workspace"] == {
        "source": f"file://{tmp_path.resolve()}",
        "mode": "ro",
    }


def test_run_agent_raises_when_token_unset(monkeypatch):
    settings = SimpleNamespace(agent_pod_token="", agent_pod_url="http://pod:8080")
    monkeypatch.setattr(agent_mod, "get_settings", lambda: settings)
    with pytest.raises(PodError, match="AGENT_POD_TOKEN"):
        _collect("hi")


def test_run_agent_raises_on_non_200(monkeypatch):
    capture: dict = {}
    settings = SimpleNamespace(
        agent_pod_token="tok",
        agent_pod_url="http://pod:8080",
        agent_model="m",
        agent_tool_list=["Bash"],
        agent_max_budget_usd=None,
        agent_request_timeout=600,
        bgp_data_root="/nope/xyz",
    )
    monkeypatch.setattr(agent_mod, "get_settings", lambda: settings)

    async def fake_classify(query):
        return BgpIntent()

    monkeypatch.setattr(agent_mod, "classify_intent", fake_classify)
    monkeypatch.setattr(agent_mod, "_agent_system_prompt", lambda intent: "SYSTEM")
    monkeypatch.setattr(
        agent_mod.httpx, "AsyncClient", lambda *a, **k: _FakeClientCtx(401, [], capture)
    )

    with pytest.raises(PodError, match="pod returned 401"):
        _collect("hi")
