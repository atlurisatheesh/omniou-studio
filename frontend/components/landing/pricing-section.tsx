"use client";

import { motion } from "framer-motion";
import { Check, Sparkles } from "lucide-react";
import Link from "next/link";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Everything you need to get started",
    features: [
      "5 videos per month",
      "720p output",
      "No watermark",
      "17 languages",
      "30-second voice clone",
      "Self-hosted option",
      "Community support",
    ],
    cta: "Start Free",
    href: "/dashboard/create",
    featured: false,
  },
  {
    name: "Creator",
    price: "$9",
    period: "/month",
    description: "For content creators who need more",
    features: [
      "50 videos per month",
      "1080p output",
      "No watermark",
      "50+ languages",
      "API access",
      "Priority processing",
      "Email support",
      "Voice profile saving",
    ],
    cta: "Upgrade to Creator",
    href: "/dashboard/create",
    featured: true,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For agencies and power users",
    features: [
      "Unlimited videos",
      "4K output",
      "No watermark",
      "50+ languages",
      "Full API access",
      "Priority GPU queue",
      "Custom branding",
      "Dedicated support",
      "Team members",
    ],
    cta: "Go Pro",
    href: "/dashboard/create",
    featured: false,
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="py-24 px-4 border-t border-border">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16">
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-3">
            Simple Pricing
          </p>
          <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
            Free to Start.
            <br />
            <span className="text-muted-foreground">Scale When Ready.</span>
          </h2>
          <p className="text-muted-foreground max-w-lg mx-auto">
            Self-host for free forever. Or use our cloud for convenience.
            70% cheaper than HeyGen and ElevenLabs combined.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
              className={`relative p-8 rounded-2xl border ${
                plan.featured
                  ? "border-primary bg-primary/[0.03] glow-blue"
                  : "border-border bg-card"
              }`}
            >
              {plan.featured && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-primary text-primary-foreground text-xs font-bold rounded-full flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> Most Popular
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-lg font-bold mb-1">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold">{plan.price}</span>
                  <span className="text-muted-foreground text-sm">{plan.period}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">{plan.description}</p>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href={plan.href}
                className={`block w-full text-center py-3 rounded-lg font-semibold text-sm transition ${
                  plan.featured
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "border border-border text-foreground hover:bg-secondary"
                }`}
              >
                {plan.cta}
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
