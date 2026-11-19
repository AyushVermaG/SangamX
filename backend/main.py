from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1.engine import router as engine_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    logger.info("SangamX backend starting up")
    yield
    logger.info("SangamX backend shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="SangamX API",
        description="Multi-agent AI collaboration platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(engine_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {"status": "ok", "service": "sangamx-backend"}

    return app


app = create_app()
