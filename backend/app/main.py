from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.booking import router as booking_router
from app.api.chat import router as chat_router
from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.vapi import router as vapi_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.services.container import build_services


settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    services = build_services(settings)
    app.state.services = services

    if settings.auto_rebuild_on_startup and services.github_source.ready:
        try:
            services.github_source.sync(refresh=False)
            logger.info("Synced GitHub source documents on startup.")
        except Exception as exc:
            logger.exception("Startup GitHub sync failed.")
            services.evaluation.log_failure("github_sync_failed", {"error": str(exc)})

    if settings.auto_rebuild_on_startup and services.embeddings.ready and not services.vector_store.ready:
        try:
            rebuilt = services.rebuild_index()
            logger.info(
                "Built index on startup with %s docs and %s chunks.",
                rebuilt.document_count,
                rebuilt.chunk_count,
            )
        except Exception as exc:
            logger.exception("Startup ingestion failed.")
            services.evaluation.log_failure("startup_ingest_failed", {"error": str(exc)})

    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(ingest_router, prefix=settings.api_prefix)
app.include_router(booking_router, prefix=settings.api_prefix)
app.include_router(events_router, prefix=settings.api_prefix)
app.include_router(vapi_router, prefix=settings.api_prefix)
