from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_services
from app.models.schemas import HealthResponse
from app.services.container import ServiceContainer


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(services: ServiceContainer = Depends(get_services)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        index_ready=services.vector_store.ready,
        embedding_ready=services.embeddings.ready,
        chat_ready=services.llm.ready,
        vector_backend=services.vector_store.backend,
    )

