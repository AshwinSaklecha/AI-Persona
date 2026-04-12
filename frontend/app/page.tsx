import { BookingPanel } from "@/components/BookingPanel";
import { PersonaConsole } from "@/components/PersonaConsole";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Ashwin Saklecha</p>
          <h1>Production-ready AI persona scaffold</h1>
          <p className="hero-text">
            This UI talks to a FastAPI backend with Gemini, FAISS-backed retrieval,
            browser voice controls, and Cal.com availability.
          </p>
        </div>
      </section>

      <section className="grid-layout">
        <PersonaConsole />
        <BookingPanel />
      </section>
    </main>
  );
}

