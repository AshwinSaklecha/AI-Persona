from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict

from app.models.schemas import RetrievedChunk


PERSONA_KEYWORDS = (
    "ashwin",
    "resume",
    "experience",
    "background",
    "project",
    "projects",
    "github",
    "contribution",
    "contributions",
    "open source",
    "deepchem",
    "gemini",
    "gemini cli",
    "cli",
    "intern",
    "spenza",
    "education",
    "cgpa",
    "portfolio",
    "kv-cache",
    "introduce yourself",
    "tell me about yourself",
    "who are you",
)

INTRO_PATTERNS = (
    "tell me about yourself",
    "introduce yourself",
    "who are you",
    "your background",
    "about ashwin",
)

CONTRIBUTION_PATTERNS = (
    "contribution",
    "contributions",
    "open source",
    "deepchem",
    "gemini cli",
    "gemini-cli",
    "pull request",
    "pull requests",
    "pr ",
)


@dataclass(slots=True)
class RetrievalService:
    embeddings: object
    vector_store: object
    min_score: float

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not getattr(self.vector_store, "ready", False):
            return []
        query_embedding = self.embeddings.embed_query(query)
        matches = self.vector_store.search(query_embedding, max(top_k * 8, 24))
        retrieved = [
            RetrievedChunk(
                id=chunk.id,
                source_id=chunk.source_id,
                source_title=chunk.source_title,
                source_type=chunk.source_type,
                text=chunk.text,
                url=chunk.url,
                score=score,
                metadata=chunk.metadata,
            )
            for chunk, score in matches
            if score >= self.min_score
        ]
        return self._rerank_results(query, retrieved, top_k)

    def should_fallback(self, query: str, results: list[RetrievedChunk]) -> str | None:
        if not self.is_persona_question(query):
            return None
        if not results:
            return "no_retrieval_match"
        if results[0].score < self.min_score:
            return "low_similarity_context"
        return None

    @staticmethod
    def is_persona_question(query: str) -> bool:
        lowered = query.lower()
        return any(keyword in lowered for keyword in PERSONA_KEYWORDS)

    @staticmethod
    def _is_intro_question(lowered_query: str) -> bool:
        return any(pattern in lowered_query for pattern in INTRO_PATTERNS)

    @staticmethod
    def _is_contribution_question(lowered_query: str) -> bool:
        return any(pattern in lowered_query for pattern in CONTRIBUTION_PATTERNS)

    def _rerank_results(
        self,
        query: str,
        results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        lowered = query.lower().strip()
        intro_question = self._is_intro_question(lowered)
        contribution_question = self._is_contribution_question(lowered)
        project_question = self._is_project_question(lowered)

        def adjusted_score(chunk: RetrievedChunk) -> float:
            title = chunk.source_title.lower()
            path = str(chunk.metadata.get("path", "")).lower()
            score = chunk.score

            if intro_question:
                if chunk.source_type == "resume":
                    score += 0.18
                if "resume" in title:
                    score += 0.14
                if "contribution" in title:
                    score += 0.04

            if contribution_question:
                if "contribution" in title:
                    score += 0.24
                if "deepchem" in title:
                    score += 0.12
                if "gemini cli" in title or "gemini-cli" in title:
                    score += 0.12
                if "contributions" in path:
                    score += 0.08

            if project_question:
                if chunk.source_type == "github":
                    score += 0.18
                if "resume" in title:
                    score -= 0.08
                if "contribution" in title or "contributions" in path:
                    score -= 0.28
                if any(
                    repo_name in title
                    for repo_name in (
                        "kv-cache",
                        "expensetracker",
                        "ecommerce-app",
                        "smart-doc-generator",
                    )
                ):
                    score += 0.2

            return score

        sorted_results = sorted(results, key=adjusted_score, reverse=True)

        max_per_source = 2
        if contribution_question or project_question or intro_question:
            max_per_source = 1

        selected: list[RetrievedChunk] = []
        source_counts: dict[str, int] = defaultdict(int)

        if project_question:
            for chunk in sorted_results:
                title = chunk.source_title.lower()
                path = str(chunk.metadata.get("path", "")).lower()
                if chunk.source_type != "github":
                    continue
                if "contribution" in title or "contributions" in path:
                    continue
                if source_counts[chunk.source_id] >= max_per_source:
                    continue
                selected.append(chunk)
                source_counts[chunk.source_id] += 1
                if len(selected) >= top_k:
                    return selected

        for chunk in sorted_results:
            if source_counts[chunk.source_id] >= max_per_source:
                continue
            selected.append(chunk)
            source_counts[chunk.source_id] += 1
            if len(selected) >= top_k:
                return selected

        for chunk in sorted_results:
            if chunk in selected:
                continue
            selected.append(chunk)
            if len(selected) >= top_k:
                break

        return selected

    @staticmethod
    def _is_project_question(lowered_query: str) -> bool:
        patterns = (
            "what projects",
            "which projects",
            "projects have you made",
            "projects have you built",
            "what have you built",
            "personal projects",
        )
        return any(pattern in lowered_query for pattern in patterns)
