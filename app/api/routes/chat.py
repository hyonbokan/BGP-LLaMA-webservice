import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.llm.service import stream_chat
from app.utils.code_extract import extract_code_from_reply

logger = get_logger(__name__)
router = APIRouter()

# Coalesce tokens into fewer SSE frames: flush once BUFFER_SIZE tokens pile up
# or BUFFER_TIME seconds pass, whichever comes first.
BUFFER_SIZE = 3
BUFFER_TIME = 0.1


def _sse(data: dict, flush: bool = False) -> str:
    msg = f"data: {json.dumps(data)}\n\n"
    if flush:
        msg += ": flush\n\n"
    return msg


async def _event_stream(provider: str, query: str, context: str = ""):
    logger.debug("SSE stream start: provider=%s", provider)
    yield _sse({"status": "generating_started"})

    accumulated, buffer = [], []
    loop = asyncio.get_running_loop()
    last_yield = loop.time()

    try:
        async for token in stream_chat(provider, query, context):
            buffer.append(token)
            accumulated.append(token)
            now = loop.time()
            if len(buffer) >= BUFFER_SIZE or (now - last_yield) > BUFFER_TIME:
                yield _sse({"status": "generating", "generated_text": "".join(buffer)}, flush=True)
                buffer.clear()
                last_yield = now
        if buffer:
            yield _sse({"status": "generating", "generated_text": "".join(buffer)}, flush=True)
    except Exception as e:  # surface to the client instead of a dropped stream
        logger.exception("Error while streaming %s response", provider)
        yield _sse({"status": "error", "message": str(e)})
        return

    full_response = "".join(accumulated)
    if not full_response:
        logger.warning("%s stream produced no output", provider)
    code = extract_code_from_reply(full_response)
    yield _sse({"status": "code_ready", "code": code} if code else {"status": "no_code_found"})


def _sse_response(generator) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        # X-Accel-Buffering travels with the response so SSE isn't buffered even
        # if a proxy forgets to disable buffering for this location.
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/bgp_gpt")
async def bgp_gpt(query: str = Query(..., description="User query")):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")
    return _sse_response(_event_stream("gpt", query))


@router.get("/chat/bgp_llama")
async def bgp_llama(
    query: str = Query(..., description="User query"),
    context: str = Query("", description="Optional context"),
):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")
    return _sse_response(_event_stream("llama", query, context))
