from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_services
from app.models.schemas import ClientEvent
from app.services.container import ServiceContainer


router = APIRouter(tags=["events"])


@router.post("/events/client", status_code=202)
def log_client_event(
    event: ClientEvent,
    services: ServiceContainer = Depends(get_services),
) -> dict[str, str]:
    if event.event_type in {"voice_interrupted", "voice_unsupported"}:
        services.evaluation.log_failure(event.event_type, event.details)
    else:
        services.evaluation.log_client_event(event.event_type, event.details)
    return {"status": "accepted"}

