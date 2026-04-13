import { PersonaConsole } from "@/components/PersonaConsole";

export default function ChatPage() {
  return (
    <main className="page-stack">
      <section className="page-hero page-hero-compact">
        <p className="eyebrow">Chat</p>
        <h1>Ask Ashwin directly.</h1>
        <p className="hero-copy">
          This is the main grounded conversation surface. You can type, start a voice
          call, ask about projects, or move straight into scheduling.
        </p>
      </section>

      <PersonaConsole />
    </main>
  );
}
