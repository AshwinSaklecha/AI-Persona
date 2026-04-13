from app.core.config import Settings
from app.services.llm import LLMService


def build_service(outcomes, **setting_overrides):
    settings = Settings(
        llm_provider="groq",
        groq_api_key="test-key",
        groq_chat_model="llama-3.3-70b-versatile",
        groq_chat_fallback_model="llama-3.1-8b-instant",
        llm_generation_max_attempts=2,
        llm_generation_retry_base_delay_ms=1,
        _env_file=None,
        **setting_overrides,
    )
    service = LLMService.__new__(LLMService)
    service.settings = settings
    service.provider = settings.llm_provider
    service._client = None
    service._types = None
    service._http_client = object()
    service._import_error = None
    service._outcomes = list(outcomes)
    service.calls = []

    def fake_generate_with_model(*, model_name, system_instruction, user_content):
        service.calls.append(
            {
                "model": model_name,
                "system_instruction": system_instruction,
                "user_content": user_content,
            }
        )
        outcome = service._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    service._generate_with_model = fake_generate_with_model
    return service


def test_llm_retries_transient_503_before_succeeding():
    service = build_service(
        [
            RuntimeError("503 Service Unavailable"),
            "Recovered response",
        ]
    )

    answer = service.generate("system", "user")

    assert answer == "Recovered response"
    assert [call["model"] for call in service.calls] == [
        "llama-3.3-70b-versatile",
        "llama-3.3-70b-versatile",
    ]


def test_llm_falls_back_to_secondary_model_after_primary_retries_fail():
    service = build_service(
        [
            RuntimeError("503 Service Unavailable"),
            RuntimeError("503 Service Unavailable"),
            "Fallback response",
        ]
    )

    answer = service.generate("system", "user")

    assert answer == "Fallback response"
    assert [call["model"] for call in service.calls] == [
        "llama-3.3-70b-versatile",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]


def test_llm_raises_non_retryable_errors_immediately():
    service = build_service([RuntimeError("401 Unauthorized")])

    try:
        service.generate("system", "user")
    except RuntimeError as exc:
        assert "401" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected a non-retryable error to be raised.")


def test_llm_retries_on_429_rate_limit_errors():
    service = build_service(
        [
            RuntimeError("429 Too Many Requests"),
            "Recovered after rate limit",
        ]
    )

    answer = service.generate("system", "user")

    assert answer == "Recovered after rate limit"
    assert [call["model"] for call in service.calls] == [
        "llama-3.3-70b-versatile",
        "llama-3.3-70b-versatile",
    ]


def test_llm_ready_for_groq_when_api_key_is_present():
    settings = Settings(
        llm_provider="groq",
        groq_api_key="test-key",
        _env_file=None,
    )
    service = LLMService(settings)

    assert service.ready is True
