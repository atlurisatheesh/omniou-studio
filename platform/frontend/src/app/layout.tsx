import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ominou Studio — One Studio. Every Creative Tool.",
  description:
    "All-in-one AI creative platform: voice synthesis, code generation, graphic design, video production, writing, and music — all in one place.",
  keywords: "AI, creative tools, voice synthesis, code generation, graphic design, video production",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  );
}
