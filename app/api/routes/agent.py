"""The agentic BGP analysis endpoint: proxy one autonomous run and re-stream it.

`POST /api/agent/run` renders the query into a task, runs it on the agent pod,
and re-streams the outcome over this backend's SSE. Distinct from `/api/chat/*`
(which only generates a script): this path runs the analysis. The frame vocab is
`agent_started` -> `running` (a heartbeat per pod keep-alive) -> `result` ->
`error`; the live per-step trace lands once the pod ships token/tool events.
"""

import json
from enum import StrEnum

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.logging import get_logger
from app.llm.agent import Running, RunResult, run_agent

logger = get_logger(__name__)
router = APIRouter()


class AgentStatus(StrEnum):
    """The `status` value on each SSE frame this endpoint emits."""

    STARTED = "agent_started"
    RUNNING = "running"
    RESULT = "result"
    ERROR = "error"


class AgentRequest(BaseModel):
    """An agent turn: a new query plus optional distilled findings from a prior run.

    `prior_findings` is how multi-turn continuity is carried — a compact summary of
    an earlier run's result, not a raw transcript. Each run is otherwise independent.
    """

    query: str
    prior_findings: str | None = None


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _event_stream(query: str, prior_findings: str | None):
    yield _sse({"status": AgentStatus.STARTED})
    try:
        async for event in run_agent(query, prior_findings):
            if isinstance(event, Running):
                yield _sse({"status": AgentStatus.RUNNING})
            elif isinstance(event, RunResult):
                yield _sse(
                    {
                        "status": AgentStatus.RESULT,
                        "text": event.text,
                        "is_error": event.is_error,
                        "subtype": event.subtype,
                        "cost_usd": event.total_cost_usd,
                        "duration_ms": event.duration_ms,
                        "num_turns": event.num_turns,
                        "structured_output": event.structured_output,
                    }
                )
    except Exception as e:  # surface to the client instead of a dropped stream
        logger.exception("Agent run failed")
        yield _sse({"status": AgentStatus.ERROR, "message": str(e)})
        return


@router.post("/agent/run")
async def agent_run(req: AgentRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is required.")
    return StreamingResponse(
        _event_stream(req.query, req.prior_findings),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
