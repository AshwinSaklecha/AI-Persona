from __future__ import annotations

import json
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from app.core.config import Settings


FAILURE_CASES = {
    "no_retrieval_match",
    "low_similarity_context",
    "booking_api_error",
    "voice_interrupted",
    "voice_unsupported",
    "llm_generation_error",
    "startup_ingest_failed",
    "github_sync_failed",
    "vapi_tool_error",
    "vapi_auth_failed",
    "voice_call_error",
}


class EvaluationLogger:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = Lock()

    def log_chat(
        self,
        *,
        query: str,
        latency_ms: int,
        retrieval_hits: int,
        top_score: float | None,
        fallback_reason: str | None,
        answer_mode: str,
    ) -> None:
        self._write(
            {
                "event_type": "chat_response",
                "timestamp": self._timestamp(),
                "query": query,
                "latency_ms": latency_ms,
                "retrieval_hits": retrieval_hits,
                "top_score": top_score,
                "fallback_triggered": fallback_reason is not None,
                "fallback_reason": fallback_reason,
                "answer_mode": answer_mode,
            }
        )

    def log_failure(self, failure_case: str, details: dict[str, Any] | None = None) -> None:
        self._write(
            {
                "event_type": "failure_case",
                "timestamp": self._timestamp(),
                "failure_case": failure_case,
                "details": details or {},
            }
        )

    def log_client_event(self, event_type: str, details: dict[str, Any] | None = None) -> None:
        self._write(
            {
                "event_type": event_type,
                "timestamp": self._timestamp(),
                "details": details or {},
            }
        )

    def _write(self, payload: dict[str, Any]) -> None:
        with self._lock:
            with self.settings.evaluation_log_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(payload, ensure_ascii=True) + "\n")

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
