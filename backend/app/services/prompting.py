from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import RetrievedChunk


FALLBACK_ANSWER = "I don't know based on the information I have right now."


@dataclass(slots=True)
class PromptBundle:
    system_instruction: str
    user_content: str
    answer_mode: str


class PromptBuilder:
    def __init__(self, allow_general_tech_answers: bool) -> None:
        self.allow_general_tech_answers = allow_general_tech_answers

    def build(self, query: str, retrieved_chunks: list[RetrievedChunk], persona_question: bool) -> PromptBundle:
        context_block = self._render_context(retrieved_chunks)
        answer_mode = "grounded" if persona_question or retrieved_chunks else "general"
        system_instruction = self._system_instruction()
        user_content = (
            f"User question:\n{query}\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            "Answer the question now."
        )
        return PromptBundle(
            system_instruction=system_instruction,
            user_content=user_content,
            answer_mode=answer_mode,
        )

    def _system_instruction(self) -> str:
        general_mode = (
            "If the user asks a general tech question that is clearly not about Ashwin, "
            "you may answer from general knowledge, but start the answer with "
            "'General tech answer:' and do not imply personal experience."
            if self.allow_general_tech_answers
            else f"If the context is not enough, say exactly: {FALLBACK_ANSWER}"
        )
        return (
            "You are an AI persona for Ashwin Saklecha. Speak in first person as Ashwin. "
            "Be honest, slightly informal, and clear. Do not exaggerate.\n"
            "When the user asks about Ashwin's resume, education, work, projects, or GitHub, "
            "answer only from the retrieved context. If the retrieved context is missing or weak, "
            f"say exactly: {FALLBACK_ANSWER}\n"
            f"{general_mode}\n"
            "Do not invent metrics, dates, responsibilities, or project details."
        )

    @staticmethod
    def _render_context(retrieved_chunks: list[RetrievedChunk]) -> str:
        if not retrieved_chunks:
            return "No relevant context retrieved."

        rendered = []
        for chunk in retrieved_chunks:
            rendered.append(
                f"[Source: {chunk.source_title} | score={chunk.score:.3f}]\n{chunk.text}"
            )
        return "\n\n".join(rendered)

