import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.logging import get_logger
from app.llm.generation import Compacted, Result, TextDelta, script_syntax_error
from app.llm.schemas import Turn
from app.llm.service import stream_chat

logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """A chat turn: the new query plus the prior conversation for context."""

    query: str
    history: list[Turn] = []


# Coalesce deltas into fewer SSE frames: flush once BUFFER_SIZE deltas pile up
# or BUFFER_TIME seconds pass, whichever comes first.
BUFFER_SIZE = 3
BUFFER_TIME = 0.1


def _sse(data: dict, flush: bool = False) -> str:
    msg = f"data: {json.dumps(data)}\n\n"
    if flush:
        msg += ": flush\n\n"
    return msg


async def _event_stream(provider: str, query: str, history: list[Turn]):
    logger.debug("SSE stream start: provider=%s", provider)
    yield _sse({"status": "generating_started"})

    buffer = []
    loop = asyncio.get_running_loop()
    last_yield = loop.time()
    result: Result | None = None
    produced_text = False

    try:
        async for event in stream_chat(provider, query, history):
            if isinstance(event, TextDelta):
                produced_text = True
                buffer.append(event.text)
                now = loop.time()
                if len(buffer) >= BUFFER_SIZE or (now - last_yield) > BUFFER_TIME:
                    yield _sse(
                        {"status": "generating", "generated_text": "".join(buffer)}, flush=True
                    )
                    buffer.clear()
                    last_yield = now
            elif isinstance(event, Compacted):
                yield _sse(
                    {
                        "status": "compacted",
                        "dropped": event.dropped,
                        "summarized": event.summarized,
                    }
                )
            elif isinstance(event, Result):
                result = event
        if buffer:
            yield _sse({"status": "generating", "generated_text": "".join(buffer)}, flush=True)
    except Exception as e:  # surface to the client instead of a dropped stream
        logger.exception("Error while streaming %s response", provider)
        yield _sse({"status": "error", "message": str(e)})
        return

    if not produced_text:
        logger.warning("%s stream produced no output", provider)

    script = result.script if result else None
    if not script:
        yield _sse({"status": "no_code_found"})
        return
    frame = {"status": "code_ready", "code": script}
    warning = script_syntax_error(script)
    if warning:
        logger.warning("Generated script has a syntax error: %s", warning)
        frame["warning"] = f"The generated script may not run: {warning}"
    yield _sse(frame)


def _sse_response(generator) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        # X-Accel-Buffering travels with the response so SSE isn't buffered even
        # if a proxy forgets to disable buffering for this location.
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/chat/bgp_gpt")
async def bgp_gpt(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is required.")
    return _sse_response(_event_stream("gpt", req.query, req.history))


@router.post("/chat/bgp_llama")
async def bgp_llama(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is required.")
    return _sse_response(_event_stream("llama", req.query, req.history))
