from app.core.config import Settings
from app.services.vapi_admin import (
    PERSONA_ASSISTANT_NAME,
    PERSONA_FIRST_MESSAGE,
    TOOL_FUNCTION_NAME,
    VapiAdminService,
)


class FakeEvaluationLogger:
    def log_failure(self, failure_case: str, details=None):
        return None


def build_service(**overrides):
    settings = Settings(
        _env_file=None,
        VAPI_PRIVATE_API_KEY="private-key",
        VAPI_ASSISTANT_ID="assistant-123",
        VAPI_PHONE_NUMBER_ID="phone-123",
        VAPI_SHARED_SECRET="shared-secret",
        PUBLIC_BACKEND_URL="https://persona.example.com",
        **overrides,
    )
    return VapiAdminService(settings, FakeEvaluationLogger())


def test_vapi_preview_builds_tool_server_url():
    service = build_service()

    preview = service.preview()

    assert preview.ready is True
    assert preview.tool_server_url == "https://persona.example.com/api/vapi/tools"
    assert preview.tool_function_name == TOOL_FUNCTION_NAME


def test_vapi_tool_payload_includes_function_and_secret_header():
    service = build_service()

    payload = service._build_tool_payload("https://persona.example.com/api/vapi/tools")

    assert payload["function"]["name"] == TOOL_FUNCTION_NAME
    assert payload["server"]["url"] == "https://persona.example.com/api/vapi/tools"
    assert payload["server"]["headers"]["X-Vapi-Secret"] == "shared-secret"


def test_vapi_assistant_patch_preserves_existing_model_and_prepends_tool():
    service = build_service()
    current_assistant = {
        "model": {
            "provider": "openai",
            "model": "gpt-4.1",
            "temperature": 0.5,
            "toolIds": ["existing-tool"],
        }
    }

    payload = service._build_assistant_patch_payload(current_assistant, "tool-123")

    assert payload["name"] == PERSONA_ASSISTANT_NAME
    assert payload["firstMessage"] == PERSONA_FIRST_MESSAGE
    assert payload["model"]["provider"] == "openai"
    assert payload["model"]["model"] == "gpt-4.1"
    assert payload["model"]["temperature"] == 0.5
    assert payload["model"]["toolIds"] == ["tool-123", "existing-tool"]
    assert payload["model"]["messages"][0]["role"] == "system"
