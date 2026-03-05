import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "CloneAI Pro — Your Face. Your Voice. Any Language. Free Forever.",
  description:
    "Build AI avatar videos for free. Clone your voice in 30 seconds. Generate talking face videos in any language. No watermark. Open source.",
  keywords: [
    "AI voice clone",
    "talking avatar",
    "HeyGen alternative",
    "free AI video",
    "voice cloning",
    "face animation",
    "open source AI",
  ],
  openGraph: {
    title: "CloneAI Pro — Free AI Avatar Video Generator",
    description: "Your face. Your voice. Any language. Any script. Free forever.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrains.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
