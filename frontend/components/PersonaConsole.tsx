"use client";

import { FormEvent, useState } from "react";

import { ChatResponse, sendChatMessage } from "@/lib/api";
import { useVapiVoice } from "@/hooks/useVapiVoice";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
};

function buildId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function PersonaConsole() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState(() => crypto.randomUUID());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const voice = useVapiVoice();

  async function handleSend(content?: string) {
    const message = (content ?? input).trim();
    if (!message || loading) {
      return;
    }

    setLoading(true);
    setError(null);
    setInput("");

    const userMessage: Message = {
      id: buildId("user"),
      role: "user",
      content: message
    };

    setMessages((current) => [...current, userMessage]);

    try {
      const response = await sendChatMessage(message, conversationId);
      setConversationId(response.conversation_id);
      const assistantMessage: Message = {
        id: buildId("assistant"),
        role: "assistant",
        content: response.answer,
        response
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (requestError) {
      const detail =
        requestError instanceof Error
          ? requestError.message
          : "Something went wrong while talking to the backend.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void handleSend();
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Grounded chat</p>
          <h2>Ask me about my resume, GitHub work, or projects</h2>
        </div>
        <div className="status-stack">
          <span className={`status-pill ${loading ? "busy" : ""}`}>
            {loading ? "Thinking..." : "Ready"}
          </span>
          <span
            className={`status-pill ${voice.active || voice.connecting ? "busy" : ""}`}
          >
            {voice.active
              ? voice.speaking
                ? "Voice speaking"
                : "Voice live"
              : voice.connecting
                ? "Connecting voice"
                : voice.ready
                  ? "Voice ready"
                  : "Voice setup needed"}
          </span>
        </div>
      </div>

      <div className="conversation">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Try prompts like:</p>
            <ul>
              <li>Tell me about your DeepChem contributions.</li>
              <li>What did you build during your internship at Spenza?</li>
              <li>Explain LRU eviction in simple terms.</li>
              <li>Book a meeting with me next week.</li>
            </ul>
          </div>
        ) : null}

        {messages.map((message) => (
          <article
            key={message.id}
            className={`message-card ${message.role === "assistant" ? "assistant" : "user"}`}
          >
            <div className="message-meta">
              <span>{message.role === "assistant" ? "Ashwin" : "You"}</span>
              {message.response ? (
                <span>
                  {message.response.answer_mode === "general"
                    ? "General tech mode"
                    : message.response.answer_mode === "booking"
                      ? "Booking flow"
                      : `${message.response.latency_ms} ms`}
                </span>
              ) : null}
            </div>
            <p>{message.content}</p>
            {message.response?.booking?.slots.length ? (
              <div className="slot-list booking-slot-list">
                {message.response.booking.slots.map((slot, index) => (
                  <button
                    key={slot.start}
                    type="button"
                    className="slot-chip"
                    onClick={() => {
                      void handleSend(String(index + 1));
                    }}
                  >
                    {index + 1}. {slot.label}
                  </button>
                ))}
              </div>
            ) : null}
            {message.response?.booking?.meeting_url ? (
              <div className="success-card compact-success">
                <strong>Booking confirmed</strong>
                <a
                  href={message.response.booking.meeting_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open meeting link
                </a>
              </div>
            ) : null}
            {message.response?.sources.length ? (
              <div className="source-list">
                {message.response.sources.map((source) => (
                  <div className="source-chip source-card" key={source.id}>
                    <div className="source-card-main">
                      <strong>{source.source_title}</strong>
                      <span>
                        {source.source_type} · {source.score.toFixed(3)}
                      </span>
                    </div>
                    {source.url ? (
                      <a href={source.url} target="_blank" rel="noreferrer">
                        Open source
                      </a>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <form className="composer" onSubmit={onSubmit}>
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type a question for Ashwin..."
          rows={4}
        />
        <div className="composer-actions">
          <button type="submit" disabled={loading}>
            Send
          </button>
          {voice.supported ? (
            <button
              type="button"
              className="secondary"
              onClick={voice.active ? () => void voice.stopCall() : () => void voice.startCall()}
              disabled={voice.connecting}
            >
              {voice.active ? "End voice call" : voice.connecting ? "Connecting..." : "Start voice call"}
            </button>
          ) : (
            <button type="button" className="secondary" disabled>
              Voice unavailable
            </button>
          )}
        </div>
      </form>

      {error ? <p className="error-text">{error}</p> : null}
      {voice.error ? <p className="error-text">{voice.error}</p> : null}
    </section>
  );
}
