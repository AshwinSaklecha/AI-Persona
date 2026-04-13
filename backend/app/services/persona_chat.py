from __future__ import annotations

import re
from time import perf_counter

from app.models.schemas import ChatResponse
from app.services.booking_flow import BookingFlowService
from app.services.evaluation import EvaluationLogger
from app.services.llm import LLMService
from app.services.prompting import FALLBACK_ANSWER, PromptBuilder
from app.services.retrieval import RetrievalService


class PersonaChatService:
    def __init__(
        self,
        *,
        retrieval: RetrievalService,
        prompt_builder: PromptBuilder,
        llm: LLMService,
        evaluation: EvaluationLogger,
        booking_flow: BookingFlowService,
        retrieval_top_k: int,
    ) -> None:
        self.retrieval = retrieval
        self.prompt_builder = prompt_builder
        self.llm = llm
        self.evaluation = evaluation
        self.booking_flow = booking_flow
        self.retrieval_top_k = retrieval_top_k

    def respond(self, message: str, conversation_id: str | None = None) -> ChatResponse:
        started = perf_counter()
        resolved_conversation_id = self.booking_flow.ensure_conversation_id(conversation_id)

        booking_result = self.booking_flow.maybe_handle(resolved_conversation_id, message)
        if booking_result is not None:
            latency_ms = int((perf_counter() - started) * 1000)
            self.evaluation.log_chat(
                query=message,
                latency_ms=latency_ms,
                retrieval_hits=0,
                top_score=None,
                fallback_reason=None,
                answer_mode="booking",
            )
            return ChatResponse(
                answer=booking_result.answer,
                answer_mode="booking",
                conversation_id=resolved_conversation_id,
                sources=[],
                booking=booking_result.booking,
                latency_ms=latency_ms,
                retrieval_hits=0,
                fallback_triggered=False,
                fallback_reason=None,
            )

        persona_question = self.retrieval.is_persona_question(message)
        retrieved_chunks = self.retrieval.retrieve(message, self.retrieval_top_k)
        fallback_reason = self.retrieval.should_fallback(message, retrieved_chunks)

        if fallback_reason:
            latency_ms = int((perf_counter() - started) * 1000)
            self.evaluation.log_failure(fallback_reason, {"query": message})
            self.evaluation.log_chat(
                query=message,
                latency_ms=latency_ms,
                retrieval_hits=len(retrieved_chunks),
                top_score=retrieved_chunks[0].score if retrieved_chunks else None,
                fallback_reason=fallback_reason,
                answer_mode="fallback",
            )
            return ChatResponse(
                answer=FALLBACK_ANSWER,
                answer_mode="fallback",
                conversation_id=resolved_conversation_id,
                sources=retrieved_chunks,
                booking=None,
                latency_ms=latency_ms,
                retrieval_hits=len(retrieved_chunks),
                fallback_triggered=True,
                fallback_reason=fallback_reason,
            )

        prompt = self.prompt_builder.build(
            query=message,
            retrieved_chunks=retrieved_chunks,
            persona_question=persona_question,
        )

        try:
            answer = self.llm.generate(
                system_instruction=prompt.system_instruction,
                user_content=prompt.user_content,
            )
        except Exception as exc:  # pragma: no cover - exercised through API layer
            self.evaluation.log_failure("llm_generation_error", {"error": str(exc)})
            raise RuntimeError("LLM generation failed.") from exc

        latency_ms = int((perf_counter() - started) * 1000)
        self.evaluation.log_chat(
            query=message,
            latency_ms=latency_ms,
            retrieval_hits=len(retrieved_chunks),
            top_score=retrieved_chunks[0].score if retrieved_chunks else None,
            fallback_reason=None,
            answer_mode=prompt.answer_mode,
        )
        cleaned_answer = self._clean_answer(answer)

        return ChatResponse(
            answer=cleaned_answer or FALLBACK_ANSWER,
            answer_mode=prompt.answer_mode if cleaned_answer else "fallback",
            conversation_id=resolved_conversation_id,
            sources=retrieved_chunks,
            booking=None,
            latency_ms=latency_ms,
            retrieval_hits=len(retrieved_chunks),
            fallback_triggered=not bool(cleaned_answer),
            fallback_reason=None if cleaned_answer else "llm_empty_response",
        )

    @staticmethod
    def _clean_answer(answer: str | None) -> str:
        if not answer:
            return ""

        cleaned = answer.replace("\r\n", "\n").replace("**", "").replace("__", "")
        cleaned = cleaned.replace("`", "")
        cleaned = re.sub(r"(?m)^[ \t]*\*\s+", "- ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
