from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_services
from app.models.schemas import (
    VapiPreviewResponse,
    VapiSyncRequest,
    VapiSyncResponse,
    VapiToolCall,
    VapiToolRequest,
    VapiToolResponse,
    VapiToolResult,
)
from app.services.container import ServiceContainer


router = APIRouter(tags=["vapi"])

PERSONA_TOOL_NAMES = {"ask_persona", "ask_ashwin", "persona_chat"}
BACKTICK_PATTERN = re.compile(r"`([^`]*)`")


@router.get("/vapi/preview", response_model=VapiPreviewResponse)
def preview_vapi_configuration(services: ServiceContainer = Depends(get_services)) -> VapiPreviewResponse:
    return services.vapi_admin.preview()


@router.post("/vapi/sync", response_model=VapiSyncResponse)
def sync_vapi_configuration(
    request: VapiSyncRequest,
    services: ServiceContainer = Depends(get_services),
) -> VapiSyncResponse:
    if not services.vapi_admin.ready:
        raise HTTPException(status_code=503, detail="Vapi admin configuration is not complete.")

    try:
        return services.vapi_admin.sync(
            request.public_backend_url,
            sync_phone_number=request.sync_phone_number,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/vapi/tools", response_model=VapiToolResponse)
def handle_vapi_tools(
    request: VapiToolRequest,
    services: ServiceContainer = Depends(get_services),
    x_vapi_secret: str | None = Header(default=None),
) -> VapiToolResponse:
    _verify_vapi_secret(services, x_vapi_secret)
    call_id = request.message.call.id if request.message.call else None
    results: list[VapiToolResult] = []

    for tool_call in request.message.toolCallList:
        try:
            if tool_call.name not in PERSONA_TOOL_NAMES:
                raise ValueError(
                    f"Unsupported tool `{tool_call.name}`. Use one of: {', '.join(sorted(PERSONA_TOOL_NAMES))}."
                )

            prompt = _extract_question(tool_call)
            response = services.persona_chat.respond(prompt, conversation_id=call_id)
            results.append(
                VapiToolResult(
                    toolCallId=tool_call.id,
                    result=_to_single_line(response.answer),
                )
            )
        except Exception as exc:
            services.evaluation.log_failure(
                "vapi_tool_error",
                {
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.id,
                    "error": str(exc),
                },
            )
            results.append(
                VapiToolResult(
                    toolCallId=tool_call.id,
                    error=_to_single_line(str(exc) or "Tool execution failed."),
                )
            )

    return VapiToolResponse(results=results)


def _verify_vapi_secret(services: ServiceContainer, provided_secret: str | None) -> None:
    expected_secret = services.settings.vapi_shared_secret
    if expected_secret and provided_secret != expected_secret:
        services.evaluation.log_failure(
            "vapi_auth_failed",
            {"provided": bool(provided_secret)},
        )
        raise HTTPException(status_code=403, detail="Invalid Vapi tool secret.")


def _extract_question(tool_call: VapiToolCall) -> str:
    arguments = tool_call.arguments
    for key in ("message", "question", "query", "prompt"):
        value = arguments.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError("Tool call is missing a `message` string.")


def _to_single_line(value: str) -> str:
    without_code_ticks = BACKTICK_PATTERN.sub(r"\1", value)
    return " ".join(without_code_ticks.split())
