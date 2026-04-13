from app.models.schemas import BookingChatState, ChatResponse, RetrievedChunk
from app.services.persona_chat import PersonaChatService


class FakeBookingFlow:
    def ensure_conversation_id(self, conversation_id):
        return conversation_id or "conversation-1"

    def maybe_handle(self, conversation_id, message):
        if "book" not in message.lower():
            return None
        return type(
            "BookingResult",
            (),
            {
                "answer": "Your meeting is booked.",
                "booking": BookingChatState(active=False, stage="confirmed"),
            },
        )()

class FakeRetrieval:
    def __init__(self, fallback_reason=None):
        self.fallback_reason = fallback_reason

    def is_persona_question(self, message):
        return True

    def retrieve(self, message, top_k):
        return [
            RetrievedChunk(
                id="chunk-1",
                source_id="source-1",
                source_title="Resume",
                source_type="resume",
                text="Ashwin built kv-cache.",
                score=0.91,
            )
        ]

    def should_fallback(self, message, chunks):
        return self.fallback_reason


class FakePrompt:
    answer_mode = "grounded"
    system_instruction = "system"
    user_content = "user"


class FakePromptBuilder:
    def build(self, query, retrieved_chunks, persona_question):
        return FakePrompt()


class FakeLLM:
    def generate(self, system_instruction, user_content):
        return "Grounded answer"


class FakeEvaluation:
    def log_chat(self, **kwargs):
        return None

    def log_failure(self, failure_case, details=None):
        return None


def test_persona_chat_returns_booking_result_before_retrieval():
    service = PersonaChatService(
        retrieval=FakeRetrieval(),
        prompt_builder=FakePromptBuilder(),
        llm=FakeLLM(),
        evaluation=FakeEvaluation(),
        booking_flow=FakeBookingFlow(),
        retrieval_top_k=5,
    )

    response = service.respond("Please book a meeting with me")

    assert isinstance(response, ChatResponse)
    assert response.answer_mode == "booking"
    assert response.booking is not None
    assert response.booking.stage == "confirmed"


def test_persona_chat_uses_fallback_when_retrieval_is_weak():
    service = PersonaChatService(
        retrieval=FakeRetrieval(fallback_reason="no_retrieval_match"),
        prompt_builder=FakePromptBuilder(),
        llm=FakeLLM(),
        evaluation=FakeEvaluation(),
        booking_flow=FakeBookingFlow(),
        retrieval_top_k=5,
    )

    response = service.respond("Did I work at Google?")

    assert response.answer_mode == "fallback"
    assert response.fallback_triggered is True
    assert response.fallback_reason == "no_retrieval_match"


def test_persona_chat_normalizes_markdown_bullets_for_plain_text_ui():
    class MarkdownLLM:
        def generate(self, system_instruction, user_content):
            return "**Ashwin**\n\n* Backend engineer in training\n* Open-source contributor"

    service = PersonaChatService(
        retrieval=FakeRetrieval(),
        prompt_builder=FakePromptBuilder(),
        llm=MarkdownLLM(),
        evaluation=FakeEvaluation(),
        booking_flow=FakeBookingFlow(),
        retrieval_top_k=5,
    )

    response = service.respond("Tell me about yourself")

    assert response.answer == "Ashwin\n\n- Backend engineer in training\n- Open-source contributor"
