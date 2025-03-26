import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi_agent.services.gpt_agent import GPTAgent
from app_1.utils.extract_code_from_reply import extract_code_from_reply

logger = logging.getLogger(__name__)
router = APIRouter()

gpt_agent = GPTAgent()

def sse_format(data: dict, flush_comment: bool = False):
    msg = f"data: {json.dumps(data)}\n\n"
    if flush_comment:
        msg += ": flush\n\n"
    return msg

@router.get("/bgp_gpt", response_class=StreamingResponse)
async def query_gpt(
    query: str = Query(..., description="User query")
):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")

    async def event_generator():
        yield sse_format({"status": "generating_started"})
        accumulated_text = []
        buffer = []
        BUFFER_SIZE = 3
        BUFFER_TIME = 0.1
        last_yield = asyncio.get_event_loop().time()

        async for chunk in gpt_agent.stream_gpt_chunks(query):
            buffer.append(chunk)
            accumulated_text.append(chunk)
            now = asyncio.get_event_loop().time()
            if len(buffer) >= BUFFER_SIZE or (now - last_yield) > BUFFER_TIME:
                chunk_str = "".join(buffer)
                yield sse_format({"status": "generating", "generated_text": chunk_str}, flush_comment=True)
                buffer.clear()
                last_yield = now

        # If leftover tokens remain
        if buffer:
            chunk_str = "".join(buffer)
            yield sse_format({"status": "generating", "generated_text": chunk_str}, flush_comment=True)

        # Code extraction if needed
        full_response = "".join(accumulated_text)
        code = extract_code_from_reply(full_response)
        if code:
            yield sse_format({"status": "code_ready", "code": code})
        else:
            yield sse_format({"status": "no_code_found"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
