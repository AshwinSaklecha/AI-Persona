"use client";

import { useState } from "react";

import { bookSlot, BookingResponse, fetchAvailability, type AvailabilitySlot } from "@/lib/api";

function toInputValue(date: Date) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}

export function BookingPanel() {
  const [rangeStart, setRangeStart] = useState(() => {
    const start = new Date();
    start.setDate(start.getDate() + 1);
    start.setHours(10, 0, 0, 0);
    return toInputValue(start);
  });

  const [rangeEnd, setRangeEnd] = useState(() => {
    const start = new Date();
    start.setDate(start.getDate() + 1);
    start.setHours(10, 0, 0, 0);
    const end = new Date(start);
    end.setDate(end.getDate() + 7);
    end.setHours(18, 0, 0, 0);
    return toInputValue(end);
  });
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<AvailabilitySlot | null>(null);
  const [attendeeName, setAttendeeName] = useState("");
  const [attendeeEmail, setAttendeeEmail] = useState("");
  const [notes, setNotes] = useState("");
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [booking, setBooking] = useState<BookingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadSlots() {
    setLoadingSlots(true);
    setError(null);
    setBooking(null);

    try {
      const response = await fetchAvailability({
        start: new Date(rangeStart).toISOString(),
        end: new Date(rangeEnd).toISOString(),
        timezone: "Asia/Kolkata",
        max_results: 6
      });
      setSlots(response.slots);
      setSelectedSlot(response.slots[0] ?? null);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to fetch available slots."
      );
    } finally {
      setLoadingSlots(false);
    }
  }

  async function confirmBooking() {
    if (!selectedSlot || !attendeeName.trim() || !attendeeEmail.trim()) {
      setError("Pick a slot and add your name and email.");
      return;
    }

    setError(null);

    try {
      const response = await bookSlot({
        start: selectedSlot.start,
        attendee_name: attendeeName.trim(),
        attendee_email: attendeeEmail.trim(),
        attendee_timezone: "Asia/Kolkata",
        notes
      });
      setBooking(response);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to create the booking."
      );
    }
  }

  return (
    <section className="panel booking-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Cal.com booking</p>
          <h2>Check live availability</h2>
        </div>
      </div>

      <div className="field-grid">
        <label>
          <span>From</span>
          <input
            type="datetime-local"
            value={rangeStart}
            onChange={(event) => setRangeStart(event.target.value)}
          />
        </label>
        <label>
          <span>To</span>
          <input
            type="datetime-local"
            value={rangeEnd}
            onChange={(event) => setRangeEnd(event.target.value)}
          />
        </label>
      </div>

      <button onClick={loadSlots} disabled={loadingSlots}>
        {loadingSlots ? "Loading slots..." : "Suggest slots"}
      </button>

      <div className="slot-list">
        {slots.map((slot) => (
          <button
            key={slot.start}
            className={`slot-chip ${selectedSlot?.start === slot.start ? "active" : ""}`}
            onClick={() => setSelectedSlot(slot)}
            type="button"
          >
            {slot.label}
          </button>
        ))}
      </div>

      <div className="field-grid">
        <label>
          <span>Name</span>
          <input
            type="text"
            value={attendeeName}
            onChange={(event) => setAttendeeName(event.target.value)}
            placeholder="Your name"
          />
        </label>
        <label>
          <span>Email</span>
          <input
            type="email"
            value={attendeeEmail}
            onChange={(event) => setAttendeeEmail(event.target.value)}
            placeholder="you@example.com"
          />
        </label>
      </div>

      <label>
        <span>Notes</span>
        <textarea
          rows={3}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="What should I know before the call?"
        />
      </label>

      <button
        className="secondary"
        onClick={confirmBooking}
        type="button"
        disabled={!selectedSlot}
      >
        Confirm booking
      </button>

      {booking ? (
        <div className="success-card">
          <strong>Booked</strong>
          <p>Status: {booking.status}</p>
          <p>Booking ID: {booking.booking_uid}</p>
          {booking.meeting_url ? (
            <a href={booking.meeting_url} target="_blank" rel="noreferrer">
              Open meeting link
            </a>
          ) : null}
        </div>
      ) : null}

      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
