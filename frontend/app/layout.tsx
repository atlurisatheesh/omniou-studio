import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgriSense — Agricultural Intelligence Platform",
  description:
    "AI-powered crop disease detection, soil analysis, weather forecasting, crop calendar, market prices & farmer community",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
