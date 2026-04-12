export type RetrievedChunk = {
  id: string;
  source_id: string;
  source_title: string;
  source_type: string;
  text: string;
  url?: string | null;
  score: number;
  metadata: Record<string, unknown>;
};

export type ChatResponse = {
  answer: string;
  answer_mode: "grounded" | "general" | "fallback" | "booking";
  conversation_id: string;
  sources: RetrievedChunk[];
  booking?: BookingChatState | null;
  latency_ms: number;
  retrieval_hits: number;
  fallback_triggered: boolean;
  fallback_reason?: string | null;
};

export type AvailabilitySlot = {
  start: string;
  end?: string | null;
  label: string;
};

export type BookingChatState = {
  active: boolean;
  stage:
    | "idle"
    | "awaiting_window"
    | "awaiting_slot_selection"
    | "awaiting_contact"
    | "confirmed";
  slots: AvailabilitySlot[];
  selected_slot?: AvailabilitySlot | null;
  booking_uid?: string | null;
  meeting_url?: string | null;
};

export type BookingResponse = {
  booking_uid: string;
  meeting_url?: string | null;
  start: string;
  end?: string | null;
  status: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function jsonRequest<T>(path: string, body: Record<string, unknown>) {
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body),
    cache: "no-store"
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "Request failed");
  }

  return (await response.json()) as T;
}

export function sendChatMessage(message: string, conversationId?: string) {
  return jsonRequest<ChatResponse>("/chat", {
    message,
    conversation_id: conversationId
  });
}

export function fetchAvailability(payload: {
  start: string;
  end: string;
  timezone?: string;
  max_results?: number;
}) {
  return jsonRequest<{ slots: AvailabilitySlot[] }>("/availability", payload);
}

export function bookSlot(payload: {
  start: string;
  attendee_name: string;
  attendee_email: string;
  attendee_timezone?: string;
  attendee_phone?: string;
  notes?: string;
}) {
  return jsonRequest<BookingResponse>("/book", payload);
}

export async function logClientEvent(
  eventType: string,
  details: Record<string, unknown> = {}
) {
  try {
    await jsonRequest("/events/client", {
      event_type: eventType,
      details
    });
  } catch {
    // Client event logging should never block the UI.
  }
}

export const VAPI_PUBLIC_KEY =
  process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY?.trim() ?? "";

export const VAPI_ASSISTANT_ID =
  process.env.NEXT_PUBLIC_VAPI_ASSISTANT_ID?.trim() ?? "";
