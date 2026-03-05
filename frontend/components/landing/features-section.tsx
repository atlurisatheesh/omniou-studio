"use client";

import { motion } from "framer-motion";
import {
  Mic,
  Camera,
  Globe,
  Shield,
  Zap,
  Download,
  Code,
  Server,
} from "lucide-react";

const features = [
  {
    icon: Mic,
    title: "30-Second Voice Clone",
    description:
      "Upload just 30 seconds of your voice. Our XTTS v2 engine creates a perfect clone with your accent, tone, and emotion.",
    color: "text-cyan-400",
  },
  {
    icon: Camera,
    title: "Photo to Talking Avatar",
    description:
      "One photo is all it takes. MuseTalk generates photorealistic face animations with natural head movement and lip sync.",
    color: "text-blue-400",
  },
  {
    icon: Globe,
    title: "50+ Languages",
    description:
      "Hindi, Tamil, Telugu, Spanish, French, Arabic, Chinese, Japanese — your clone speaks any language fluently.",
    color: "text-green-400",
  },
  {
    icon: Download,
    title: "No Watermark. Ever.",
    description:
      "Download 1080p MP4 videos with zero watermarks. Not on free. Not on paid. Never. Your content is yours.",
    color: "text-yellow-400",
  },
  {
    icon: Shield,
    title: "100% Private & Self-Hosted",
    description:
      "Your face and voice data never leave your server. Self-host on any GPU machine. Full control, full privacy.",
    color: "text-red-400",
  },
  {
    icon: Code,
    title: "Open Source (MIT)",
    description:
      "Fork it. Modify it. Build on top of it. MIT license means you own it forever. No vendor lock-in.",
    color: "text-purple-400",
  },
  {
    icon: Zap,
    title: "Real-Time Progress",
    description:
      "Watch your video generate in real-time via WebSocket. Voice → Face → Lip Sync → Enhanced → Done.",
    color: "text-orange-400",
  },
  {
    icon: Server,
    title: "One-Command Deploy",
    description:
      "docker-compose up. That's it. Full stack: Next.js + FastAPI + Redis + PostgreSQL — ready in 60 seconds.",
    color: "text-pink-400",
  },
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-3">
            Everything You Need
          </p>
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
            Built for Creators.
            <br />
            <span className="text-muted-foreground">Powered by AI.</span>
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Every feature HeyGen charges $29/month for — free, open source, and self-hosted.
          </p>
        </div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.2 }}
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {features.map((f) => (
            <motion.div
              key={f.title}
              variants={item}
              className="group p-6 bg-card border border-border rounded-xl hover:border-primary/30 transition-all hover:bg-primary/[0.02]"
            >
              <f.icon className={`w-8 h-8 ${f.color} mb-4`} />
              <h3 className="font-bold text-foreground mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {f.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
