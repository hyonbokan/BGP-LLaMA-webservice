import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import environ
from .routers import llama_routes, gpt_routes

env = environ.Env()
environ.Env.read_env() 

logger = logging.getLogger(__name__)


cors_origins = env.list("CORS_ALLOWED_ORIGINS")
csrf_origins = env.list("CSRF_TRUSTED_ORIGINS")
allowed_hosts = env.list("ALLOWED_HOSTS")

app = FastAPI(
    title="My SSE API",
    description="A microservice for LLaMA and GPT SSE streaming",
    version="1.0.0",
)

# Add CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llama_routes.router, tags=["llama"])

app.include_router(gpt_routes.router, tags=["gpt"])

@app.get("/health")
def health():
    return {"status": "ok"}
