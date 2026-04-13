from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import Settings
from app.models.schemas import VapiPreviewResponse, VapiSyncResponse
from app.services.evaluation import EvaluationLogger


TOOL_FUNCTION_NAME = "ask_persona"
PERSONA_ASSISTANT_NAME = "Ashwin Persona"
PERSONA_FIRST_MESSAGE = (
    "Hi, this is Ashwin's AI representative. I can talk about Ashwin's background, "
    "projects, and help book a time to chat. What would you like to know?"
)
PERSONA_END_CALL_MESSAGE = (
    "Thanks for the conversation. If you'd like, I can help you book a time to talk with Ashwin."
)
PERSONA_VOICEMAIL_MESSAGE = (
    "Hi, this is Ashwin's AI representative following up. Feel free to call back when it's convenient."
)
PERSONA_SYSTEM_PROMPT = """You are Ashwin Saklecha's AI representative.

Speak in first person as Ashwin when discussing Ashwin's background, experience, projects, and fit.
Your tone is honest, slightly informal, clear, and never exaggerated.

Important rules:
- On every user turn, call the `ask_persona` tool with the user's latest message.
- Use the tool for resume questions, GitHub/project questions, booking requests, follow-up booking turns, and general conversation.
- If the tool returns a normal answer, speak that answer directly. Do not reinterpret it, summarize it differently, or ask an extra clarifying question.
- If the tool returns booking instructions or available slots, read them directly and ask only the exact follow-up needed to continue booking.
- If the tool says it does not know, be direct and honest instead of guessing.
- Only ask a clarifying question if the tool itself asks for clarification or the tool result explicitly says more detail is needed.
- Do not say there was a technical issue, a calendar issue, or an access problem unless the tool result explicitly says that.
- Do not add filler like 'let me check', 'one moment', or repeated apologies after the tool returns.
- Keep spoken answers concise and natural.
- Do not invent facts about Ashwin, his resume, his GitHub work, or his availability.
- When the tool returns booking slots, read them clearly and ask the caller which option they want.
"""


class VapiAdminService:
    def __init__(self, settings: Settings, evaluation: EvaluationLogger) -> None:
        self.settings = settings
        self.evaluation = evaluation

    @property
    def ready(self) -> bool:
        return bool(self.settings.vapi_private_api_key and self.settings.vapi_assistant_id)

    def preview(self, public_backend_url: str | None = None) -> VapiPreviewResponse:
        resolved_url = self._resolve_public_backend_url(public_backend_url)
        return VapiPreviewResponse(
            ready=self.ready and bool(resolved_url),
            assistant_id=self.settings.vapi_assistant_id,
            phone_number_id=self.settings.vapi_phone_number_id,
            public_backend_url=resolved_url,
            tool_server_url=self._build_tool_server_url(resolved_url) if resolved_url else None,
            tool_function_name=TOOL_FUNCTION_NAME,
        )

    def sync(self, public_backend_url: str | None = None, *, sync_phone_number: bool = True) -> VapiSyncResponse:
        if not self.ready:
            raise RuntimeError("Vapi admin configuration is incomplete.")

        resolved_url = self._resolve_public_backend_url(public_backend_url)
        if not resolved_url:
            raise RuntimeError("PUBLIC_BACKEND_URL is required before syncing Vapi.")

        tool_server_url = self._build_tool_server_url(resolved_url)
        existing_tool = self._find_existing_tool(TOOL_FUNCTION_NAME)
        if existing_tool is None:
            tool = self._create_tool(tool_server_url)
            tool_created = True
        else:
            tool = self._update_tool(existing_tool["id"], tool_server_url)
            tool_created = False

        assistant = self._get_assistant(self.settings.vapi_assistant_id or "")
        self._update_assistant(assistant, tool["id"])

        phone_updated = False
        if sync_phone_number and self.settings.vapi_phone_number_id:
            self._update_phone_number(self.settings.vapi_phone_number_id, self.settings.vapi_assistant_id or "")
            phone_updated = True

        return VapiSyncResponse(
            tool_id=tool["id"],
            tool_created=tool_created,
            tool_server_url=tool_server_url,
            assistant_id=self.settings.vapi_assistant_id or "",
            phone_number_id=self.settings.vapi_phone_number_id,
            phone_number_updated=phone_updated,
            synced_at=datetime.now(timezone.utc),
        )

    def _resolve_public_backend_url(self, override: str | None) -> str | None:
        candidate = (override or self.settings.public_backend_url or "").strip()
        return candidate.rstrip("/") or None

    def _build_tool_server_url(self, public_backend_url: str) -> str:
        return f"{public_backend_url}/api/vapi/tools"

    def _find_existing_tool(self, function_name: str) -> dict[str, Any] | None:
        tools = self._request("GET", "/tool")
        if not isinstance(tools, list):
            return None
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            if tool.get("type") != "function":
                continue
            function = tool.get("function") or {}
            if function.get("name") == function_name:
                return tool
        return None

    def _create_tool(self, tool_server_url: str) -> dict[str, Any]:
        return self._request("POST", "/tool", json=self._build_tool_payload(tool_server_url))

    def _update_tool(self, tool_id: str, tool_server_url: str) -> dict[str, Any]:
        payload = self._build_tool_payload(tool_server_url)
        payload.pop("type", None)
        return self._request("PATCH", f"/tool/{tool_id}", json=payload)

    def _get_assistant(self, assistant_id: str) -> dict[str, Any]:
        return self._request("GET", f"/assistant/{assistant_id}")

    def _update_assistant(self, current_assistant: dict[str, Any], tool_id: str) -> dict[str, Any]:
        assistant_id = current_assistant.get("id") or self.settings.vapi_assistant_id or ""
        payload = self._build_assistant_patch_payload(current_assistant, tool_id)
        return self._request("PATCH", f"/assistant/{assistant_id}", json=payload)

    def _update_phone_number(self, phone_number_id: str, assistant_id: str) -> dict[str, Any]:
        payload = {
            "assistantId": assistant_id,
            "name": "Persona",
            "server": {
                "timeoutSeconds": 20,
            },
        }
        return self._request("PATCH", f"/phone-number/{phone_number_id}", json=payload)

    def _build_tool_payload(self, tool_server_url: str) -> dict[str, Any]:
        server: dict[str, Any] = {"url": tool_server_url}
        if self.settings.vapi_shared_secret:
            server["headers"] = {"X-Vapi-Secret": self.settings.vapi_shared_secret}

        return {
            "type": "function",
            "function": {
                "name": TOOL_FUNCTION_NAME,
                "description": (
                    "Returns Ashwin's grounded response for resume questions, project questions, "
                    "general follow-ups, and scheduling or booking requests."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The user's latest message, verbatim.",
                        }
                    },
                    "required": ["message"],
                },
            },
            "server": server,
        }

    def _build_assistant_patch_payload(
        self,
        current_assistant: dict[str, Any],
        tool_id: str,
    ) -> dict[str, Any]:
        current_model = dict(current_assistant.get("model") or {})
        existing_tool_ids = list(current_model.get("toolIds") or [])
        merged_tool_ids = [tool_id, *[value for value in existing_tool_ids if value != tool_id]]

        patched_model = {
            **current_model,
            "messages": [{"role": "system", "content": PERSONA_SYSTEM_PROMPT}],
            "toolIds": merged_tool_ids,
            "temperature": 0.1,
        }

        return {
            "name": PERSONA_ASSISTANT_NAME,
            "firstMessage": PERSONA_FIRST_MESSAGE,
            "endCallMessage": PERSONA_END_CALL_MESSAGE,
            "voicemailMessage": PERSONA_VOICEMAIL_MESSAGE,
            "model": patched_model,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        headers = {"Authorization": f"Bearer {self.settings.vapi_private_api_key}"}
        url = f"{self.settings.vapi_api_base_url}{path}"

        try:
            with httpx.Client(timeout=20) as client:
                response = client.request(method, url, headers=headers, json=json)
        except Exception as exc:  # pragma: no cover - network failures vary by environment
            self.evaluation.log_failure("vapi_tool_error", {"path": path, "error": str(exc)})
            raise RuntimeError(f"Vapi request failed for `{path}`.") from exc

        if response.is_error:
            self.evaluation.log_failure(
                "vapi_tool_error",
                {
                    "path": path,
                    "status_code": response.status_code,
                    "response_text": response.text,
                },
            )
            raise RuntimeError(f"Vapi API returned {response.status_code} for `{path}`: {response.text}")

        return response.json()
