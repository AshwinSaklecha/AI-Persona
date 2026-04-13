from __future__ import annotations

from time import sleep
from typing import Any

import httpx

from app.core.config import Settings


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = settings.llm_provider.lower().strip()
        self._client: Any | None = None
        self._types: Any | None = None
        self._http_client: httpx.Client | None = None
        self._import_error: Exception | None = None

        if self.provider == "groq":
            if settings.groq_api_key:
                self._http_client = httpx.Client(
                    base_url=settings.groq_api_base_url.rstrip("/"),
                    timeout=30.0,
                    trust_env=False,
                )
            return

        if not settings.gemini_api_key:
            return

        try:
            from google import genai
            from google.genai import types
        except Exception as exc:  # pragma: no cover - import-path safety
            self._import_error = exc
            return

        self._client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(clientArgs={"trust_env": False}),
        )
        self._types = types

    @property
    def ready(self) -> bool:
        if self.provider == "groq":
            return bool(self.settings.groq_api_key and self._http_client)
        return self._client is not None and self._types is not None

    def generate(self, system_instruction: str, user_content: str) -> str:
        if not self.ready:
            if self.provider == "groq":
                raise RuntimeError("Groq chat client is not configured.")
            raise RuntimeError("Gemini chat client is not configured.") from self._import_error

        last_error: Exception | None = None

        for model_name in self._candidate_models():
            for attempt in range(1, self.settings.llm_generation_max_attempts + 1):
                try:
                    return self._generate_with_model(
                        model_name=model_name,
                        system_instruction=system_instruction,
                        user_content=user_content,
                    )
                except Exception as exc:
                    last_error = exc
                    if not self._is_retryable_generation_error(exc):
                        raise

                    if attempt >= self.settings.llm_generation_max_attempts:
                        break

                    sleep(self._retry_delay_seconds(attempt, exc))

        if last_error is not None:
            raise last_error
        raise RuntimeError("LLM generation failed without an exception.")

    def _generate_with_model(
        self,
        *,
        model_name: str,
        system_instruction: str,
        user_content: str,
    ) -> str:
        if self.provider == "groq":
            return self._generate_with_groq(
                model_name=model_name,
                system_instruction=system_instruction,
                user_content=user_content,
            )
        return self._generate_with_gemini(
            model_name=model_name,
            system_instruction=system_instruction,
            user_content=user_content,
        )

    def _generate_with_gemini(
        self,
        *,
        model_name: str,
        system_instruction: str,
        user_content: str,
    ) -> str:
        response = self._client.models.generate_content(
            model=model_name,
            contents=user_content,
            config=self._build_gemini_config(system_instruction),
        )
        return (response.text or "").strip()

    def _generate_with_groq(
        self,
        *,
        model_name: str,
        system_instruction: str,
        user_content: str,
    ) -> str:
        if not self._http_client or not self.settings.groq_api_key:
            raise RuntimeError("Groq chat client is not configured.")

        response = self._http_client.post(
            "chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "temperature": self.settings.llm_temperature,
                "max_tokens": self.settings.llm_max_output_tokens,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content},
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices") or []
        content = ""
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
        return content.strip()

    def _build_gemini_config(self, system_instruction: str) -> Any:
        return self._types.GenerateContentConfig(
            temperature=self.settings.llm_temperature,
            system_instruction=system_instruction,
            thinking_config=self._types.ThinkingConfig(thinking_budget=0),
        )

    def _candidate_models(self) -> list[str]:
        if self.provider == "groq":
            models = [self.settings.groq_chat_model]
            fallback_model = self.settings.groq_chat_fallback_model
        else:
            models = [self.settings.gemini_chat_model]
            fallback_model = self.settings.gemini_chat_fallback_model

        if fallback_model and fallback_model not in models:
            models.append(fallback_model)
        return models

    def _retry_delay_seconds(self, attempt: int, exc: Exception) -> float:
        base_seconds = self.settings.llm_generation_retry_base_delay_ms / 1000
        lowered = str(exc).lower()
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        multiplier = 4 if status_code == 429 or "429" in lowered or "too many requests" in lowered else 1
        return base_seconds * multiplier * (2 ** max(attempt - 1, 0))

    @staticmethod
    def _is_retryable_generation_error(exc: Exception) -> bool:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if status_code in {408, 429, 500, 502, 503, 504}:
            return True

        message = str(exc).lower()
        return (
            "503" in message
            or "429" in message
            or "500" in message
            or "502" in message
            or "504" in message
            or "service unavailable" in message
            or "unavailable" in message
            or "overloaded" in message
            or "too many requests" in message
            or "resource exhausted" in message
            or "rate limit" in message
            or "timeout" in message
        )


GeminiLLMService = LLMService
