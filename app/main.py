from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agent, chat, files, health
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    get_logger(__name__).info("BGP-LLaMA API starting (log level=%s)", settings.log_level)

    app = FastAPI(
        title="BGP-LLaMA API",
        description="LLaMA/GPT SSE streaming + artifact download for BGP analysis.",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Everything lives under /api; nginx serves the SPA and proxies /api here.
    app.include_router(health.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(agent.router, prefix="/api")
    app.include_router(files.router, prefix="/api")

    return app


app = create_app()
