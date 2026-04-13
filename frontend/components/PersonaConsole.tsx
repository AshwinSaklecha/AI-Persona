"use client";

import { FormEvent, useState } from "react";

import { ChatResponse, sendChatMessage } from "@/lib/api";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
};

function getAnswerBadge(response: ChatResponse) {
  switch (response.answer_mode) {
    case "general":
      return "General";
    case "booking":
      return "Booking";
    default:
      return "Grounded";
  }
}

function buildId(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export function PersonaConsole() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState(() => crypto.randomUUID());
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <section className="panel panel-wide">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Main chat</p>
          <h2>Ask about resume, repositories, contributions, or availability.</h2>
          <p className="panel-copy">
            This is the public chat interface for the persona. Use it for grounded
            questions or to start the booking flow.
          </p>
        </div>
      </div>

      <div className="conversation">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Try prompts like:</p>
            <ul>
              <li>Walk me through the design of kv-cache.</li>
              <li>What tradeoffs did you make in expenseTracker?</li>
              <li>What changed in your Gemini CLI contribution?</li>
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
                  {getAnswerBadge(message.response)} · {message.response.latency_ms} ms
                </span>
              ) : null}
            </div>
            <p>{message.content}</p>
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
          </article>
        ))}
      </div>

      <form className="composer" onSubmit={onSubmit}>
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask a question or start a booking flow..."
          rows={4}
        />
        <div className="composer-actions">
          <button type="submit" disabled={loading}>
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>
      </form>

      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
