from __future__ import annotations

from dataclasses import dataclass
import re

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
            f"Response requirements:\n{self._response_requirements(query, retrieved_chunks)}\n\n"
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
            "Be honest, slightly informal, clear, and natural. Do not exaggerate.\n"
            "When the user asks about Ashwin's resume, education, work, projects, or GitHub, "
            "answer only from the retrieved context. If the retrieved context is missing or weak, "
            f"say exactly: {FALLBACK_ANSWER}\n"
            f"{general_mode}\n"
            "Do not invent metrics, dates, responsibilities, or project details.\n"
            "When the question is broad, synthesize across the relevant sources instead of focusing on one random detail.\n"
            "Write in plain text only.\n"
            "Prefer short natural paragraphs. You may use simple hyphen bullets or numbered lists if they make the answer clearer.\n"
            "Do not use markdown bold markers, tables, headings, or code blocks.\n"
            "Do not dump the entire resume unless the user explicitly asks for everything."
        )

    def _response_requirements(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> str:
        lowered = query.lower().strip()
        requirements = [
            "Sound like a natural human answer, not a profile summary.",
            "Use plain text only.",
        ]

        if self._is_name_question(lowered):
            requirements.append("Answer in one short sentence with the name only.")

        if self._is_intro_question(lowered):
            requirements.append(
                "Treat this as a self-introduction. Start with who I am, what I focus on, and what kind of work I do."
            )
            requirements.append(
                "After that, briefly mention the most relevant experience or projects. Do not jump straight into one project."
            )
            requirements.append(
                "Mention that I am a third-year Computer Science student in Bengaluru focused on backend systems, AI/ML, and open source if that context is available."
            )
            requirements.append(
                "Ground the answer in a balanced mix of internship experience, personal projects, and open-source work instead of sounding generic."
            )
            requirements.append(
                "Do not turn the answer into a project inventory. Mention at most one or two concrete examples unless the user asks for more detail."
            )
            requirements.append("Avoid generic filler or motivational clichés.")

        if self._is_interest_question(lowered):
            requirements.append(
                "Answer this as a question about what genuinely interests me in tech and the kind of problems I like working on."
            )
            requirements.append(
                "Focus on themes like backend systems, AI/ML, open source, building reliable products, and learning through real projects."
            )
            requirements.append(
                "Do not list a bunch of project names unless they help explain the interest naturally."
            )
            requirements.append("Avoid generic filler like 'technology is always evolving' unless it is directly useful.")

        if self._is_fit_question(lowered):
            requirements.append(
                "Answer this like a thoughtful interview response, not a resume summary."
            )
            requirements.append(
                "Connect my fit to my backend focus, internship execution, project work, and open-source contributions with two or three concrete proofs."
            )
            requirements.append(
                "Keep each example factually separate. Do not merge details from one project into another."
            )
            requirements.append("Only mention details that are explicitly supported by the retrieved context.")

        if self._is_contribution_question(lowered):
            requirements.append(
                "Summarize the main open-source contributions clearly instead of describing only one contribution."
            )
            if self._has_multiple_contribution_sources(retrieved_chunks):
                requirements.append(
                    "The retrieved context includes multiple contribution tracks. Mention both DeepChem and Gemini CLI."
                )

        if self._wants_short_answer(lowered):
            requirements.append("Keep the answer to at most two short sentences.")

        if self._wants_tradeoffs(lowered):
            requirements.append("Explicitly mention tradeoffs, design choices, and why they mattered.")

        if self._is_project_question(lowered):
            requirements.append(
                "If the user is asking broadly about my projects, mention more than one relevant project from the retrieved context instead of focusing on only one."
            )
            requirements.append(
                "Focus on personal projects first. Do not replace a project answer with open-source contributions unless the user explicitly asks about contributions too."
            )
            requirements.append(
                "Prefer the selected GitHub projects over resume-only projects when both are available."
            )

        if self._wants_bullets(lowered):
            requirements.append("Use short hyphen bullets.")
            requirements.append("Keep each bullet concise and avoid long paragraphs.")
            if self._is_project_question(lowered):
                requirements.append("For each project bullet, include the project name plus a short purpose or stack hint.")

        return "\n".join(f"- {requirement}" for requirement in requirements)

    @staticmethod
    def _is_intro_question(lowered_query: str) -> bool:
        patterns = (
            "tell me about yourself",
            "introduce yourself",
            "who are you",
            "about yourself",
            "your background",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _is_name_question(lowered_query: str) -> bool:
        patterns = (
            "what is your name",
            "what's your name",
            "whats your name",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _is_contribution_question(lowered_query: str) -> bool:
        patterns = (
            "contribution",
            "contributions",
            "open source",
            "deepchem",
            "gemini cli",
            "gemini-cli",
            "pull request",
            "pull requests",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _wants_short_answer(lowered_query: str) -> bool:
        patterns = ("2 lines", "two lines", "2 line", "two line", "2 sentences", "two sentences")
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _wants_tradeoffs(lowered_query: str) -> bool:
        patterns = ("tradeoff", "trade-off", "tradeoffs", "trade offs", "design choice")
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _is_project_question(lowered_query: str) -> bool:
        patterns = (
            "what projects",
            "which projects",
            "some of your projects",
            "projects have you made",
            "projects have you built",
            "what have you built",
            "personal projects",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _is_interest_question(lowered_query: str) -> bool:
        patterns = (
            "what interests you",
            "what are your interests",
            "what are you interested in",
            "what do you enjoy",
            "what excites you",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _is_fit_question(lowered_query: str) -> bool:
        patterns = (
            "why are you a good fit",
            "why are you right for this role",
            "why should we hire you",
            "fit for this role",
            "why you",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _wants_bullets(lowered_query: str) -> bool:
        patterns = (
            "bullet",
            "bullet points",
            "bullets",
            "in points",
            "as a list",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _has_multiple_contribution_sources(retrieved_chunks: list[RetrievedChunk]) -> bool:
        lowered_titles = {chunk.source_title.lower() for chunk in retrieved_chunks}
        return any("deepchem" in title for title in lowered_titles) and any(
            "gemini cli" in title or "gemini-cli" in title for title in lowered_titles
        )

    @staticmethod
    def _render_context(retrieved_chunks: list[RetrievedChunk]) -> str:
        if not retrieved_chunks:
            return "No relevant context retrieved."

        rendered = []
        for chunk in retrieved_chunks:
            clean_text = re.sub(r"\n{3,}", "\n\n", chunk.text).strip()
            rendered.append(
                f"[Source: {chunk.source_title} | score={chunk.score:.3f}]\n{clean_text}"
            )
        return "\n\n".join(rendered)
