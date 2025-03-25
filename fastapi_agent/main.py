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

@app.get("/bgp_llama", response_class=StreamingResponse)
async def query_agent(
    query: str = Query(..., description="User query"),
    context: str = Query("", description="Optional context")
):
    if not query:
        raise HTTPException(status_code=400, detail="Query field is required.")

    # Build the full prompt.
    full_query = (context + "\n" if context else "") + BASE_SETUP + query

    # Create a fresh streamer instance.
    streamer = llama_agent.streamer_factory()

    # Tokenize the input.
    inputs = llama_agent.tokenizer(
        full_query,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=1500
    )
    input_ids = inputs.input_ids.to(llama_agent.model.device)
    attention_mask = inputs.attention_mask.to(llama_agent.model.device)

    generation_kwargs = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "streamer": streamer,
        "max_new_tokens": 100,
        "do_sample": True,
        "temperature": 0.1,
        "repetition_penalty": 1.1,
        "eos_token_id": llama_agent.tokenizer.eos_token_id,
        "pad_token_id": llama_agent.tokenizer.pad_token_id,
        "early_stopping": True,
    }

    loop = asyncio.get_event_loop()
    # Start model generation in a background thread.
    generation_future = loop.run_in_executor(None, lambda: llama_agent.model.generate(**generation_kwargs))
    
    assistant_reply_chunks = []

    def get_next_token(streamer):
        try:
            return next(streamer)
        except StopIteration:
            return None

    async def event_generator():
        # Send an initial event.
        yield f"data: {json.dumps({'status': 'generating_started'})}\n\n"
        
        # Stream tokens as they are produced.
        while True:
            new_text = await loop.run_in_executor(None, get_next_token, streamer)
            if new_text is None:
                break
            assistant_reply_chunks.append(new_text)
            # Yield this token immediately.
            yield f"data: {json.dumps({'status': 'generating', 'generated_text': new_text})}\n\n"
            # Yield control briefly to force flushing.
            await asyncio.sleep(0.01)
        
        await generation_future
        
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