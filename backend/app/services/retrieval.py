from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import RetrievedChunk


PERSONA_KEYWORDS = (
    "ashwin",
    "resume",
    "experience",
    "project",
    "projects",
    "github",
    "deepchem",
    "intern",
    "spenza",
    "education",
    "cgpa",
    "portfolio",
    "kv-cache",
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
        matches = self.vector_store.search(query_embedding, top_k)
        return [
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

