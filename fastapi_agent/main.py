import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import llama_routes, gpt_routes

logger = logging.getLogger(__name__)

app = FastAPI(
    title="My SSE API",
    description="A microservice for LLaMA and GPT SSE streaming",
    version="1.0.0",
)

# Add CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://llama.cnu.ac.kr", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llama_routes.router, tags=["llama"])

app.include_router(gpt_routes.router, tags=["gpt"])

@app.get("/health")
def health():
    return {"status": "ok"}
