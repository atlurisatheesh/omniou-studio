"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function CTASection() {
  return (
    <section className="py-24 px-4 border-t border-border relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-t from-primary/5 to-transparent pointer-events-none" />
      <div className="max-w-3xl mx-auto text-center relative z-10">
        <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-6">
          Ready to Clone
          <br />
          <span className="gradient-text">Yourself?</span>
        </h2>
        <p className="text-lg text-muted-foreground mb-10 max-w-xl mx-auto">
          Join thousands of creators who use CloneAI Pro to make videos in minutes,
          not hours. No credit card. No watermark. No catch.
        </p>
        <Link
          href="/dashboard/create"
          className="group inline-flex items-center gap-2 px-10 py-5 bg-primary text-primary-foreground font-bold text-lg rounded-xl hover:bg-primary/90 transition-all glow-blue"
        >
          Start Creating — It&apos;s Free
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </Link>
      </div>
    </section>
  );
}
