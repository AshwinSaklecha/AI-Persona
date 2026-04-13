from app.services.retrieval import RetrievalService
from app.models.schemas import DocumentChunk


class FakeEmbeddings:
    def __init__(self):
        self.calls = 0

    def embed_query(self, query: str):
        self.calls += 1
        return query


class FakeVectorStore:
    ready = True

    def search(self, query_embedding, top_k: int):
        return []


def test_persona_question_without_context_triggers_fallback():
    service = RetrievalService(
        embeddings=FakeEmbeddings(),
        vector_store=FakeVectorStore(),
        min_score=0.35,
    )

    reason = service.should_fallback("Tell me about Ashwin's internship", [])

    assert reason == "no_retrieval_match"


def test_general_question_does_not_force_fallback():
    service = RetrievalService(
        embeddings=FakeEmbeddings(),
        vector_store=FakeVectorStore(),
        min_score=0.35,
    )

    reason = service.should_fallback("How does consistent hashing work?", [])

    assert reason is None


def test_persona_detection_matches_resume_keywords():
    result = RetrievalService.is_persona_question("What did you build in kv-cache?")
    assert result is True


class RerankingAwareVectorStore:
    ready = True

    def search(self, query_embedding, top_k: int):
        return [
            (
                DocumentChunk(
                    id="project::0",
                    source_id="project",
                    source_title="AshwinSaklecha/kv-cache",
                    source_type="github",
                    text="KV cache chunk",
                    chunk_index=0,
                ),
                0.9,
            ),
            (
                DocumentChunk(
                    id="resume::0",
                    source_id="resume",
                    source_title="Ashwin Resume",
                    source_type="resume",
                    text="Resume summary chunk",
                    chunk_index=0,
                ),
                0.84,
            ),
            (
                DocumentChunk(
                    id="expense::0",
                    source_id="expense",
                    source_title="AshwinSaklecha/expenseTracker",
                    source_type="github",
                    text="Expense tracker chunk",
                    chunk_index=0,
                ),
                0.83,
            ),
            (
                DocumentChunk(
                    id="deepchem::0",
                    source_id="deepchem",
                    source_title="DeepChem Contributions",
                    source_type="github",
                    text="DeepChem contribution chunk",
                    chunk_index=0,
                    metadata={"path": "github/live/deepchem-deepchem-contributions.md"},
                ),
                0.81,
            ),
            (
                DocumentChunk(
                    id="deepchem::1",
                    source_id="deepchem",
                    source_title="DeepChem Contributions",
                    source_type="github",
                    text="Another DeepChem contribution chunk",
                    chunk_index=1,
                    metadata={"path": "github/live/deepchem-deepchem-contributions.md"},
                ),
                0.8,
            ),
            (
                DocumentChunk(
                    id="gemini-cli::0",
                    source_id="gemini-cli",
                    source_title="Gemini CLI Contributions",
                    source_type="github",
                    text="Gemini CLI contribution chunk",
                    chunk_index=0,
                    metadata={"path": "github/live/google-gemini-gemini-cli-contributions.md"},
                ),
                0.79,
            ),
        ]


def test_intro_query_expands_to_resume_style_retrieval():
    embeddings = FakeEmbeddings()
    service = RetrievalService(
        embeddings=embeddings,
        vector_store=RerankingAwareVectorStore(),
        min_score=0.35,
    )

    results = service.retrieve("Tell me about yourself", top_k=5)

    assert results[0].source_title == "Ashwin Resume"
    assert embeddings.calls == 1


def test_contribution_query_expands_to_multiple_contribution_sources():
    embeddings = FakeEmbeddings()
    service = RetrievalService(
        embeddings=embeddings,
        vector_store=RerankingAwareVectorStore(),
        min_score=0.35,
    )

    results = service.retrieve("Tell me about your open source contributions", top_k=3)

    titles = {result.source_title for result in results}

    assert "DeepChem Contributions" in titles
    assert "Gemini CLI Contributions" in titles
    assert embeddings.calls == 1


def test_project_query_prefers_personal_projects_over_contribution_chunks():
    embeddings = FakeEmbeddings()
    service = RetrievalService(
        embeddings=embeddings,
        vector_store=RerankingAwareVectorStore(),
        min_score=0.35,
    )

    results = service.retrieve("What projects have you made?", top_k=3)

    titles = [result.source_title for result in results]

    assert "AshwinSaklecha/kv-cache" in titles
    assert "DeepChem Contributions" not in titles
