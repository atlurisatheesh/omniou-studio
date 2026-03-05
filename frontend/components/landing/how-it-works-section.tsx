"use client";

import { motion } from "framer-motion";
import { Upload, Mic, FileText, Play } from "lucide-react";

const steps = [
  {
    num: "01",
    icon: Upload,
    title: "Upload Your Photo",
    description: "Upload a clear front-facing photo. Just one photo — that's your avatar.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    num: "02",
    icon: Mic,
    title: "Record 30s of Voice",
    description: "Read a short script for 30 seconds. Our AI captures your unique voice signature.",
    color: "from-cyan-500 to-green-500",
  },
  {
    num: "03",
    icon: FileText,
    title: "Type Your Script",
    description: "Write what you want your clone to say. Any language. Any length. Hit generate.",
    color: "from-green-500 to-yellow-500",
  },
  {
    num: "04",
    icon: Play,
    title: "Download Your Video",
    description: "Watch your AI clone speak your words. Download 1080p MP4, zero watermark, free.",
    color: "from-yellow-500 to-orange-500",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 px-4 border-t border-border">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-3">
            Simple 4-Step Process
          </p>
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
            Photo → Voice → Script → Video
          </h2>
          <p className="text-muted-foreground">
            From upload to download in under 2 minutes.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
              className="relative"
            >
              {/* Connector line */}
              {i < steps.length - 1 && (
                <div className="hidden lg:block absolute top-12 left-full w-6 h-px bg-border z-0" />
              )}

              <div className="p-6 bg-card border border-border rounded-xl relative z-10">
                <div
                  className={`w-12 h-12 rounded-lg bg-gradient-to-br ${step.color} flex items-center justify-center mb-4`}
                >
                  <step.icon className="w-6 h-6 text-white" />
                </div>
                <div className="text-xs font-mono text-muted-foreground mb-2">
                  STEP {step.num}
                </div>
                <h3 className="font-bold text-lg mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
