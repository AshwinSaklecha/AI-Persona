import type { Metadata } from "next";

import { SiteHeader } from "@/components/SiteHeader";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Ashwin Persona",
    template: "%s | Ashwin Persona"
  },
  description: "Grounded AI persona for Ashwin Saklecha with chat, voice, and booking."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="app-frame">
          <SiteHeader />
          <div className="page-shell">{children}</div>
        </div>
      </body>
    </html>
  );
}
