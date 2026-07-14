import asyncio
from types import SimpleNamespace

import pytest

import app.api.routes.agent as agent_route
import app.llm.agent as agent_mod
from app.bgp.gather import GatherUnavailable
from app.llm.agent import (
    PodError,
    Running,
    RunResult,
    Token,
    ToolCall,
    _fallback_dir,
    _to_result,
)
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


def test_streams_token_and_tool_trace(client, monkeypatch):
    events = [
        ToolCall(id="b1", name="bash", status="running", input={"command": "ls"}, output=None),
        ToolCall(
            id="b1", name="bash", status="completed", input={"command": "ls"}, output="a\nb\n"
        ),
        Token(text="Origin "),
        Token(text="is AS15169."),
        RunResult("Origin is AS15169.", False, "success", 0.01, 900, 2, None),
    ]
    monkeypatch.setattr(agent_route, "run_agent", _fake_run(events))

    resp = client.post("/api/agent/run", json={"query": "analyze 8.8.8.0/24"})
    assert resp.status_code == 200
    body = resp.text
    assert '"status": "tool"' in body
    assert '"name": "bash"' in body
    assert '"state": "completed"' in body
    assert '"status": "token"' in body
    assert '"text": "Origin "' in body
    # The trace precedes the terminal result.
    assert body.index('"status": "tool"') < body.index('"status": "result"')


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


def test_fallback_dir_is_none_when_absent():
    settings = SimpleNamespace(bgp_data_root="/definitely/not/here/xyz", bgp_sample_data_root="")
    assert _fallback_dir(settings) is None


def test_fallback_dir_points_at_existing_dir(tmp_path):
    settings = SimpleNamespace(bgp_data_root=str(tmp_path), bgp_sample_data_root="")
    assert _fallback_dir(settings) == str(tmp_path.resolve())


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


def test_agent_system_prompt_is_autonomous_and_analyzes_staged_data():
    from app.llm.agent import _agent_system_prompt
    from app.llm.schemas import BgpIntent, TimeWindow

    prompt = _agent_system_prompt(
        BgpIntent(
            target_asn="15169",
            prefixes=["8.8.8.0/24"],
            time_window=TimeWindow(
                from_time="2026-07-11 00:00:00", until_time="2026-07-11 00:20:00"
            ),
        )
    )
    low = prompt.lower()
    # Autonomous (no clarifying questions); analyzes backend-staged data, does not fetch or hand-write
    # pybgpstream.
    assert "staged" in low
    assert "not fetch" in low and "not write pybgpstream" in low
    assert "never ask" in low and "autonomous" in low
    # Parsed parameters are threaded into the prompt.
    assert "8.8.8.0/24" in prompt and "AS15169" in prompt


def test_agent_system_prompt_omits_parameter_block_when_empty():
    from app.llm.agent import _agent_system_prompt
    from app.llm.schemas import BgpIntent

    prompt = _agent_system_prompt(BgpIntent())
    assert "Parameters the analysis was scoped to" not in prompt
    assert "staged" in prompt.lower()


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
        agent_tools=["Bash", "Read", "Write"],
        agent_max_budget_usd=None,
        agent_request_timeout=600,
        bgp_data_root="/definitely/not/here/xyz",
        bgp_sample_data_root="",
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


_POD_STREAM_WITH_TRACE = [
    "event: tool",
    'data: {"id": "b1", "name": "bash", "status": "running", "input": {"command": "ls"}}',
    "",
    "event: tool",
    'data: {"id": "b1", "name": "bash", "status": "completed", "input": {"command": "ls"},'
    ' "output": "a\\nb\\n"}',
    "",
    "event: token",
    'data: {"text": "Origin is AS15169."}',
    "",
    "event: cost",
    'data: {"total_cost_usd": 0.01, "duration_ms": 900}',
    "",
    "event: done",
    'data: {"text": "Origin is AS15169.", "is_error": false, "subtype": "success",'
    ' "total_cost_usd": 0.01, "duration_ms": 900, "num_turns": 2, "structured_output": null}',
    "",
]


def test_run_agent_parses_token_and_tool_trace(monkeypatch):
    capture: dict = {}
    settings = SimpleNamespace(
        agent_pod_token="tok",
        agent_pod_url="http://pod:8080",
        agent_model="m",
        agent_tools=["Bash"],
        agent_max_budget_usd=None,
        agent_request_timeout=600,
        bgp_data_root="/nope/xyz",
        bgp_sample_data_root="",
    )
    monkeypatch.setattr(agent_mod, "get_settings", lambda: settings)

    async def fake_classify(query):
        return BgpIntent()

    monkeypatch.setattr(agent_mod, "classify_intent", fake_classify)
    monkeypatch.setattr(agent_mod, "_agent_system_prompt", lambda intent: "SYSTEM")
    monkeypatch.setattr(
        agent_mod.httpx,
        "AsyncClient",
        lambda *a, **k: _FakeClientCtx(200, _POD_STREAM_WITH_TRACE, capture),
    )

    events = _collect("analyze 8.8.8.0/24")

    # Two tool transitions, one token chunk, then the terminal result — the cost tick is dropped.
    assert [type(e).__name__ for e in events] == ["ToolCall", "ToolCall", "Token", "RunResult"]
    running, completed, token, result = events
    assert (running.name, running.status, running.input) == ("bash", "running", {"command": "ls"})
    assert completed.status == "completed" and completed.output == "a\nb\n"
    assert token.text == "Origin is AS15169."
    assert result.text == "Origin is AS15169." and result.num_turns == 2


def test_run_agent_includes_workspace_when_data_root_exists(monkeypatch, tmp_path):
    capture: dict = {}
    settings = SimpleNamespace(
        agent_pod_token="tok",
        agent_pod_url="http://pod:8080",
        agent_model="gpt-5.4-mini-2026-03-17",
        agent_tools=["Bash", "Read", "Write"],
        agent_max_budget_usd=None,
        agent_request_timeout=600,
        bgp_data_root=str(tmp_path),
        bgp_sample_data_root="",
        workspace_transport="file",
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


def _scoped_settings(**overrides):
    base = {
        "agent_pod_token": "tok",
        "agent_pod_url": "http://pod:8080",
        "agent_model": "m",
        "agent_tools": ["Bash"],
        "agent_max_budget_usd": None,
        "agent_request_timeout": 600,
        "bgp_data_root": "/definitely/not/here/xyz",
        "bgp_sample_data_root": "",
        "workspace_transport": "file",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _wire_scoped_run(monkeypatch, settings):
    """Stub classify + prompt + pod stream for a scoped run; returns the capture dict."""
    capture: dict = {}
    monkeypatch.setattr(agent_mod, "get_settings", lambda: settings)

    async def fake_classify(query):
        return BgpIntent(prefixes=["1.1.1.0/24"])

    monkeypatch.setattr(agent_mod, "classify_intent", fake_classify)
    monkeypatch.setattr(agent_mod, "_agent_system_prompt", lambda intent: "SYSTEM")
    monkeypatch.setattr(
        agent_mod, "build_fetch_plan", lambda intent, s: object()
    )  # a gatherable plan
    monkeypatch.setattr(
        agent_mod.httpx, "AsyncClient", lambda *a, **k: _FakeClientCtx(200, _POD_STREAM, capture)
    )
    return capture


def test_run_agent_gathers_stages_and_reaps_scoped_workspace(monkeypatch, tmp_path):
    # A scoped query gathers live, stages the data as the workspace, and reaps it after the run.
    staged = tmp_path / "staged"
    staged.mkdir()
    capture = _wire_scoped_run(monkeypatch, _scoped_settings())

    async def fake_gather(plan, settings):
        return str(staged)

    reaped: list[str] = []
    monkeypatch.setattr(agent_mod, "gather_and_stage", fake_gather)
    monkeypatch.setattr(agent_mod, "reap_stage", lambda d: reaped.append(d))

    _collect("analyze 1.1.1.0/24")

    assert capture["json"]["workspace"] == {"source": f"file://{staged}", "mode": "ro"}
    assert reaped == [str(staged)]  # this run's staged dir is cleaned up


def test_run_agent_falls_back_to_static_root_when_gather_unavailable(monkeypatch, tmp_path):
    # No pybgpstream on the host: fall back to a statically staged BGP_DATA_ROOT, reaping nothing.
    capture = _wire_scoped_run(monkeypatch, _scoped_settings(bgp_data_root=str(tmp_path)))

    async def unavailable(plan, settings):
        raise GatherUnavailable("no pybgpstream")

    reaped: list[str] = []
    monkeypatch.setattr(agent_mod, "gather_and_stage", unavailable)
    monkeypatch.setattr(agent_mod, "reap_stage", lambda d: reaped.append(d))

    _collect("analyze 1.1.1.0/24")

    assert capture["json"]["workspace"] == {"source": f"file://{tmp_path.resolve()}", "mode": "ro"}
    assert reaped == []  # the static root is not this run's to delete


def test_run_agent_falls_back_to_bundled_sample_when_no_data_root(monkeypatch, tmp_path):
    # No pybgpstream AND no real BGP_DATA_ROOT → use the bundled synthetic sample so the demo works.
    sample = tmp_path / "sample_bgp_data"
    sample.mkdir()
    capture = _wire_scoped_run(
        monkeypatch, _scoped_settings(bgp_data_root="/nope/xyz", bgp_sample_data_root=str(sample))
    )

    async def unavailable(plan, settings):
        raise GatherUnavailable("no pybgpstream")

    monkeypatch.setattr(agent_mod, "gather_and_stage", unavailable)
    monkeypatch.setattr(agent_mod, "reap_stage", lambda d: None)

    _collect("analyze 1.1.1.0/24")

    assert capture["json"]["workspace"] == {"source": f"file://{sample.resolve()}", "mode": "ro"}


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
        agent_tools=["Bash"],
        agent_max_budget_usd=None,
        agent_request_timeout=600,
        bgp_data_root="/nope/xyz",
        bgp_sample_data_root="",
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
