from app.core.config import Settings
from app.models.schemas import AvailabilitySlot, BookingResponse
from app.services.booking_flow import BookingFlowService


class FakeEvaluationLogger:
    def log_client_event(self, event_type: str, details=None):
        return None

    def log_failure(self, failure_case: str, details=None):
        return None


class FakeCalComService:
    ready = True

    def __init__(self) -> None:
        self.booked = None

    def get_availability(self, request):
        return [
            AvailabilitySlot(
                start="2026-04-15T10:00:00+05:30",
                end="2026-04-15T10:30:00+05:30",
                label="Wed, 15 Apr 10:00 AM (Asia/Kolkata)",
            ),
            AvailabilitySlot(
                start="2026-04-15T11:00:00+05:30",
                end="2026-04-15T11:30:00+05:30",
                label="Wed, 15 Apr 11:00 AM (Asia/Kolkata)",
            ),
        ]

    def book_slot(self, request):
        self.booked = request
        return BookingResponse(
            booking_uid="booking-123",
            meeting_url="https://cal.com/booking-123",
            start=request.start,
            end="2026-04-15T10:30:00+05:30",
            status="ACCEPTED",
        )


def test_booking_flow_runs_from_intent_to_confirmation():
    calcom = FakeCalComService()
    service = BookingFlowService(
        settings=Settings(_env_file=None),
        calcom=calcom,
        evaluation=FakeEvaluationLogger(),
    )
    conversation_id = service.ensure_conversation_id(None)

    first = service.maybe_handle(conversation_id, "Can you book a meeting with me?")
    assert first is not None
    assert first.booking.stage == "awaiting_window"

    second = service.maybe_handle(
        conversation_id,
        "2026-04-15 10:00 to 2026-04-18 18:00 timezone: Asia/Kolkata",
    )
    assert second is not None
    assert second.booking.stage == "awaiting_slot_selection"
    assert len(second.booking.slots) == 2

    third = service.maybe_handle(conversation_id, "1")
    assert third is not None
    assert third.booking.stage == "awaiting_contact"
    assert third.booking.selected_slot is not None

    fourth = service.maybe_handle(
        conversation_id,
        "Name: Test User, Email: test@example.com, Notes: Looking forward to it",
    )
    assert fourth is not None
    assert fourth.booking.stage == "confirmed"
    assert fourth.booking.booking_uid == "booking-123"
    assert calcom.booked is not None
    assert calcom.booked.attendee_email == "test@example.com"


def test_booking_flow_accepts_hyphenated_contact_fields_and_inline_slot_change():
    calcom = FakeCalComService()
    service = BookingFlowService(
        settings=Settings(_env_file=None),
        calcom=calcom,
        evaluation=FakeEvaluationLogger(),
    )
    conversation_id = service.ensure_conversation_id(None)

    service.maybe_handle(conversation_id, "Book a meeting with me")
    service.maybe_handle(
        conversation_id,
        "2026-04-15 10:00 to 2026-04-18 18:00 timezone: Asia/Kolkata",
    )
    service.maybe_handle(conversation_id, "1")

    result = service.maybe_handle(
        conversation_id,
        "slot 2, name - samay raina, email - maisamayhoon@gmail.com, number - 911",
    )

    assert result is not None
    assert result.booking.stage == "confirmed"
    assert calcom.booked is not None
    assert calcom.booked.attendee_name == "samay raina"
    assert calcom.booked.attendee_email == "maisamayhoon@gmail.com"
    assert calcom.booked.attendee_phone == "911"
    assert calcom.booked.start == "2026-04-15T11:00:00+05:30"


def test_booking_flow_ignores_non_booking_messages():
    service = BookingFlowService(
        settings=Settings(_env_file=None),
        calcom=FakeCalComService(),
        evaluation=FakeEvaluationLogger(),
    )

    result = service.maybe_handle("conversation-1", "Tell me about your DeepChem work")

    assert result is None


def test_booking_window_is_converted_to_utc_for_calcom():
    service = BookingFlowService(
        settings=Settings(_env_file=None),
        calcom=FakeCalComService(),
        evaluation=FakeEvaluationLogger(),
    )

    parsed = service._parse_window(
        "2026-04-15 10:00 to 2026-04-18 18:00 timezone: Asia/Kolkata"
    )

    assert parsed is not None
    start, end, timezone_name = parsed
    assert start.endswith("Z")
    assert end.endswith("Z")
    assert start == "2026-04-15T04:30:00Z"
    assert end == "2026-04-18T12:30:00Z"
    assert timezone_name == "Asia/Kolkata"
