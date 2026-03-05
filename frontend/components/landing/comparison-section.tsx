"use client";

import { motion } from "framer-motion";
import { Check, X } from "lucide-react";

const rows = [
  { feature: "Price", heygen: "$29/mo", eleven: "$22/mo", synthesia: "$22/mo", us: "FREE FOREVER", usWin: true },
  { feature: "Voice sample needed", heygen: "5 minutes", eleven: "1 minute", synthesia: "Recording session", us: "30 SECONDS", usWin: true },
  { feature: "Watermark on free tier", heygen: "Yes", eleven: "Yes", synthesia: "Yes", us: "Never", usWin: true },
  { feature: "Self-hosted / Private", heygen: "No", eleven: "No", synthesia: "No", us: "Yes — 100%", usWin: true },
  { feature: "Open source", heygen: "No", eleven: "No", synthesia: "No", us: "MIT License", usWin: true },
  { feature: "Indian languages", heygen: "Limited", eleven: "Limited", synthesia: "Limited", us: "Full support", usWin: true },
  { feature: "API access", heygen: "Enterprise $$$", eleven: "Paid tiers", synthesia: "Enterprise only", us: "Free", usWin: true },
  { feature: "One-command deploy", heygen: "No", eleven: "No", synthesia: "No", us: "Docker Compose", usWin: true },
];

export function ComparisonSection() {
  return (
    <section className="py-24 px-4 border-t border-border">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-3">
            Honest Comparison
          </p>
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
            Why Switch to CloneAI Pro
          </h2>
          <p className="text-muted-foreground">
            Everything they charge for — we give you free.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="overflow-x-auto"
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-4 px-4 text-muted-foreground font-normal text-xs uppercase tracking-widest">
                  Feature
                </th>
                <th className="text-center py-4 px-4 text-muted-foreground font-normal text-xs uppercase tracking-widest">
                  HeyGen
                </th>
                <th className="text-center py-4 px-4 text-muted-foreground font-normal text-xs uppercase tracking-widest">
                  ElevenLabs
                </th>
                <th className="text-center py-4 px-4 text-muted-foreground font-normal text-xs uppercase tracking-widest">
                  Synthesia
                </th>
                <th className="text-center py-4 px-4 text-primary font-bold text-xs uppercase tracking-widest">
                  CloneAI Pro
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.feature} className="border-b border-border/50 hover:bg-primary/[0.02] transition">
                  <td className="py-4 px-4 font-medium">{row.feature}</td>
                  <td className="py-4 px-4 text-center text-red-400">{row.heygen}</td>
                  <td className="py-4 px-4 text-center text-red-400">{row.eleven}</td>
                  <td className="py-4 px-4 text-center text-red-400">{row.synthesia}</td>
                  <td className="py-4 px-4 text-center">
                    <span className="text-green-400 font-bold">{row.us}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      </div>
    </section>
  );
}
