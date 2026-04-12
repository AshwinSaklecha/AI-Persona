from __future__ import annotations

from datetime import datetime

import httpx

from app.core.config import Settings
from app.models.schemas import AvailabilityRequest, AvailabilitySlot, BookingRequest, BookingResponse


class CalComService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def ready(self) -> bool:
        return bool(
            self.settings.calcom_api_key
            and self.settings.calcom_username
            and self.settings.calcom_event_type
        )

    def get_availability(self, request: AvailabilityRequest) -> list[AvailabilitySlot]:
        self._ensure_ready()
        response = httpx.get(
            f"{self.settings.calcom_api_base_url}/slots",
            headers=self._headers(self.settings.calcom_slots_api_version),
            params={
                "username": self.settings.calcom_username,
                "eventTypeSlug": self.settings.calcom_event_type,
                "start": request.start,
                "end": request.end,
                "timeZone": request.timezone or self.settings.timezone,
                "duration": self.settings.meeting_duration,
                "format": "range",
            },
            timeout=20.0,
        )
        self._raise_for_status(response)
        payload = response.json()
        slots: list[AvailabilitySlot] = []
        for day in payload.get("data", {}).values():
            for raw_slot in day:
                start = raw_slot.get("start")
                end = raw_slot.get("end")
                slots.append(
                    AvailabilitySlot(
                        start=start,
                        end=end,
                        label=self._format_slot_label(start, request.timezone or self.settings.timezone),
                    )
                )

        slots.sort(key=lambda item: item.start)
        return slots[: request.max_results]

    def book_slot(self, request: BookingRequest) -> BookingResponse:
        self._ensure_ready()
        response = httpx.post(
            f"{self.settings.calcom_api_base_url}/bookings",
            headers=self._headers(self.settings.calcom_bookings_api_version),
            json={
                "start": request.start,
                "eventTypeSlug": self.settings.calcom_event_type,
                "username": self.settings.calcom_username,
                "attendee": {
                    "name": request.attendee_name,
                    "email": request.attendee_email,
                    "timeZone": request.attendee_timezone or self.settings.timezone,
                    **({"phoneNumber": request.attendee_phone} if request.attendee_phone else {}),
                },
                "metadata": {
                    "notes": request.notes or "",
                },
            },
            timeout=20.0,
        )
        self._raise_for_status(response)
        data = response.json()["data"]
        return BookingResponse(
            booking_uid=data["uid"],
            meeting_url=data.get("meetingUrl") or data.get("location"),
            start=data["start"],
            end=data.get("end"),
            status=data["status"],
        )

    def _headers(self, api_version: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.calcom_api_key}",
            "cal-api-version": api_version,
            "Content-Type": "application/json",
        }

    def _ensure_ready(self) -> None:
        if not self.ready:
            raise RuntimeError("Cal.com is not configured.")

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(response.text) from exc

    @staticmethod
    def _format_slot_label(start: str, timezone_name: str) -> str:
        timestamp = datetime.fromisoformat(start.replace("Z", "+00:00"))
        return f"{timestamp.strftime('%a, %d %b %I:%M %p')} ({timezone_name})"
