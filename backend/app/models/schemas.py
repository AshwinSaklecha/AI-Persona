from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class SourceDocument(BaseModel):
    id: str
    title: str
    text: str
    source_type: str
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    id: str
    source_id: str
    source_title: str
    source_type: str
    text: str
    url: str | None = None
    chunk_index: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    id: str
    source_id: str
    source_title: str
    source_type: str
    text: str
    url: str | None = None
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class AvailabilitySlot(BaseModel):
    start: str
    end: str | None = None
    label: str


class BookingChatState(BaseModel):
    active: bool = False
    stage: Literal[
        "idle",
        "awaiting_window",
        "awaiting_slot_selection",
        "awaiting_contact",
        "confirmed",
    ] = "idle"
    slots: list[AvailabilitySlot] = Field(default_factory=list)
    selected_slot: AvailabilitySlot | None = None
    booking_uid: str | None = None
    meeting_url: str | None = None


class ChatResponse(BaseModel):
    answer: str
    answer_mode: Literal["grounded", "general", "fallback", "booking"]
    conversation_id: str
    sources: list[RetrievedChunk] = Field(default_factory=list)
    booking: BookingChatState | None = None
    latency_ms: int
    retrieval_hits: int
    fallback_triggered: bool = False
    fallback_reason: str | None = None


class IngestResponse(BaseModel):
    document_count: int
    chunk_count: int
    index_backend: str
    rebuilt_at: datetime


class GitHubIngestRequest(BaseModel):
    repos: list[str] = Field(default_factory=list)
    contribution_repos: list[str] = Field(default_factory=list)
    refresh: bool = True
    rebuild_index: bool = True


class GitHubIngestResponse(BaseModel):
    generated_files: list[str]
    repo_count: int
    contribution_repo_count: int
    index_rebuilt: bool = False
    document_count: int | None = None
    chunk_count: int | None = None
    synced_at: datetime


class AvailabilityRequest(BaseModel):
    start: str
    end: str
    timezone: str | None = None
    max_results: int = Field(default=5, ge=1, le=20)


class AvailabilityResponse(BaseModel):
    slots: list[AvailabilitySlot]


class BookingRequest(BaseModel):
    start: str
    attendee_name: str
    attendee_email: EmailStr
    attendee_timezone: str | None = None
    attendee_phone: str | None = None
    notes: str | None = None


class BookingResponse(BaseModel):
    booking_uid: str
    meeting_url: str | None = None
    start: str
    end: str | None = None
    status: str


class ClientEvent(BaseModel):
    event_type: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    index_ready: bool
    embedding_ready: bool
    chat_ready: bool
    vector_backend: str
