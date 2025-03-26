import asyncio
import json
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app_1.prompts.llama_prompt_local_run import BASE_SETUP
from app_1.services.llama_agent import LlamaAgent
from app_1.utils.extract_code_from_reply import extract_code_from_reply

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Llama Agent Microservice",
    description="A microservice implementing an AI agent following the ReAct pattern with MCP.",
    version="1.0.0",
)

llama_agent = LlamaAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://llama.cnu.ac.kr", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/bgp_llama", response_class=StreamingResponse)
async def query_agent(
    query: str = Query(..., description="User query"),
    context: str = Query("", description="Optional context")
):
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")

    streamer, thread = llama_agent.stream_tokens(query, context)
    assistant_reply_chunks = []
    loop = asyncio.get_event_loop()

    def get_next_token():
        try:
            return next(streamer)
        except StopIteration:
            return None

    async def event_generator():
        # Initial SSE event
        yield f"data: {json.dumps({'status': 'generating_started'})}\n\n"
        buffer = []
        last_yield = loop.time()
        while True:
            new_text = await loop.run_in_executor(None, get_next_token)
            if new_text is None:
                # If there's something left in buffer, yield it.
                if buffer:
                    chunk = "".join(buffer)
                    yield f"data: {json.dumps({'status': 'generating', 'generated_text': chunk})}\n\n"
                    yield f": flush\n\n"
                break
            buffer.append(new_text)
            assistant_reply_chunks.append(new_text)
            now = loop.time()
            # If we have 3 tokens or >0.1s elapsed, yield them
            if len(buffer) >= 3 or (now - last_yield) > 0.1:
                chunk = "".join(buffer)
                yield f"data: {json.dumps({'status': 'generating', 'generated_text': chunk})}\n\n"
                yield f": flush\n\n"
                buffer = []
                last_yield = now

        thread.join()
        full_response = "".join(assistant_reply_chunks)
        code = extract_code_from_reply(full_response)
        if code:
            yield f"data: {json.dumps({'status': 'code_ready', 'code': code})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'no_code_found'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/bgp_llama/health")
async def health():
    return JSONResponse(content={"status": "ok"})