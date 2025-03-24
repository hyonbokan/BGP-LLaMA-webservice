from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import logging

from app_1.services.llama_agent import LlamaAgent

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Llama Agent Microservice",
    description="A microservice implementing an AI agent following the ReAct pattern with MCP.",
    version="1.0.0",
)

# Dependency injection: instantiate your agent once.
# TODO: use FastAPI's dependency system.
llama_agent = LlamaAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://llama.cnu.ac.kr", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/bgp_llama", response_class=StreamingResponse)
async def query_agent(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    query = body.get("query")
    context = body.get("context", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query field is required.")

    # Generate response using the agent. (You might later make this incremental.)
    result = await llama_agent.generate_response(query, context)
    full_response = result.get("response", "")
    code = result.get("code", None)

    async def event_generator():
        # Send an initial event.
        yield f"data: {json.dumps({'status': 'generating_started'})}\n\n"
        # For simplicity, we send the full generated response in one go.
        yield f"data: {json.dumps({'status': 'generating', 'generated_text': full_response})}\n\n"
        if code:
            yield f"data: {json.dumps({'status': 'code_ready', 'code': code})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'no_code_found'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/agent/health")
async def health():
    return JSONResponse(content={"status": "ok"})
