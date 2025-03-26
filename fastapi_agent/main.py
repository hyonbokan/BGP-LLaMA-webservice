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

# Instantiate your agent once.
llama_agent = LlamaAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://llama.cnu.ac.kr", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sse_event(data_dict, flush=False):
    event_str = f"data: {json.dumps(data_dict)}\n\n"
    if flush:
        # Some browsers and proxies flush on comment lines as well
        event_str += ": flush\n\n"
    return event_str

@app.get("/bgp_llama", response_class=StreamingResponse)
async def query_agent(
    query: str = Query(..., description="User query"),
    context: str = Query("", description="Optional context")
):
    """
    SSE endpoint: Streams tokens in real time.
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")

    # Start generation in a background thread.
    streamer, thread = llama_agent.stream_tokens(query, context)
    assistant_reply_chunks = []  # accumulates tokens for final code extraction
    loop = asyncio.get_event_loop()

    def get_next_token():
        try:
            return next(streamer)
        except StopIteration:
            return None

    async def event_generator():
        # Send an initial SSE event to let the client know we started.
        yield sse_event({"status": "generating_started"})
        
        # Optional buffering logic:
        buffer = []
        last_yield = loop.time()
        BUFFER_SIZE = 3       # tokens to accumulate
        BUFFER_TIME = 0.1     # seconds to wait before flushing

        while True:
            new_text = await loop.run_in_executor(None, get_next_token)
            if new_text is None:
                # No more tokens. If there's something left in the buffer, yield it now.
                if buffer:
                    chunk = "".join(buffer)
                    yield sse_event({"status": "generating", "generated_text": chunk}, flush=True)
                break
            
            # Accumulate tokens in a buffer
            buffer.append(new_text)
            assistant_reply_chunks.append(new_text)
            
            # If buffer is "full" or enough time has passed, flush it now
            now = loop.time()
            if len(buffer) >= BUFFER_SIZE or (now - last_yield) > BUFFER_TIME:
                chunk = "".join(buffer)
                yield sse_event({"status": "generating", "generated_text": chunk}, flush=True)
                buffer = []
                last_yield = now

        # Join the background thread to ensure generation is finished.
        thread.join()
        
        # final processing phase
        full_response = "".join(assistant_reply_chunks)
        code = extract_code_from_reply(full_response)
        if code:
            yield sse_event({"status": "code_ready", "code": code})
        else:
            yield sse_event({"status": "no_code_found"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/bgp_llama/health")
async def health():
    return JSONResponse(content={"status": "ok"})