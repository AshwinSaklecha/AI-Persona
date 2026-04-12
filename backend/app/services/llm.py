from __future__ import annotations

from typing import Any

from app.core.config import Settings


class GeminiLLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Any | None = None
        self._types: Any | None = None
        self._import_error: Exception | None = None

        if not settings.gemini_api_key:
            return

        try:
            from google import genai
            from google.genai import types
        except Exception as exc:  # pragma: no cover - import-path safety
            self._import_error = exc
            return

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._types = types

    @property
    def ready(self) -> bool:
        return self._client is not None and self._types is not None

    def generate(self, system_instruction: str, user_content: str) -> str:
        if not self.ready:
            raise RuntimeError("Gemini chat client is not configured.") from self._import_error

        config = self._types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=system_instruction,
            thinking_config=self._types.ThinkingConfig(thinking_budget=0),
        )
        response = self._client.models.generate_content(
            model=self.settings.gemini_chat_model,
            contents=user_content,
            config=config,
        )
        return (response.text or "").strip()

