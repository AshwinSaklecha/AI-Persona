from app.api.vapi import _extract_question, _to_single_line
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
