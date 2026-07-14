"""Run a BGP question as one autonomous agent run on the opencode-agent-pod.

`run_agent` is the agent-path analog of the chat pipeline: it classifies the
query, renders the autonomous prompt, then POSTs a single run to the pod and
relays the pod's Server-Sent Events. The backend gathers the BGP data and stages
it as a read-only workspace; the pod holds the provider keys and the agent loop
(inspect the staged data, analyze it in Python, observe, self-correct). The agent
never fetches — this forwards a rendered task plus a workspace pointer and streams
the outcome back.

It yields four event kinds as the run streams: `Token` for a chunk of the agent's
answer text, `ToolCall` for a tool's state transition (its name, status, input,
and — once finished — output), `Running` for a keep-alive tick while the pod is
otherwise idle, and a terminal `RunResult` carrying the pod's answer (free text,
plus run metadata: cost, turns, duration, subtype). The `Token`/`ToolCall` events
are the live step trace a run-and-observe console renders.
"""

import json
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx

from app.bgp import GatherUnavailable, build_fetch_plan, gather_and_stage, reap_stage
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.llm.classifier import classify_intent
from app.llm.schemas import BgpIntent
from app.llm.workspace import no_cleanup, publish_workspace
from prompts.loader import PromptTemplate, load_prompt

logger = get_logger(__name__)


class PodError(Exception):
    """The pod could not be reached or refused the run (bad config, auth, or HTTP status)."""


class PodEvent(StrEnum):
    """Named SSE events the pod emits that this client acts on (others are ignored)."""

    TOKEN = "token"
    TOOL = "tool"
    COST = "cost"
    DONE = "done"


@dataclass
class Running:
    """A liveness tick while the pod works the run and emits nothing else."""


@dataclass
class Token:
    """A chunk of the agent's answer text as it streams."""

    text: str


@dataclass
class ToolCall:
    """A tool-call state transition: its name, status, input, and — once done — output."""

    id: str
    name: str
    status: str
    input: Any | None = None
    output: Any | None = None


@dataclass
class RunResult:
    """The terminal pod result: the answer text plus run metadata."""

    text: str
    is_error: bool
    subtype: str | None
    total_cost_usd: float | None
    duration_ms: int | None
    num_turns: int | None
    structured_output: Any | None


AgentEvent = Running | Token | ToolCall | RunResult


async def run_agent(query: str, prior_findings: str | None = None) -> AsyncIterator[AgentEvent]:
    """Stream one autonomous agent run for a query, relaying the pod's events.

    Classifies the query, gathers and stages the scoped BGP data as the agent's
    workspace, renders the routed system prompt (threading distilled
    `prior_findings` from an earlier run when given, the memory unit that carries
    context forward without replaying a whole transcript), then POSTs a single
    run to the pod and yields the run's live `token`/`tool` events, `Running`
    ticks per keep-alive, and a terminal `RunResult`. The staged data is reaped
    when the run ends. Raises `PodError` if the pod is unreachable or non-200.
    """
    settings = get_settings()
    if not settings.agent_pod_token:
        raise PodError("AGENT_POD_TOKEN is not set; the pod refuses unauthenticated runs")

    intent = await classify_intent(query)
    system_prompt = _agent_system_prompt(intent)
    if prior_findings:
        system_prompt = f"{system_prompt}\n\n## Prior findings\n{prior_findings}"

    local_dir, reap_local = await _prepare_workspace(intent, settings)
    try:
        workspace_source, release_source = await publish_workspace(local_dir, settings)
        try:
            body = _run_body(settings, system_prompt, query, workspace_source)
            url = f"{settings.agent_pod_url.rstrip('/')}/agent/run"
            headers = {"Authorization": f"Bearer {settings.agent_pod_token}"}
            logger.debug(
                "agent run: model=%s tools=%s -> %s", settings.agent_model, body["tools"], url
            )

            timeout = httpx.Timeout(settings.agent_request_timeout, connect=10.0)
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("POST", url, json=body, headers=headers) as response:
                        if response.status_code != 200:
                            detail = (await response.aread()).decode(errors="replace")
                            raise PodError(f"pod returned {response.status_code}: {detail}")
                        async for event in _relay(response):
                            yield event
            except httpx.HTTPError as exc:  # connection refused, read timeout, etc.
                raise PodError(f"could not reach the agent pod: {exc}") from exc
        finally:
            release_source()  # drop the uploaded workspace (no-op for the file transport)
    finally:
        reap_local()  # reap a freshly gathered dir; a no-op for a static fallback root


def _agent_system_prompt(intent: BgpIntent) -> str:
    """Render the autonomous-analyst system prompt, seeding any parsed parameters.

    Unlike the generate-only chat prompt, this instructs the agent to analyze the
    backend-staged BGP data and report findings without asking clarifying questions.
    """
    window = intent.time_window
    return load_prompt(
        PromptTemplate.AGENT_SYSTEM,
        target_asn=intent.target_asn,
        prefixes=intent.prefixes,
        from_time=window.from_time if window else None,
        until_time=window.until_time if window else None,
        collectors=intent.collectors,
    )


def _run_body(
    settings: Settings, system_prompt: str, prompt: str, workspace_source: str | None
) -> dict:
    """Assemble the pod's `/agent/run` body. Omits the workspace when none was staged."""
    body: dict[str, Any] = {
        "model": settings.agent_model,
        "system_prompt": system_prompt,
        "prompt": prompt,
        "tools": settings.agent_tools,
        "max_budget_usd": settings.agent_max_budget_usd,
    }
    if workspace_source is not None:
        body["workspace"] = {"source": workspace_source, "mode": "ro"}
    return body


async def _prepare_workspace(
    intent: BgpIntent, settings: Settings
) -> tuple[str | None, Callable[[], None]]:
    """Prepare the agent's local workspace directory, returning it plus a cleanup to run after the
    run.

    Gathers the scoped BGP updates live into a fresh directory (which the returned cleanup reaps)
    when the intent carries a gatherable scope. Falls back to a static directory — with a no-op
    cleanup, since a static root is not this run's to delete — when there is no scope to gather,
    when pybgpstream is absent (e.g. a dev host), or when a gather fails, so a run still gets data
    rather than an empty directory. Transport of the directory to the pod is a separate step.
    """
    plan = build_fetch_plan(intent, settings)
    if plan is not None:
        try:
            staged = await gather_and_stage(plan, settings)
            return staged, lambda: reap_stage(staged)
        except GatherUnavailable:
            logger.warning("pybgpstream unavailable; falling back to static BGP data")
        except Exception as exc:  # a gather/staging failure must not fail the run
            logger.warning("BGP gather failed (%s); falling back to static BGP data", exc)
    return _fallback_dir(settings), no_cleanup


def _fallback_dir(settings: Settings) -> str | None:
    """A static workspace directory for a run that didn't gather live: the configured
    `BGP_DATA_ROOT` if it exists, else the bundled synthetic sample (so the demo works on a host
    without pybgpstream), else None (an empty scratch dir).
    """
    root = Path(settings.bgp_data_root)
    if root.exists():
        return str(root.resolve())

    sample = settings.bgp_sample_data_root
    if sample and Path(sample).is_dir():
        logger.warning(
            "no live gather and BGP_DATA_ROOT %s is absent; using the bundled SYNTHETIC sample at "
            "%s (demo data, not real BGP) — install pybgpstream or set BGP_DATA_ROOT for real data",
            settings.bgp_data_root,
            sample,
        )
        return str(Path(sample).resolve())

    logger.warning(
        "no BGP data available (no gather, no BGP_DATA_ROOT, no sample); empty workspace"
    )
    return None


async def _relay(response: httpx.Response) -> AsyncIterator[AgentEvent]:
    """Translate the pod's SSE stream into typed events.

    The pod frames liveness as `:` comments and payloads as named `event:`/`data:`
    frames: `token` and `tool` carry the live step trace, `done` carries the
    terminal result, and a `cost` tick is ignored. A keep-alive comment yields a
    `Running` tick so the caller knows the pod is still working.
    """
    event_name: str | None = None
    data_lines: list[str] = []
    async for line in response.aiter_lines():
        if line.startswith(":"):  # a keep-alive comment — the pod is still working
            yield Running()
            continue
        if line == "":  # blank line terminates a frame
            event = _frame_event(event_name, data_lines)
            if event is not None:
                yield event
            event_name, data_lines = None, []
            continue
        if line.startswith("event:"):
            event_name = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data_lines.append(line[len("data:") :].lstrip())


def _frame_event(event_name: str | None, data_lines: list[str]) -> AgentEvent | None:
    """Map one completed `event:`/`data:` frame to a typed event, or None to ignore it."""
    if not data_lines:
        return None
    payload = json.loads("\n".join(data_lines))
    if event_name == PodEvent.TOKEN:
        return Token(text=payload.get("text", ""))
    if event_name == PodEvent.TOOL:
        return ToolCall(
            id=str(payload.get("id", "")),
            name=payload.get("name", "?"),
            status=payload.get("status", ""),
            input=payload.get("input"),
            output=payload.get("output"),
        )
    if event_name == PodEvent.DONE:
        return _to_result(payload)
    return None  # a `cost` tick or any other event carries nothing this client renders


def _to_result(payload: dict) -> RunResult:
    """Read a pod `done` payload (an OpencodeResult) into a `RunResult`."""
    return RunResult(
        text=payload.get("text", ""),
        is_error=bool(payload.get("is_error", False)),
        subtype=payload.get("subtype"),
        total_cost_usd=payload.get("total_cost_usd"),
        duration_ms=payload.get("duration_ms"),
        num_turns=payload.get("num_turns"),
        structured_output=payload.get("structured_output"),
    )
