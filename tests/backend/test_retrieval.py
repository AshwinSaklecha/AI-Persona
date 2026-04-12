from app.services.retrieval import RetrievalService


class FakeEmbeddings:
    def embed_query(self, query: str):
        return [1.0, 0.0]


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
