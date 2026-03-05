"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Video,
  Mic,
  Camera,
  LayoutDashboard,
  Settings,
  CreditCard,
  LogOut,
  Check,
  Sparkles,
  Zap,
  Crown,
  ArrowRight,
  Clock,
  Download,
} from "lucide-react";

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "/forever",
    description: "For personal experiments",
    features: [
      "5 videos per month",
      "720p resolution",
      "30 second max duration",
      "Community support",
      "CloneAI watermark",
    ],
    icon: Sparkles,
    current: true,
  },
  {
    name: "Pro",
    price: "$0",
    period: "/forever",
    description: "Everything, no limits",
    features: [
      "Unlimited videos",
      "1080p resolution",
      "No duration limit",
      "Priority processing",
      "No watermark",
      "API access",
      "Priority support",
    ],
    icon: Crown,
    current: false,
    highlight: true,
    badge: "Open Source — Always Free",
  },
];

interface UsageItem {
  label: string;
  used: number;
  limit: number | "unlimited";
}

const USAGE: UsageItem[] = [
  { label: "Videos This Month", used: 3, limit: "unlimited" },
  { label: "Storage Used", used: 245, limit: 5000 },
  { label: "Voice Clones", used: 2, limit: "unlimited" },
  { label: "Avatars", used: 3, limit: "unlimited" },
];

export default function BillingPage() {
  const [selectedPlan] = useState("Free");

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card p-6 sticky top-0 h-screen">
        <Link href="/" className="flex items-center gap-2 mb-10">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-cyan-400 flex items-center justify-center">
            <Video className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-lg">CloneAI Pro</span>
        </Link>
        <nav className="flex-1 space-y-1">
          {[
            { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard", active: false },
            { icon: Plus, label: "Create Clone", href: "/dashboard/create", active: false },
            { icon: Mic, label: "Voice Library", href: "/dashboard/voice-library", active: false },
            { icon: Camera, label: "Avatars", href: "/dashboard/avatars", active: false },
            { icon: Settings, label: "Settings", href: "/dashboard/settings", active: false },
            { icon: CreditCard, label: "Billing", href: "/dashboard/billing", active: true },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
                item.active
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          ))}
        </nav>
        <button className="flex items-center gap-3 px-3 py-2.5 text-sm text-muted-foreground hover:text-foreground transition mt-auto">
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-6 md:p-10 max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold">Billing & Plans</h1>
          <p className="text-muted-foreground text-sm mt-1">
            CloneAI Pro is <span className="text-primary font-semibold">100% free and open source</span>. No hidden fees, ever.
          </p>
        </div>

        {/* Plans */}
        <div className="grid md:grid-cols-2 gap-4 mb-10">
          {PLANS.map((plan) => {
            const PlanIcon = plan.icon;
            return (
              <div
                key={plan.name}
                className={`bg-card border rounded-xl p-6 relative ${
                  plan.highlight
                    ? "border-primary shadow-lg shadow-primary/10"
                    : "border-border"
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-primary-foreground text-xs font-bold rounded-full">
                    {plan.badge}
                  </div>
                )}

                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      plan.highlight
                        ? "bg-primary/20 text-primary"
                        : "bg-secondary text-muted-foreground"
                    }`}
                  >
                    <PlanIcon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold">{plan.name}</h3>
                    <p className="text-xs text-muted-foreground">{plan.description}</p>
                  </div>
                </div>

                <div className="mb-6">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground text-sm">{plan.period}</span>
                </div>

                <ul className="space-y-2.5 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm">
                      <Check className={`w-4 h-4 ${plan.highlight ? "text-primary" : "text-green-400"}`} />
                      {feature}
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full py-2.5 rounded-xl text-sm font-semibold transition ${
                    plan.current
                      ? "bg-secondary text-muted-foreground cursor-default"
                      : plan.highlight
                      ? "bg-primary text-primary-foreground hover:bg-primary/90"
                      : "bg-secondary text-foreground hover:bg-secondary/80"
                  }`}
                  disabled={plan.current}
                >
                  {plan.current ? "Current Plan" : "Self-Host for Free →"}
                </button>
              </div>
            );
          })}
        </div>

        {/* Usage */}
        <section className="bg-card border border-border rounded-xl p-6 mb-8">
          <h2 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4 text-primary" />
            Current Usage
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {USAGE.map((item) => (
              <div key={item.label} className="space-y-2">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="text-xl font-bold">
                  {item.used}
                  <span className="text-sm text-muted-foreground font-normal">
                    {" / "}
                    {item.limit === "unlimited" ? "∞" : item.limit}
                    {item.label.includes("Storage") ? " MB" : ""}
                  </span>
                </p>
                {item.limit !== "unlimited" && (
                  <div className="h-1.5 bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{
                        width: `${Math.min((item.used / (item.limit as number)) * 100, 100)}%`,
                      }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Open Source Banner */}
        <section className="bg-gradient-to-r from-primary/10 to-cyan-400/10 border border-primary/20 rounded-xl p-6 text-center">
          <h3 className="text-lg font-bold mb-2">
            Why is CloneAI Pro Free?
          </h3>
          <p className="text-sm text-muted-foreground max-w-xl mx-auto mb-4">
            We believe AI tools for content creation should be accessible to everyone.
            CloneAI Pro is 100% open source — you can self-host, modify, and contribute.
            No subscriptions, no hidden costs.
          </p>
          <div className="flex items-center justify-center gap-3">
            <a
              href="https://github.com/cloneai-pro/cloneai-pro"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-xl font-semibold text-sm hover:bg-primary/90 transition"
            >
              View on GitHub
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}
