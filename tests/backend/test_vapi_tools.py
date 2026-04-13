from app.api.vapi import (
    _error_result,
    _extract_question,
    _extract_tool_context,
    _success_result,
    _to_single_line,
)
from app.models.schemas import VapiToolCall


def test_extract_question_prefers_supported_argument_keys():
    tool_call = VapiToolCall(
        id="tool-1",
        name="ask_persona",
        arguments={"query": "Tell me about kv-cache"},
    )

    assert _extract_question(tool_call) == "Tell me about kv-cache"


def test_to_single_line_removes_backticks_and_line_breaks():
    result = _to_single_line("Here are the slots:\n`1.` Tomorrow at 10:00 AM")

    assert result == "Here are the slots: 1. Tomorrow at 10:00 AM"


def test_extract_tool_context_accepts_nested_function_name_and_json_arguments():
    payload = {
        "message": {
            "call": {"id": "call-123"},
            "toolCallList": [
                {
                    "id": "tool-1",
                    "function": {"name": "ask_persona"},
                    "arguments": '{"message":"Tell me about your projects"}',
                }
            ],
        }
    }

    call_id, tool_calls = _extract_tool_context(payload)

    assert call_id == "call-123"
    assert len(tool_calls) == 1
    assert tool_calls[0].name == "ask_persona"
    assert tool_calls[0].arguments["message"] == "Tell me about your projects"


def test_success_result_omits_error_key():
    result = _success_result("tool-1", "Hello from Ashwin")

    assert result == {"toolCallId": "tool-1", "result": "Hello from Ashwin"}


def test_error_result_omits_result_key():
    result = _error_result("tool-1", "Invalid Vapi tool secret.")

    assert result == {"toolCallId": "tool-1", "error": "Invalid Vapi tool secret."}
