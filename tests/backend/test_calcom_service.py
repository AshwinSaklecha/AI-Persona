from app.core.config import Settings
from app.models.schemas import BookingRequest
from app.services.calcom import CalComService


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.text = str(payload)

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_book_slot_does_not_send_length_in_minutes(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["json"] = json
        return FakeResponse(
            {
                "data": {
                    "uid": "booking-123",
                    "meetingUrl": "https://cal.com/booking-123",
                    "start": json["start"],
                    "end": "2026-04-15T10:30:00.000+05:30",
                    "status": "ACCEPTED",
                }
            }
        )

    monkeypatch.setattr("app.services.calcom.httpx.post", fake_post)

    service = CalComService(
        Settings(
            calcom_api_key="key",
            calcom_username="ashwinsaklecha",
            calcom_event_type="30min",
            _env_file=None,
        )
    )
    response = service.book_slot(
        BookingRequest(
            start="2026-04-15T10:00:00.000+05:30",
            attendee_name="samay raina",
            attendee_email="maisamayhoon@gmail.com",
            attendee_timezone="Asia/Kolkata",
            attendee_phone="911",
            notes="hello",
        )
    )

    assert "lengthInMinutes" not in captured["json"]
    assert captured["json"]["eventTypeSlug"] == "30min"
    assert response.booking_uid == "booking-123"

