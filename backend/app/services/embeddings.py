from __future__ import annotations

from typing import Any

from app.core.config import Settings


class GeminiEmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Any | None = None
        self._import_error: Exception | None = None

        if not settings.gemini_api_key:
            return

        try:
            from google import genai
        except Exception as exc:  # pragma: no cover - import-path safety
            self._import_error = exc
            return

        self._client = genai.Client(api_key=settings.gemini_api_key)

    @property
    def ready(self) -> bool:
        return self._client is not None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self._client:
            raise RuntimeError("Gemini embedding client is not configured.") from self._import_error
        if not texts:
            return []

        response = self._client.models.embed_content(
            model=self.settings.gemini_embedding_model,
            contents=texts,
        )
        return [list(item.values) for item in response.embeddings]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

