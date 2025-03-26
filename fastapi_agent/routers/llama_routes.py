import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi_agent.services.llama_agent import LlamaAgent
from app_1.utils.extract_code_from_reply import extract_code_from_reply

logger = logging.getLogger(__name__)
router = APIRouter()

llama_agent = LlamaAgent()

def sse_event(data_dict, flush=False):
    event_str = f"data: {json.dumps(data_dict)}\n\n"
    if flush:
        event_str += ": flush\n\n"
    return event_str

@router.get("/bgp_llama", response_class=StreamingResponse)
async def query_llama(
    query: str = Query(..., description="User query"),
    context: str = Query("", description="Optional context")
):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")

    # Start generation in a background thread.
    streamer, thread = llama_agent.stream_tokens(query, context)
    assistant_reply_chunks = []
    loop = asyncio.get_event_loop()

    def get_next_token():
        try:
            return next(streamer)
        except StopIteration:
            return None

    async def event_generator():
        # 1. Send an initial SSE event to tell the client we started
        yield sse_event({"status": "generating_started"})

        # 2. Yield tokens one-by-one, flushing after each token
        while True:
            token = await loop.run_in_executor(None, get_next_token)
            if token is None:
                break
            assistant_reply_chunks.append(token)
            yield sse_event({"status": "generating", "generated_text": token}, flush=True)

        # 3. Join the generation thread, ensuring it's finished
        thread.join()

        # 4. After generation, do final processing (like code extraction)
        full_response = "".join(assistant_reply_chunks)
        code = extract_code_from_reply(full_response)
        if code:
            yield sse_event({"status": "code_ready", "code": code})
        else:
            yield sse_event({"status": "no_code_found"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")