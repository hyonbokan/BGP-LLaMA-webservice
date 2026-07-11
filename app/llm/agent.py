"""Run a BGP question as one autonomous agent run on the opencode-agent-pod.

`run_agent` is the agent-path analog of the chat pipeline: it classifies the
query, renders the same routed prompt, then POSTs a single run to the pod and
relays the pod's Server-Sent Events. The pod holds the provider keys and the
agent loop (write a script, run it against staged data, observe, self-correct);
this only forwards a rendered task and streams the outcome back.

It yields two event kinds: `Running` for each keep-alive tick while the pod
works, and a terminal `RunResult` carrying the pod's answer (free text, plus
run metadata: cost, turns, duration, subtype). Live per-step token/tool events
are a pod feature not built yet, so between submit and the result there is only
a running heartbeat.
"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.llm.classifier import classify_intent
from app.llm.schemas import BgpIntent
from prompts.loader import PromptTemplate, load_prompt

logger = get_logger(__name__)


class PodError(Exception):
    """The pod could not be reached or refused the run (bad config, auth, or HTTP status)."""


class PodEvent(StrEnum):
    """Named SSE events the pod emits that this client acts on (others are ignored)."""

    COST = "cost"
    DONE = "done"


@dataclass
class Running:
    """A liveness tick while the pod works the run — no live step trace yet."""


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


AgentEvent = Running | RunResult


async def run_agent(query: str, prior_findings: str | None = None) -> AsyncIterator[AgentEvent]:
    """Stream one autonomous agent run for a query, relaying the pod's events.

    Classifies the query, renders the routed system prompt (threading distilled
    `prior_findings` from an earlier run when given, the memory unit that carries
    context forward without replaying a whole transcript), then POSTs a single
    run to the pod and yields a `Running` tick per keep-alive and a terminal
    `RunResult`. Raises `PodError` if the pod is unreachable or returns non-200.
    """
    settings = get_settings()
    if not settings.agent_pod_token:
        raise PodError("AGENT_POD_TOKEN is not set; the pod refuses unauthenticated runs")

    intent = await classify_intent(query)
    system_prompt = _agent_system_prompt(intent)
    if prior_findings:
        system_prompt = f"{system_prompt}\n\n## Prior findings\n{prior_findings}"

    body = _run_body(settings, system_prompt, query)
    url = f"{settings.agent_pod_url.rstrip('/')}/agent/run"
    headers = {"Authorization": f"Bearer {settings.agent_pod_token}"}
    logger.debug("agent run: model=%s tools=%s -> %s", settings.agent_model, body["tools"], url)

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


def _agent_system_prompt(intent: BgpIntent) -> str:
    """Render the autonomous-analyst system prompt, seeding any parsed parameters.

    Unlike the generate-only chat prompt, this instructs the agent to write and run
    pybgpstream code and report findings without asking clarifying questions.
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


def _run_body(settings: Settings, system_prompt: str, prompt: str) -> dict:
    """Assemble the pod's `/agent/run` body. Omits the workspace when no staged data exists."""
    body: dict[str, Any] = {
        "model": settings.agent_model,
        "system_prompt": system_prompt,
        "prompt": prompt,
        "tools": settings.agent_tool_list,
        "max_budget_usd": settings.agent_max_budget_usd,
    }
    source = _workspace_source(settings.bgp_data_root)
    if source is not None:
        body["workspace"] = {"source": source, "mode": "ro"}
    return body


def _workspace_source(bgp_data_root: str) -> str | None:
    """A `file://` pointer to the staged BGP data, or None when the directory is absent.

    The pod stages a workspace by reference (it copies the source into a throwaway
    dir per run). With no data staged yet, running without a workspace still gives
    the agent an empty scratch dir to write and run code in, rather than failing
    every run on a missing path.
    """
    root = Path(bgp_data_root)
    if not root.exists():
        logger.warning("BGP_DATA_ROOT %s is absent; running without a staged workspace", root)
        return None
    return f"file://{root.resolve()}"


async def _relay(response: httpx.Response) -> AsyncIterator[AgentEvent]:
    """Translate the pod's SSE stream into `Running` ticks and a terminal `RunResult`.

    The pod frames liveness as `:` comments and payloads as named `event:`/`data:`
    frames; only its terminal `done` frame carries the result. Unknown events (a
    `cost` tick, future token/tool events) are ignored.
    """
    event_name: str | None = None
    data_lines: list[str] = []
    async for line in response.aiter_lines():
        if line.startswith(":"):  # a keep-alive comment — the pod is still working
            yield Running()
            continue
        if line == "":  # blank line terminates a frame
            if event_name == PodEvent.DONE and data_lines:
                yield _to_result(json.loads("\n".join(data_lines)))
            event_name, data_lines = None, []
            continue
        if line.startswith("event:"):
            event_name = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data_lines.append(line[len("data:") :].lstrip())


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
