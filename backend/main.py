from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1.engine import router as engine_router
from app.task_store import task_store

logger = logging.getLogger(__name__)


async def _periodic_task_cleanup(interval_seconds: float = 60.0, ttl_seconds: float = 3600.0) -> None:
    """Background loop that periodically evicts expired terminal tasks."""
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            await task_store.cleanup_expired_tasks(ttl_seconds=ttl_seconds)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning("Error during periodic task cleanup: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    logger.info("SangamX backend starting up")

    # Start periodic task cleanup
    cleanup_task = asyncio.create_task(_periodic_task_cleanup())

    yield

    logger.info("SangamX backend shutting down")
    # Cancel periodic cleanup
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    # Cancel any remaining running tasks cleanly
    await task_store.cancel_all_running()
    logger.info("SangamX backend shutdown complete")


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
        # NOTE: test_api_health.py asserts {"status": "healthy"} — keep in sync.
        return {"status": "healthy"}

    return app


app = create_app()
