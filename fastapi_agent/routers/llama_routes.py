import json
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi_agent.services.llm_service import stream_chat
from app_1.utils.extract_code_from_reply import extract_code_from_reply

logger = logging.getLogger(__name__)
router = APIRouter()


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

    async def event_generator():
        # 1. Tell the client we started.
        yield sse_event({"status": "generating_started"})

        assistant_reply_chunks = []
        batch_tokens = []
        batch_size = 3

        try:
            # The local fine-tuned BGP-LLaMA is served by vLLM over the same
            # OpenAI-compatible API as GPT, so streaming is one async loop.
            async for token in stream_chat("llama", query, context):
                batch_tokens.append(token)
                if len(batch_tokens) >= batch_size:
                    batch_text = "".join(batch_tokens)
                    assistant_reply_chunks.append(batch_text)
                    yield sse_event({"status": "generating", "generated_text": batch_text}, flush=True)
                    batch_tokens = []

            # Flush any remaining tokens.
            if batch_tokens:
                batch_text = "".join(batch_tokens)
                assistant_reply_chunks.append(batch_text)
                yield sse_event({"status": "generating", "generated_text": batch_text}, flush=True)
        except Exception as e:
            logger.exception("Error while streaming LLaMA response")
            yield sse_event({"status": "error", "message": str(e)})
            return

        # 2. After generation, do final processing (like code extraction).
        full_response = "".join(assistant_reply_chunks)
        code = extract_code_from_reply(full_response)
        if code:
            yield sse_event({"status": "code_ready", "code": code})
        else:
            yield sse_event({"status": "no_code_found"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
