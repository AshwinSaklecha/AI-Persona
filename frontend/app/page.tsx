import Link from "next/link";

export default function HomePage() {
  return (
    <main className="page-stack">
      <section className="page-hero">
        <p className="eyebrow">About</p>
        <h1>A grounded AI version of Ashwin for chat and booking.</h1>
        <p className="hero-copy">
          This persona is built around real resume data, selected GitHub work,
          contribution history, and live availability. The website is focused on text
          chat and scheduling, while the phone-call flow lives separately.
        </p>
        <div className="hero-actions">
          <Link href="/chat" className="button-link">
            Open chat
          </Link>
          <Link href="/book" className="button-link secondary-link">
            Book manually
          </Link>
        </div>
      </section>

      <section className="feature-grid">
        <article className="feature-card">
          <p className="eyebrow">What it does</p>
          <h2>One persona, two actions on the web.</h2>
          <p>
            Use the chat page for grounded answers and the booking page when you want a
            direct calendar flow without conversation.
          </p>
        </article>

        <article className="feature-card">
          <p className="eyebrow">How it stays honest</p>
          <h2>RAG first, guesses last.</h2>
          <p>
            Answers are grounded against resume data, curated GitHub repositories, and
            selected contribution PRs. When the context is weak, the persona is meant to
            say it does not know instead of bluffing.
          </p>
        </article>

        <article className="feature-card">
          <p className="eyebrow">Current sources</p>
          <h2>Focused on the work that matters.</h2>
          <p>
            Indexed sources include Ashwin&apos;s resume, <code>kv-cache</code>,
            <code> expenseTracker</code>, <code>eCommerce-App</code>,
            <code> smart-doc-generator</code>, DeepChem contributions, and the Gemini
            CLI contribution under review.
          </p>
        </article>
      </section>
    </main>
  );
}
