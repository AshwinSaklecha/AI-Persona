from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.deps import get_services
from app.models.schemas import (
    VapiPreviewResponse,
    VapiSyncRequest,
    VapiSyncResponse,
    VapiToolCall,
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


@router.post("/vapi/tools")
async def handle_vapi_tools(
    request: Request,
    services: ServiceContainer = Depends(get_services),
    x_vapi_secret: str | None = Header(default=None),
) -> JSONResponse:
    payload = await request.json()
    call_id, tool_calls = _extract_tool_context(payload)
    secret_error = _verify_vapi_secret(services, x_vapi_secret)
    results: list[dict[str, str]] = []

    for tool_call in tool_calls:
        try:
            if secret_error:
                raise ValueError(secret_error)
            if tool_call.name not in PERSONA_TOOL_NAMES:
                raise ValueError(
                    f"Unsupported tool `{tool_call.name}`. Use one of: {', '.join(sorted(PERSONA_TOOL_NAMES))}."
                )

            prompt = _extract_question(tool_call)
            response = services.persona_chat.respond(prompt, conversation_id=call_id)
            results.append(_success_result(tool_call.id, response.answer))
        except Exception as exc:
            services.evaluation.log_failure(
                "vapi_tool_error",
                {
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.id,
                    "error": str(exc),
                },
            )
            results.append(_error_result(tool_call.id, str(exc) or "Tool execution failed."))

    return JSONResponse(content={"results": results})


def _verify_vapi_secret(services: ServiceContainer, provided_secret: str | None) -> str | None:
    expected_secret = services.settings.vapi_shared_secret
    if expected_secret and provided_secret != expected_secret:
        services.evaluation.log_failure(
            "vapi_auth_failed",
            {"provided": bool(provided_secret)},
        )
        return "Invalid Vapi tool secret."
    return None


def _extract_tool_context(payload: dict) -> tuple[str | None, list[VapiToolCall]]:
    message = payload.get("message") if isinstance(payload, dict) else {}
    if not isinstance(message, dict):
        return None, []

    call = message.get("call")
    call_id = call.get("id") if isinstance(call, dict) else None

    raw_tool_calls = message.get("toolCallList") or []
    parsed_tool_calls: list[VapiToolCall] = []

    if not isinstance(raw_tool_calls, list):
        return call_id, parsed_tool_calls

    for raw_tool_call in raw_tool_calls:
        parsed = _parse_tool_call(raw_tool_call)
        if parsed is not None:
            parsed_tool_calls.append(parsed)

    return call_id, parsed_tool_calls


def _parse_tool_call(raw_tool_call: object) -> VapiToolCall | None:
    if not isinstance(raw_tool_call, dict):
        return None

    name = raw_tool_call.get("name")
    function = raw_tool_call.get("function")
    if not isinstance(name, str) and isinstance(function, dict):
        candidate_name = function.get("name")
        name = candidate_name if isinstance(candidate_name, str) else None

    tool_call_id = raw_tool_call.get("id") or raw_tool_call.get("toolCallId")
    if not isinstance(tool_call_id, str):
        return None

    arguments = raw_tool_call.get("arguments") or {}
    normalized_arguments = _normalize_tool_arguments(arguments)

    return VapiToolCall(
        id=tool_call_id,
        name=name or "",
        arguments=normalized_arguments,
    )


def _normalize_tool_arguments(arguments: object) -> dict[str, object]:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return {"message": arguments}
        if isinstance(parsed, dict):
            return parsed
    return {}


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


def _success_result(tool_call_id: str, result: str) -> dict[str, str]:
    return {
        "toolCallId": tool_call_id,
        "result": _to_single_line(result),
    }


def _error_result(tool_call_id: str, error: str) -> dict[str, str]:
    return {
        "toolCallId": tool_call_id,
        "error": _to_single_line(error),
    }
