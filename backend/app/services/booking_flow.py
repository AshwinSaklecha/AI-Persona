from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import Settings
from app.models.schemas import (
    AvailabilityRequest,
    AvailabilitySlot,
    BookingChatState,
    BookingRequest,
    BookingResponse,
)
from app.services.calcom import CalComService
from app.services.evaluation import EvaluationLogger


BOOKING_KEYWORDS = (
    "book",
    "booking",
    "schedule",
    "meeting",
    "availability",
    "available slot",
    "call",
    "interview",
)
DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2})?)\s*(?:to|-)\s*"
    r"(?P<end>\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2})?)",
    re.IGNORECASE,
)
TIMEZONE_PATTERN = re.compile(r"(?:timezone|tz)\s*[:=]?\s*(?P<value>[A-Za-z_/\-+]+)", re.IGNORECASE)
LABELED_OPTION_PATTERN = re.compile(r"\b(?:option|slot)\s*(?P<index>\d+)\b", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"(?P<email>[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})")
NAME_PATTERN = re.compile(r"\bname\b\s*[:=\-]\s*(?P<name>[^\n,]+)", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"\b(?:phone|number|mobile)\b\s*[:=\-]\s*(?P<phone>[^\n,]+)", re.IGNORECASE)
NOTES_PATTERN = re.compile(r"\bnotes?\b\s*[:=\-]\s*(?P<notes>.+)", re.IGNORECASE | re.DOTALL)
CANCEL_KEYWORDS = ("cancel", "stop", "never mind", "nevermind")


@dataclass(slots=True)
class BookingConversationState:
    stage: Literal[
        "idle",
        "awaiting_window",
        "awaiting_slot_selection",
        "awaiting_contact",
    ] = "idle"
    timezone: str | None = None
    slots: list[AvailabilitySlot] = field(default_factory=list)
    selected_slot: AvailabilitySlot | None = None


@dataclass(slots=True)
class BookingFlowResult:
    answer: str
    booking: BookingChatState


class BookingConversationStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._store: dict[str, BookingConversationState] = {}

    def get(self, conversation_id: str) -> BookingConversationState:
        with self._lock:
            return self._store.get(conversation_id, BookingConversationState())

    def set(self, conversation_id: str, state: BookingConversationState) -> None:
        with self._lock:
            self._store[conversation_id] = state

    def clear(self, conversation_id: str) -> None:
        with self._lock:
            self._store.pop(conversation_id, None)


class BookingFlowService:
    def __init__(
        self,
        *,
        settings: Settings,
        calcom: CalComService,
        evaluation: EvaluationLogger,
        store: BookingConversationStore | None = None,
    ) -> None:
        self.settings = settings
        self.calcom = calcom
        self.evaluation = evaluation
        self.store = store or BookingConversationStore()

    def ensure_conversation_id(self, conversation_id: str | None) -> str:
        return conversation_id or str(uuid4())

    def maybe_handle(self, conversation_id: str, message: str) -> BookingFlowResult | None:
        normalized = message.strip().lower()
        state = self.store.get(conversation_id)

        if state.stage != "idle" and any(keyword in normalized for keyword in CANCEL_KEYWORDS):
            self.store.clear(conversation_id)
            self.evaluation.log_client_event("booking_flow_cancelled", {"conversation_id": conversation_id})
            return BookingFlowResult(
                answer="Booking cancelled. If you want to try again, just ask me to schedule a meeting.",
                booking=BookingChatState(active=False, stage="idle"),
            )

        if state.stage == "idle" and not self._is_booking_intent(normalized):
            return None

        if not self.calcom.ready:
            return BookingFlowResult(
                answer="Scheduling is not configured right now, so I can't check live slots yet.",
                booking=BookingChatState(active=False, stage="idle"),
            )

        if state.stage == "idle":
            self.evaluation.log_client_event("booking_flow_started", {"conversation_id": conversation_id})
            state.stage = "awaiting_window"
            self.store.set(conversation_id, state)

            parsed_window = self._parse_window(message)
            if parsed_window is None:
                return BookingFlowResult(
                    answer=self._window_prompt(),
                    booking=self._public_state(state),
                )

            return self._handle_window(conversation_id, state, parsed_window)

        if state.stage == "awaiting_window":
            parsed_window = self._parse_window(message)
            if parsed_window is None:
                return BookingFlowResult(
                    answer=(
                        "I need an exact availability window before I can suggest live slots. "
                        f"{self._window_prompt()}"
                    ),
                    booking=self._public_state(state),
                )
            return self._handle_window(conversation_id, state, parsed_window)

        if state.stage == "awaiting_slot_selection":
            parsed_window = self._parse_window(message)
            if parsed_window is not None:
                return self._handle_window(conversation_id, state, parsed_window)

            slot = self._parse_slot_selection(message, state.slots)
            if slot is None:
                return BookingFlowResult(
                    answer=(
                        "Pick one of the suggested slots by replying with the slot number, "
                        "or send a new exact date range if you want me to refresh the options."
                    ),
                    booking=self._public_state(state),
                )

            state.selected_slot = slot
            state.stage = "awaiting_contact"
            self.store.set(conversation_id, state)
            self.evaluation.log_client_event(
                "booking_slot_selected",
                {"conversation_id": conversation_id, "slot_start": slot.start},
            )
            return BookingFlowResult(
                answer=(
                    f"I can hold `{slot.label}`. Reply with `Name: ...` and `Email: ...`. "
                    "You can also add `Phone:` or `Notes:` if you want."
                ),
                booking=self._public_state(state),
            )

        if state.stage == "awaiting_contact":
            slot = self._parse_slot_selection(message, state.slots)
            if slot is not None:
                state.selected_slot = slot
                self.store.set(conversation_id, state)

            details = self._parse_contact_details(message)
            if details["name"] is None or details["email"] is None:
                return BookingFlowResult(
                    answer=(
                        "I'm missing the attendee details I need to confirm the booking. "
                        "Please reply with `Name: ...` and `Email: ...`."
                    ),
                    booking=self._public_state(state),
                )

            try:
                booking = self.calcom.book_slot(
                    BookingRequest(
                        start=state.selected_slot.start if state.selected_slot else "",
                        attendee_name=details["name"],
                        attendee_email=details["email"],
                        attendee_timezone=state.timezone or self.settings.timezone,
                        attendee_phone=details["phone"],
                        notes=details["notes"],
                    )
                )
            except Exception as exc:
                self.evaluation.log_failure(
                    "booking_api_error",
                    {"error": str(exc), "action": "chat_booking"},
                )
                return BookingFlowResult(
                    answer=(
                        "I couldn't confirm the booking right now because the scheduling API failed. "
                        "Try again in a moment, or send a fresh date range."
                    ),
                    booking=self._public_state(state),
                )

            self.store.clear(conversation_id)
            self.evaluation.log_client_event(
                "booking_confirmed",
                {
                    "conversation_id": conversation_id,
                    "booking_uid": booking.booking_uid,
                    "slot_start": booking.start,
                },
            )
            return BookingFlowResult(
                answer=self._confirmation_message(booking),
                booking=BookingChatState(
                    active=False,
                    stage="confirmed",
                    selected_slot=state.selected_slot,
                    booking_uid=booking.booking_uid,
                    meeting_url=booking.meeting_url,
                ),
            )

        return None

    def _handle_window(
        self,
        conversation_id: str,
        state: BookingConversationState,
        parsed_window: tuple[str, str, str],
    ) -> BookingFlowResult:
        start, end, timezone_name = parsed_window
        try:
            slots = self.calcom.get_availability(
                AvailabilityRequest(
                    start=start,
                    end=end,
                    timezone=timezone_name,
                    max_results=5,
                )
            )
        except Exception as exc:
            self.evaluation.log_failure(
                "booking_api_error",
                {"error": str(exc), "action": "chat_availability"},
            )
            return BookingFlowResult(
                answer=(
                    "I couldn't fetch live availability from Cal.com just now. "
                    "Please try again in a minute."
                ),
                booking=self._public_state(state),
            )

        if not slots:
            state.stage = "awaiting_window"
            state.timezone = timezone_name
            state.slots = []
            state.selected_slot = None
            self.store.set(conversation_id, state)
            return BookingFlowResult(
                answer=(
                    "I didn't find open slots in that window. "
                    "Send another exact range like `2026-04-15 10:00 to 2026-04-18 18:00`."
                ),
                booking=self._public_state(state),
            )

        state.stage = "awaiting_slot_selection"
        state.timezone = timezone_name
        state.slots = slots
        state.selected_slot = None
        self.store.set(conversation_id, state)
        self.evaluation.log_client_event(
            "booking_slots_suggested",
            {"conversation_id": conversation_id, "slot_count": len(slots)},
        )
        lines = [
            "Here are the live slots I found:",
            "",
            *[f"{index}. {slot.label}" for index, slot in enumerate(slots, start=1)],
            "",
            "Reply with the slot number you want, or send a new exact window if these don't work.",
        ]
        return BookingFlowResult(
            answer="\n".join(lines),
            booking=self._public_state(state),
        )

    @staticmethod
    def _is_booking_intent(message: str) -> bool:
        return any(keyword in message for keyword in BOOKING_KEYWORDS)

    def _window_prompt(self) -> str:
        return (
            "Send an exact time window like "
            "`2026-04-15 10:00 to 2026-04-18 18:00` "
            f"and optionally `Timezone: {self.settings.timezone}`."
        )

    def _parse_window(self, message: str) -> tuple[str, str, str] | None:
        match = DATE_RANGE_PATTERN.search(message)
        if match is None:
            return None

        timezone_name = self._extract_timezone(message)
        start = self._parse_datetime_value(match.group("start"), timezone_name, end_of_day=False)
        end = self._parse_datetime_value(match.group("end"), timezone_name, end_of_day=True)
        if start >= end:
            return None
        return self._to_utc_string(start), self._to_utc_string(end), timezone_name

    def _extract_timezone(self, message: str) -> str:
        match = TIMEZONE_PATTERN.search(message)
        value = match.group("value").strip() if match else self.settings.timezone
        try:
            ZoneInfo(value)
            return value
        except ZoneInfoNotFoundError:
            return self.settings.timezone

    def _parse_datetime_value(self, value: str, timezone_name: str, *, end_of_day: bool) -> datetime:
        normalized = value.strip().replace("T", " ")
        if len(normalized) == 10:
            parsed = datetime.fromisoformat(normalized)
            parsed = datetime.combine(parsed.date(), time(18, 0) if end_of_day else time(9, 0))
        else:
            parsed = datetime.fromisoformat(normalized)
        return parsed.replace(tzinfo=ZoneInfo(timezone_name))

    @staticmethod
    def _to_utc_string(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _parse_slot_selection(message: str, slots: list[AvailabilitySlot]) -> AvailabilitySlot | None:
        stripped = message.strip()
        if stripped.isdigit():
            index = int(stripped) - 1
        else:
            match = LABELED_OPTION_PATTERN.search(message)
            if match is None:
                return None
            index = int(match.group("index")) - 1
        if index < 0 or index >= len(slots):
            return None
        return slots[index]

    @staticmethod
    def _parse_contact_details(message: str) -> dict[str, str | None]:
        name_match = NAME_PATTERN.search(message)
        email_match = EMAIL_PATTERN.search(message)
        phone_match = PHONE_PATTERN.search(message)
        notes_match = NOTES_PATTERN.search(message)

        return {
            "name": name_match.group("name").strip() if name_match else None,
            "email": email_match.group("email").strip() if email_match else None,
            "phone": phone_match.group("phone").strip() if phone_match else None,
            "notes": notes_match.group("notes").strip() if notes_match else None,
        }

    @staticmethod
    def _confirmation_message(booking: BookingResponse) -> str:
        lines = [
            "Your meeting is booked.",
            f"Booking ID: {booking.booking_uid}",
            f"Start: {booking.start}",
            f"Status: {booking.status}",
        ]
        if booking.meeting_url:
            lines.append(f"Meeting link: {booking.meeting_url}")
        return "\n".join(lines)

    @staticmethod
    def _public_state(state: BookingConversationState) -> BookingChatState:
        return BookingChatState(
            active=state.stage != "idle",
            stage=state.stage,
            slots=state.slots,
            selected_slot=state.selected_slot,
        )
