from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import Settings
from app.models.schemas import IngestResponse
from app.services.calcom import CalComService
from app.services.booking_flow import BookingFlowService
from app.services.chunking import TextChunker
from app.services.embeddings import GeminiEmbeddingService
from app.services.evaluation import EvaluationLogger
from app.services.github_source import GitHubSourceService
from app.services.llm import GeminiLLMService
from app.services.persona_chat import PersonaChatService
from app.services.prompting import PromptBuilder
from app.services.retrieval import RetrievalService
from app.services.source_loader import LocalSourceLoader
from app.services.vapi_admin import VapiAdminService
from app.services.vector_store import VectorStore


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    chunker: TextChunker
    embeddings: GeminiEmbeddingService
    vector_store: VectorStore
    retrieval: RetrievalService
    prompt_builder: PromptBuilder
    llm: GeminiLLMService
    evaluation: EvaluationLogger
    source_loader: LocalSourceLoader
    github_source: GitHubSourceService
    calcom: CalComService
    booking_flow: BookingFlowService
    persona_chat: PersonaChatService
    vapi_admin: VapiAdminService

    def rebuild_index(self) -> IngestResponse:
        documents = self.source_loader.load()
        chunks = self.chunker.chunk_documents(documents)
        embeddings = self.embeddings.embed_texts([chunk.text for chunk in chunks])
        self.vector_store.rebuild(chunks, embeddings)
        return IngestResponse(
            document_count=len(documents),
            chunk_count=len(chunks),
            index_backend=self.vector_store.backend,
            rebuilt_at=datetime.now(timezone.utc),
        )


def build_services(settings: Settings) -> ServiceContainer:
    chunker = TextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    embeddings = GeminiEmbeddingService(settings)
    vector_store = VectorStore(settings)
    vector_store.load()
    retrieval = RetrievalService(
        embeddings=embeddings,
        vector_store=vector_store,
        min_score=settings.retrieval_min_score,
    )
    prompt_builder = PromptBuilder(settings.allow_general_tech_answers)
    llm = GeminiLLMService(settings)
    evaluation = EvaluationLogger(settings)
    source_loader = LocalSourceLoader(settings.source_dir)
    github_source = GitHubSourceService(settings)
    calcom = CalComService(settings)
    booking_flow = BookingFlowService(
        settings=settings,
        calcom=calcom,
        evaluation=evaluation,
    )
    persona_chat = PersonaChatService(
        retrieval=retrieval,
        prompt_builder=prompt_builder,
        llm=llm,
        evaluation=evaluation,
        booking_flow=booking_flow,
        retrieval_top_k=settings.retrieval_top_k,
    )
    vapi_admin = VapiAdminService(settings, evaluation)

    return ServiceContainer(
        settings=settings,
        chunker=chunker,
        embeddings=embeddings,
        vector_store=vector_store,
        retrieval=retrieval,
        prompt_builder=prompt_builder,
        llm=llm,
        evaluation=evaluation,
        source_loader=source_loader,
        github_source=github_source,
        calcom=calcom,
        booking_flow=booking_flow,
        persona_chat=persona_chat,
        vapi_admin=vapi_admin,
    )
