import Link from "next/link";

const features = [
  { icon: "🎤", name: "Voice Studio", desc: "Text-to-speech, voice cloning, dubbing in 20+ languages with ultra-realistic AI voices." },
  { icon: "🎨", name: "Design Studio", desc: "Generate stunning images, remove backgrounds, upscale, and create from 50+ templates." },
  { icon: "💻", name: "Code Studio", desc: "AI code generation in 20+ languages, browser IDE, project scaffolding, one-click deploy." },
  { icon: "🎬", name: "Video Studio", desc: "AI video generation, face swap, editing, and 4K upscaling powered by deep learning." },
  { icon: "✍️", name: "AI Writer", desc: "Blog posts, ad copy, emails, SEO content — 10 content types, 8 tones, instant generation." },
  { icon: "🎵", name: "Music Studio", desc: "Generate music, jingles, sound effects, and remixes across 18 genres and 16 moods." },
];

const plans = [
  { name: "Free", price: "$0", period: "", credits: "50 credits/mo", cta: "Get Started", features: ["Basic voice & text", "720p exports", "Community support"] },
  { name: "Pro", price: "$29", period: "/mo", credits: "2,000 credits/mo", cta: "Start Pro Trial", popular: true, features: ["All 6 studios", "4K exports", "API access", "Priority support"] },
  { name: "Team", price: "$79", period: "/seat/mo", credits: "10,000 credits/mo", cta: "Start Team Trial", features: ["5 team seats", "Custom models", "Workflow automation", "Dedicated support"] },
  { name: "Enterprise", price: "Custom", period: "", credits: "Unlimited", cta: "Contact Sales", features: ["Unlimited seats", "On-premise option", "Custom integrations", "SLA guarantee"] },
];

const stats = [
  { value: "6", label: "AI Studios" },
  { value: "20+", label: "Languages" },
  { value: "50+", label: "Templates" },
  { value: "99.9%", label: "Uptime" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Nav */}
      <nav className="border-b border-[#1a1a2e] bg-[#0a0a0f]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-brand-400 to-purple-400 bg-clip-text text-transparent">
            Ominou Studio
          </h1>
          <div className="hidden md:flex items-center gap-8 text-sm text-surface-400">
            <a href="#features" className="hover:text-white transition">Features</a>
            <a href="#pricing" className="hover:text-white transition">Pricing</a>
            <a href="#workflow" className="hover:text-white transition">Workflows</a>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="px-4 py-2 text-sm text-surface-300 hover:text-white transition">
              Sign In
            </Link>
            <Link href="/register" className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition">
              Get Started Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-brand-600/10 via-transparent to-transparent" />
        <div className="max-w-4xl mx-auto text-center px-6 py-24 md:py-32 relative">
          <div className="inline-block px-4 py-1.5 rounded-full bg-brand-600/20 text-brand-400 text-sm font-medium mb-6">
            🚀 The all-in-one AI creative platform
          </div>
          <h2 className="text-4xl md:text-6xl font-bold leading-tight">
            Voice. Design. Code.{" "}
            <span className="bg-gradient-to-r from-brand-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Video. Write. Music.
            </span>
          </h2>
          <p className="text-lg text-surface-400 mt-6 max-w-2xl mx-auto">
            Six powerful AI studios, one unified platform. Create anything — from voice clones to full applications — 
            with automated workflows that chain tools together.
          </p>
          <div className="flex items-center justify-center gap-4 mt-8">
            <Link
              href="/register"
              className="px-8 py-3.5 rounded-lg bg-gradient-to-r from-brand-600 to-purple-600 hover:from-brand-700 hover:to-purple-700 text-white font-semibold text-lg transition"
            >
              Start Creating — Free
            </Link>
            <a href="#features" className="px-8 py-3.5 rounded-lg border border-[#2a2a4a] text-surface-300 hover:text-white hover:border-surface-400 transition text-lg">
              See Features
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-6 mt-16 max-w-lg mx-auto">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <p className="text-2xl font-bold text-white">{s.value}</p>
                <p className="text-xs text-surface-500">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h3 className="text-3xl font-bold">Six Studios, Infinite Possibilities</h3>
          <p className="text-surface-400 mt-2">Every creative tool you need, powered by cutting-edge AI</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div key={f.name} className="glass rounded-xl p-6 card-hover">
              <span className="text-4xl">{f.icon}</span>
              <h4 className="text-lg font-semibold text-white mt-4">{f.name}</h4>
              <p className="text-sm text-surface-400 mt-2 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Workflow */}
      <section id="workflow" className="bg-[#0d0d15] py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold">Automated Workflows</h3>
            <p className="text-surface-400 mt-2">Chain studios together into powerful AI pipelines</p>
          </div>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {["✍️ Write Script", "→", "🎤 Generate Voice", "→", "🎬 Create Video", "→", "🎵 Add Music", "→", "📢 Publish"].map(
              (step, i) =>
                step === "→" ? (
                  <span key={i} className="text-brand-500 text-xl">→</span>
                ) : (
                  <div key={i} className="px-5 py-3 rounded-lg glass text-sm font-medium text-white">
                    {step}
                  </div>
                )
            )}
          </div>
          <p className="text-center text-surface-500 text-sm mt-8">
            Build custom workflows or use pre-built templates. Automate your entire content pipeline.
          </p>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h3 className="text-3xl font-bold">Simple, Transparent Pricing</h3>
          <p className="text-surface-400 mt-2">Start free, scale as you grow</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`glass rounded-xl p-6 ${plan.popular ? "border border-brand-500/50 ring-1 ring-brand-500/20 scale-105" : ""}`}
            >
              {plan.popular && (
                <p className="text-xs text-brand-400 font-medium mb-2">Most Popular</p>
              )}
              <h4 className="text-xl font-bold text-white">{plan.name}</h4>
              <p className="mt-2">
                <span className="text-3xl font-bold text-white">{plan.price}</span>
                <span className="text-surface-400 text-sm">{plan.period}</span>
              </p>
              <p className="text-sm text-surface-500 mt-1">{plan.credits}</p>
              <ul className="mt-5 space-y-2.5">
                {plan.features.map((f, i) => (
                  <li key={i} className="text-sm text-surface-400 flex items-center gap-2">
                    <span className="text-green-400">✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                className={`block w-full text-center mt-6 py-2.5 rounded-lg text-sm font-medium transition ${
                  plan.popular
                    ? "bg-brand-600 text-white hover:bg-brand-700"
                    : "bg-[#1a1a2e] text-surface-300 hover:text-white"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-r from-brand-600/20 to-purple-600/20 py-20">
        <div className="max-w-2xl mx-auto text-center px-6">
          <h3 className="text-3xl font-bold">Ready to create with AI?</h3>
          <p className="text-surface-400 mt-3">
            Join thousands of creators using Ominou Studio to build amazing content.
          </p>
          <Link
            href="/register"
            className="inline-block mt-6 px-8 py-3.5 rounded-lg bg-gradient-to-r from-brand-600 to-purple-600 hover:from-brand-700 hover:to-purple-700 text-white font-semibold text-lg transition"
          >
            Get Started Free →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#1a1a2e] py-10">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
          <p className="text-sm text-surface-500">© 2025 Ominou Studio. All rights reserved.</p>
          <div className="flex gap-6 text-sm text-surface-500">
            <a href="#" className="hover:text-white transition">Privacy</a>
            <a href="#" className="hover:text-white transition">Terms</a>
            <a href="#" className="hover:text-white transition">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
