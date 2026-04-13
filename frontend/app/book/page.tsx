import { BookingPanel } from "@/components/BookingPanel";

export default function BookPage() {
  return (
    <main className="page-stack">
      <section className="page-hero page-hero-compact">
        <p className="eyebrow">Book</p>
        <h1>Pick a time without the chat flow.</h1>
        <p className="hero-copy">
          This page is for the direct route: check live availability, choose a slot, and
          confirm the meeting manually.
        </p>
      </section>

      <BookingPanel />
    </main>
  );
}
