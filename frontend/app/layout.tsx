import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ashwin Persona",
  description: "AI persona for Ashwin Saklecha with grounded chat, voice, and booking."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

