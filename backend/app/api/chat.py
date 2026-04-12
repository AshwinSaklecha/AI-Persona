from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_services
from app.models.schemas import ChatRequest, ChatResponse
from app.services.container import ServiceContainer
from app.services.prompting import FALLBACK_ANSWER


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, services: ServiceContainer = Depends(get_services)) -> ChatResponse:
    started = perf_counter()
    conversation_id = services.booking_flow.ensure_conversation_id(request.conversation_id)

    booking_result = services.booking_flow.maybe_handle(conversation_id, request.message)
    if booking_result is not None:
        latency_ms = int((perf_counter() - started) * 1000)
        services.evaluation.log_chat(
            query=request.message,
            latency_ms=latency_ms,
            retrieval_hits=0,
            top_score=None,
            fallback_reason=None,
            answer_mode="booking",
        )
        return ChatResponse(
            answer=booking_result.answer,
            answer_mode="booking",
            conversation_id=conversation_id,
            sources=[],
            booking=booking_result.booking,
            latency_ms=latency_ms,
            retrieval_hits=0,
            fallback_triggered=False,
            fallback_reason=None,
        )

    persona_question = services.retrieval.is_persona_question(request.message)
    retrieved_chunks = services.retrieval.retrieve(
        request.message,
        services.settings.retrieval_top_k,
    )
    fallback_reason = services.retrieval.should_fallback(request.message, retrieved_chunks)

    if fallback_reason:
        latency_ms = int((perf_counter() - started) * 1000)
        services.evaluation.log_failure(fallback_reason, {"query": request.message})
        services.evaluation.log_chat(
            query=request.message,
            latency_ms=latency_ms,
            retrieval_hits=len(retrieved_chunks),
            top_score=retrieved_chunks[0].score if retrieved_chunks else None,
            fallback_reason=fallback_reason,
            answer_mode="fallback",
        )
        return ChatResponse(
            answer=FALLBACK_ANSWER,
            answer_mode="fallback",
            conversation_id=conversation_id,
            sources=retrieved_chunks,
            latency_ms=latency_ms,
            retrieval_hits=len(retrieved_chunks),
            fallback_triggered=True,
            fallback_reason=fallback_reason,
        )

    prompt = services.prompt_builder.build(
        query=request.message,
        retrieved_chunks=retrieved_chunks,
        persona_question=persona_question,
    )

    try:
        answer = services.llm.generate(
            system_instruction=prompt.system_instruction,
            user_content=prompt.user_content,
        )
    except Exception as exc:
        services.evaluation.log_failure("llm_generation_error", {"error": str(exc)})
        raise HTTPException(status_code=503, detail="LLM generation failed.") from exc

    latency_ms = int((perf_counter() - started) * 1000)
    services.evaluation.log_chat(
        query=request.message,
        latency_ms=latency_ms,
        retrieval_hits=len(retrieved_chunks),
        top_score=retrieved_chunks[0].score if retrieved_chunks else None,
        fallback_reason=None,
        answer_mode=prompt.answer_mode,
    )

    return ChatResponse(
        answer=answer or FALLBACK_ANSWER,
        answer_mode=prompt.answer_mode if answer else "fallback",
        conversation_id=conversation_id,
        sources=retrieved_chunks,
        latency_ms=latency_ms,
        retrieval_hits=len(retrieved_chunks),
        fallback_triggered=not bool(answer),
        fallback_reason=None if answer else "llm_empty_response",
    )
