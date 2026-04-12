from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_services
from app.models.schemas import ChatRequest, ChatResponse
from app.services.container import ServiceContainer


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, services: ServiceContainer = Depends(get_services)) -> ChatResponse:
    try:
        return services.persona_chat.respond(
            request.message,
            conversation_id=request.conversation_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="LLM generation failed.") from exc
