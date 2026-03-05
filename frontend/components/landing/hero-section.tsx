"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Play, ArrowRight, Github, Zap } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-20 px-4 overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-5xl mx-auto text-center relative z-10">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 border border-primary/30 bg-primary/5 rounded-full text-xs tracking-widest uppercase text-primary mb-8"
        >
          <Zap className="w-3 h-3" />
          Open Source · MIT License · Free Forever
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-5xl sm:text-6xl lg:text-8xl font-extrabold tracking-tight leading-[0.9] mb-6"
        >
          <span className="gradient-text">Your Face.</span>
          <br />
          <span className="gradient-text">Your Voice.</span>
          <br />
          <span className="text-foreground">Any Language.</span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          Upload your photo and 30 seconds of your voice. Type any script in any of 50+ languages.
          Get a studio-quality talking avatar video.{" "}
          <span className="text-primary font-semibold">No watermark. No subscription. Free forever.</span>
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
        >
          <Link
            href="/dashboard/create"
            className="group flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground font-bold text-lg rounded-xl hover:bg-primary/90 transition-all glow-blue"
          >
            Start Creating — Free
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <a
            href="https://github.com/cloneai-pro/cloneai-pro"
            target="_blank"
            rel="noopener"
            className="flex items-center gap-2 px-8 py-4 border border-border text-foreground font-semibold text-lg rounded-xl hover:bg-secondary transition"
          >
            <Github className="w-5 h-5" />
            View on GitHub
          </a>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.7 }}
          className="flex flex-wrap items-center justify-center gap-8 sm:gap-16 text-center"
        >
          {[
            { value: "30s", label: "Voice Sample" },
            { value: "50+", label: "Languages" },
            { value: "$0", label: "Forever" },
            { value: "1080p", label: "No Watermark" },
          ].map((stat) => (
            <div key={stat.label}>
              <div className="text-3xl font-extrabold text-primary">{stat.value}</div>
              <div className="text-xs uppercase tracking-widest text-muted-foreground mt-1">
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
