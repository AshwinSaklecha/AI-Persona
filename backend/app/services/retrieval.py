from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
import re

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
    "interest",
    "interests",
    "fit",
    "strengths",
    "why are you",
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
    github_repo_list: tuple[str, ...] = ()
    github_contribution_repo_list: tuple[str, ...] = ()

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

    @staticmethod
    def _is_interest_question(lowered_query: str) -> bool:
        patterns = (
            "what interests you",
            "what are your interests",
            "what are you interested in",
            "what do you enjoy",
            "what excites you",
            "what are your main interests",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _is_fit_question(lowered_query: str) -> bool:
        patterns = (
            "why are you a good fit",
            "why are you right for this role",
            "why should we hire you",
            "why are you suited",
            "fit for this role",
            "why you",
        )
        return any(pattern in lowered_query for pattern in patterns)

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
        interest_question = self._is_interest_question(lowered)
        fit_question = self._is_fit_question(lowered)

        def adjusted_score(chunk: RetrievedChunk) -> float:
            title = chunk.source_title.lower()
            path = str(chunk.metadata.get("path", "")).lower()
            score = chunk.score

            if intro_question:
                if self._is_resume_source(chunk):
                    score += 0.18
                if self._is_resume_summary_chunk(chunk):
                    score += 0.14
                if self._is_experience_chunk(chunk):
                    score += 0.12
                if self._is_project_source(chunk):
                    score += 0.08
                if self._is_contribution_source(chunk):
                    score += 0.04

            if contribution_question:
                if self._is_contribution_source(chunk):
                    score += 0.24
                if "deepchem" in title:
                    score += 0.12
                if "gemini cli" in title or "gemini-cli" in title:
                    score += 0.12
                if "contributions" in path:
                    score += 0.08

            if project_question:
                if self._is_project_source(chunk):
                    score += 0.18
                if self._is_resume_source(chunk):
                    score -= 0.08
                if self._is_contribution_source(chunk):
                    score -= 0.28
                if self._is_known_project_repo(chunk):
                    score += 0.2

            if interest_question:
                if self._is_resume_summary_chunk(chunk):
                    score += 0.18
                if self._is_project_source(chunk):
                    score += 0.08
                if self._is_contribution_source(chunk):
                    score += 0.08
                if self._is_experience_chunk(chunk):
                    score += 0.06

            if fit_question:
                if self._is_experience_chunk(chunk):
                    score += 0.18
                if self._is_project_source(chunk):
                    score += 0.12
                if self._is_contribution_source(chunk):
                    score += 0.1
                if self._is_resume_summary_chunk(chunk):
                    score += 0.08

            return score

        sorted_results = sorted(results, key=adjusted_score, reverse=True)

        if contribution_question:
            return self._select_contribution_results(sorted_results, top_k)
        if project_question:
            return self._select_project_results(sorted_results, top_k)
        if intro_question:
            return self._select_balanced_results(
                sorted_results,
                top_k,
                include_resume=True,
                include_experience=True,
                include_projects=1,
                include_contributions=1,
            )
        if interest_question:
            return self._select_balanced_results(
                sorted_results,
                top_k,
                include_resume=True,
                include_experience=False,
                include_projects=1,
                include_contributions=1,
            )
        if fit_question:
            return self._select_balanced_results(
                sorted_results,
                top_k,
                include_resume=True,
                include_experience=True,
                include_projects=1,
                include_contributions=1,
            )

        max_per_source = 2
        selected: list[RetrievedChunk] = []
        source_counts: dict[str, int] = defaultdict(int)

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
            "some of your projects",
            "projects have you made",
            "projects have you built",
            "what have you built",
            "personal projects",
        )
        return any(pattern in lowered_query for pattern in patterns)

    @staticmethod
    def _normalize_repo_name(value: str) -> str:
        lowered = value.lower()
        return re.sub(r"[^a-z0-9]+", "", lowered)

    def _is_resume_source(self, chunk: RetrievedChunk) -> bool:
        return chunk.source_type == "resume" or "resume" in chunk.source_title.lower()

    def _is_resume_summary_chunk(self, chunk: RetrievedChunk) -> bool:
        lowered = chunk.text.lower()
        return self._is_resume_source(chunk) and (
            "third-year computer science" in lowered
            or "passionate about backend systems" in lowered
            or "## summary" in lowered
        )

    def _is_experience_chunk(self, chunk: RetrievedChunk) -> bool:
        lowered = chunk.text.lower()
        return self._is_resume_source(chunk) and (
            "spenza" in lowered or "software engineer intern" in lowered or "## experience" in lowered
        )

    def _is_contribution_source(self, chunk: RetrievedChunk) -> bool:
        title = chunk.source_title.lower()
        path = str(chunk.metadata.get("path", "")).lower()
        return "contribution" in title or "contributions" in path

    def _is_known_project_repo(self, chunk: RetrievedChunk) -> bool:
        if not self.github_repo_list:
            return False
        title = self._normalize_repo_name(chunk.source_title)
        path = self._normalize_repo_name(str(chunk.metadata.get("path", "")))
        return any(
            self._normalize_repo_name(repo_name) in title or self._normalize_repo_name(repo_name) in path
            for repo_name in self.github_repo_list
        )

    def _is_project_source(self, chunk: RetrievedChunk) -> bool:
        if chunk.source_type != "github":
            return False
        if self._is_contribution_source(chunk):
            return False
        if not self.github_repo_list:
            return True
        return self._is_known_project_repo(chunk)

    def _select_contribution_results(
        self,
        sorted_results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        selected: list[RetrievedChunk] = []
        seen_sources: set[str] = set()

        for preferred in ("deepchem", "gemini"):
            for chunk in sorted_results:
                title = chunk.source_title.lower()
                if chunk.source_id in seen_sources or not self._is_contribution_source(chunk):
                    continue
                if preferred in title:
                    selected.append(chunk)
                    seen_sources.add(chunk.source_id)
                    break

        for chunk in sorted_results:
            if chunk.source_id in seen_sources or not self._is_contribution_source(chunk):
                continue
            selected.append(chunk)
            seen_sources.add(chunk.source_id)
            if len(selected) >= top_k:
                return selected

        return selected[:top_k]

    def _select_project_results(
        self,
        sorted_results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        selected: list[RetrievedChunk] = []
        seen_sources: set[str] = set()

        for chunk in sorted_results:
            if chunk.source_id in seen_sources or not self._is_project_source(chunk):
                continue
            selected.append(chunk)
            seen_sources.add(chunk.source_id)
            if len(selected) >= top_k:
                return selected

        if len(selected) < top_k:
            selected.extend(
                chunk
                for chunk in self._supplement_sources(self._is_project_source)
                if chunk.source_id not in seen_sources
            )

        deduped: list[RetrievedChunk] = []
        seen_sources.clear()
        for chunk in selected:
            if chunk.source_id in seen_sources:
                continue
            deduped.append(chunk)
            seen_sources.add(chunk.source_id)
            if len(deduped) >= top_k:
                break
        return deduped

    def _select_balanced_results(
        self,
        sorted_results: list[RetrievedChunk],
        top_k: int,
        *,
        include_resume: bool,
        include_experience: bool,
        include_projects: int,
        include_contributions: int,
    ) -> list[RetrievedChunk]:
        selected: list[RetrievedChunk] = []
        seen_sources: set[str] = set()

        if include_resume:
            self._append_first_matching(
                sorted_results,
                selected,
                seen_sources,
                lambda chunk: self._is_resume_summary_chunk(chunk) or self._is_resume_source(chunk),
            )

        if include_experience:
            self._append_first_matching(
                sorted_results,
                selected,
                seen_sources,
                self._is_experience_chunk,
            )

        for _ in range(include_projects):
            self._append_first_matching(
                sorted_results,
                selected,
                seen_sources,
                self._is_project_source,
            )

        for _ in range(include_contributions):
            self._append_first_matching(
                sorted_results,
                selected,
                seen_sources,
                self._is_contribution_source,
            )

        for chunk in sorted_results:
            if chunk.source_id in seen_sources:
                continue
            selected.append(chunk)
            seen_sources.add(chunk.source_id)
            if len(selected) >= top_k:
                break

        return selected[:top_k]

    @staticmethod
    def _append_first_matching(
        sorted_results: list[RetrievedChunk],
        selected: list[RetrievedChunk],
        seen_sources: set[str],
        predicate,
    ) -> None:
        for chunk in sorted_results:
            if chunk.source_id in seen_sources:
                continue
            if predicate(chunk):
                selected.append(chunk)
                seen_sources.add(chunk.source_id)
                return

    def _supplement_sources(self, predicate) -> list[RetrievedChunk]:
        chunks = getattr(self.vector_store, "chunks", []) or []
        supplemented: list[RetrievedChunk] = []
        for chunk in chunks:
            candidate = RetrievedChunk(
                id=chunk.id,
                source_id=chunk.source_id,
                source_title=chunk.source_title,
                source_type=chunk.source_type,
                text=chunk.text,
                url=chunk.url,
                score=0.0,
                metadata=chunk.metadata,
            )
            if predicate(candidate):
                supplemented.append(candidate)
        return supplemented
