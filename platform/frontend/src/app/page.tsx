import Link from "next/link";

const features = [
  { icon: "🎬", name: "Film Studio", desc: "Script-to-video pipeline with AI crew — Director, DOP, VFX, Music. Full cinematic production.", gradient: "from-indigo-500 to-blue-500" },
  { icon: "🧬", name: "Clone Lab", desc: "Voice cloning from 10s of audio. Face swap in any video. Create your digital twin.", gradient: "from-purple-500 to-pink-500" },
  { icon: "🎙️", name: "Voice Studio", desc: "Ultra-realistic text-to-speech, voice cloning, dubbing in 20+ languages.", gradient: "from-emerald-500 to-teal-500" },
  { icon: "🎨", name: "Design Studio", desc: "AI image generation, background removal, upscaling — 50+ templates.", gradient: "from-amber-500 to-orange-500" },
  { icon: "💻", name: "Code Studio", desc: "AI code generation in 20+ languages, browser IDE, one-click deploy.", gradient: "from-cyan-500 to-blue-500" },
  { icon: "🎵", name: "Music Studio", desc: "AI-generated music, jingles, sound effects across 18 genres.", gradient: "from-rose-500 to-red-500" },
];

const crewRoles = [
  { icon: "🎬", name: "Director", desc: "Creative vision & pacing" },
  { icon: "📷", name: "DOP", desc: "Camera, lighting & composition" },
  { icon: "✍️", name: "Scriptwriter", desc: "Dialogue & narrative" },
  { icon: "🎵", name: "Music Director", desc: "Score & audio design" },
  { icon: "🎨", name: "Designer", desc: "Titles & motion graphics" },
  { icon: "✨", name: "VFX Artist", desc: "Visual effects" },
  { icon: "💃", name: "Choreographer", desc: "Movement & transitions" },
];

const plans = [
  { name: "Free", price: "$0", period: "", credits: "50 credits/mo", cta: "Get Started", features: ["Basic studios", "720p exports", "Community support"] },
  { name: "Pro", price: "$29", period: "/mo", credits: "2,000 credits/mo", cta: "Start Pro Trial", popular: true, features: ["All studios + Film Studio", "4K exports", "AI Crew", "API access", "Priority support"] },
  { name: "Team", price: "$79", period: "/seat/mo", credits: "10,000 credits/mo", cta: "Start Team Trial", features: ["5 team seats", "Custom AI models", "Workflow automation", "Dedicated support"] },
  { name: "Enterprise", price: "Custom", period: "", credits: "Unlimited", cta: "Contact Sales", features: ["Unlimited seats", "On-premise", "Custom integrations", "SLA guarantee"] },
];

const stats = [
  { value: "7", label: "AI Studios" },
  { value: "7", label: "AI Crew Members" },
  { value: "10 min", label: "Max Video Length" },
  { value: "4K+", label: "Max Resolution" },
];

const videoCapabilities = [
  { label: "Duration", items: ["1 min", "2 min", "3 min", "5 min", "10 min", "Custom"] },
  { label: "Quality", items: ["1080p", "2K", "4K"] },
  { label: "Styles", items: ["3D", "Cinematic", "2D Animation", "Documentary"] },
  { label: "Aspect Ratio", items: ["16:9", "9:16", "1:1", "4:3"] },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen relative z-10 text-white">
      {/* Nav */}
      <nav className="border-b border-[#1e1e30]/50 glass-strong sticky top-0 z-50">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 via-purple-500 to-pink-500 flex items-center justify-center font-bold text-white text-xs shadow-lg shadow-brand-500/20">O</div>
            <span className="text-lg font-bold gradient-text tracking-tight">Ominou Studio</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-surface-200">
            <a href="#features" className="hover:text-white transition">Features</a>
            <a href="#crew" className="hover:text-white transition">AI Crew</a>
            <a href="#pricing" className="hover:text-white transition">Pricing</a>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="px-4 py-2 text-sm text-surface-200 hover:text-white transition">Sign In</Link>
            <Link href="/register" className="px-5 py-2 rounded-lg bg-gradient-to-r from-brand-500 to-purple-500 text-white text-sm font-semibold hover:from-brand-600 hover:to-purple-600 transition shadow-lg shadow-brand-500/20">
              Get Started Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden perspective-container">
        {/* 3D Floating Orbs */}
        <div className="absolute top-10 left-[10%] w-72 h-72 rounded-full bg-brand-500/15 blur-[80px] orb-float pointer-events-none" />
        <div className="absolute top-32 right-[15%] w-60 h-60 rounded-full bg-purple-500/12 blur-[70px] orb-float-2 pointer-events-none" />
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-[500px] h-40 bg-pink-500/8 rounded-full blur-[90px] hero-glow pointer-events-none" />

        {/* 3D Decorative shapes */}
        <div className="absolute top-24 left-[8%] w-16 h-16 rounded-2xl border border-brand-500/20 bg-brand-500/5 backdrop-blur-sm float-3d pointer-events-none hidden lg:block" />
        <div className="absolute top-44 right-[10%] w-20 h-20 rounded-full border border-purple-500/20 bg-purple-500/5 backdrop-blur-sm float-3d-reverse pointer-events-none hidden lg:block" />
        <div className="absolute bottom-32 left-[15%] w-14 h-14 rounded-xl border border-pink-500/15 bg-pink-500/5 backdrop-blur-sm float-3d-slow pointer-events-none hidden lg:block" />
        <div className="absolute top-60 left-[45%] w-10 h-10 rounded-lg border border-cyan-500/15 bg-cyan-500/5 backdrop-blur-sm float-3d pointer-events-none hidden lg:block" />
        <div className="absolute bottom-48 right-[20%] w-12 h-12 rounded-2xl border border-amber-500/15 bg-amber-500/5 backdrop-blur-sm float-3d-reverse pointer-events-none hidden lg:block" />

        <div className="max-w-5xl mx-auto text-center px-6 pt-24 pb-20 md:pt-32 md:pb-28 relative">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-sm font-medium mb-8 float-3d-slow">
            <span className="w-2 h-2 bg-accent-green rounded-full animate-pulse" />
            <span className="text-surface-100">AI Film Production Platform — Script to Screen</span>
          </div>

          <h2 className="text-5xl md:text-7xl font-extrabold leading-[1.1] tracking-tight">
            Your AI{" "}
            <span className="gradient-text">Production</span>
            <br />
            <span className="gradient-text">Crew</span> is Ready
          </h2>

          <p className="text-lg md:text-xl text-surface-200 mt-6 max-w-2xl mx-auto leading-relaxed">
            7 AI specialists — Director, DOP, VFX, Music Director, and more — working in parallel to transform your script into a cinematic masterpiece.
          </p>

          <div className="flex items-center justify-center gap-4 mt-10">
            <Link href="/register"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500 hover:from-brand-600 hover:via-purple-600 hover:to-pink-600 text-white font-bold text-lg transition shadow-2xl shadow-brand-500/25">
              Start Directing — Free
            </Link>
            <a href="#features" className="px-8 py-4 rounded-xl glass text-surface-100 hover:text-white transition text-lg font-medium">
              See How It Works
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-8 mt-20 max-w-xl mx-auto">
            {stats.map(s => (
              <div key={s.label} className="text-center">
                <p className="text-3xl font-extrabold gradient-text">{s.value}</p>
                <p className="text-xs text-surface-300 mt-1 font-medium">{s.label}</p>
              </div>
            ))}
          </div>

          {/* 3D Video Capabilities Showcase */}
          <div className="mt-20 perspective-container">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
              {videoCapabilities.map((cap, i) => (
                <div key={cap.label} className={`glass rounded-xl p-4 card-3d ${i % 2 === 0 ? "float-3d-slow" : ""}`}>
                  <h4 className="text-xs font-semibold text-brand-400 mb-2">{cap.label}</h4>
                  <div className="space-y-1">
                    {cap.items.map(item => (
                      <span key={item} className="block text-[11px] text-surface-200">{item}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* AI Crew */}
      <section id="crew" className="py-20 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-500/[0.02] to-transparent pointer-events-none" />
        <div className="max-w-6xl mx-auto px-6 relative">
          <div className="text-center mb-14">
            <h3 className="text-3xl md:text-4xl font-bold tracking-tight">
              Meet Your <span className="gradient-text">AI Crew</span>
            </h3>
            <p className="text-surface-200 mt-3 max-w-xl mx-auto">
              7 specialized AI agents collaborate on every production — from script analysis to final cut
            </p>
          </div>

          {/* 3D Pipeline visualization */}
          <div className="flex items-center justify-center gap-3 flex-wrap mb-12 perspective-container">
            {crewRoles.map((r, i) => (
              <div key={r.name} className="flex items-center gap-3">
                <div className={`glass rounded-xl px-5 py-3 card-3d text-center ${i % 2 === 0 ? "float-3d-slow" : ""}`}>
                  <span className="text-2xl block">{r.icon}</span>
                  <span className="text-xs font-semibold text-white block mt-1">{r.name}</span>
                  <span className="text-[10px] text-surface-300">{r.desc}</span>
                </div>
                {i < crewRoles.length - 1 && (
                  <span className="text-brand-400/50 text-lg hidden sm:inline">→</span>
                )}
              </div>
            ))}
          </div>

          {/* Workflow demo */}
          <div className="glass rounded-2xl p-8 max-w-3xl mx-auto card-3d">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center text-xl flex-shrink-0 float-3d-slow">🎬</div>
              <div>
                <h4 className="text-sm font-semibold text-white mb-2">How it works</h4>
                <div className="space-y-3">
                  {[
                    { step: "1", text: "Paste your script or describe your vision in the chat" },
                    { step: "2", text: "Choose duration, style (3D / Cinematic / 2D), quality & aspect ratio" },
                    { step: "3", text: "AI Scriptwriter analyzes & breaks it into scenes" },
                    { step: "4", text: "DOP plans camera angles, Director sets the pacing" },
                    { step: "5", text: "Video AI generates each scene with character consistency" },
                    { step: "6", text: "Music Director adds score, VFX adds effects, final export" },
                  ].map(s => (
                    <div key={s.step} className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-brand-500/15 text-brand-400 text-xs font-bold flex items-center justify-center flex-shrink-0">{s.step}</span>
                      <span className="text-sm text-surface-200">{s.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-20 perspective-container">
        <div className="text-center mb-14">
          <h3 className="text-3xl md:text-4xl font-bold tracking-tight">Seven Studios, <span className="gradient-text">Infinite Possibilities</span></h3>
          <p className="text-surface-200 mt-3">Every creative tool you need, powered by cutting-edge AI</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <div key={f.name} className="glass rounded-xl p-6 card-3d slide-up" style={{ animationDelay: `${i * 80}ms` }}>
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.gradient} flex items-center justify-center text-2xl float-3d-slow`}>
                {f.icon}
              </div>
              <h4 className="text-lg font-semibold text-white mt-4">{f.name}</h4>
              <p className="text-sm text-surface-200 mt-2 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="max-w-6xl mx-auto px-6 py-20 perspective-container">
        <div className="text-center mb-14">
          <h3 className="text-3xl md:text-4xl font-bold tracking-tight">Simple, <span className="gradient-text">Transparent</span> Pricing</h3>
          <p className="text-surface-200 mt-3">Start free, scale as you grow</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {plans.map((plan, i) => (
            <div key={plan.name}
              className={`glass rounded-xl p-6 card-3d ${plan.popular ? "border border-brand-500/40 shadow-lg shadow-brand-500/10 scale-[1.03]" : ""} ${i % 2 === 0 ? "float-3d-slow" : ""}`}>
              {plan.popular && <p className="text-xs text-brand-400 font-semibold mb-2">Most Popular</p>}
              <h4 className="text-xl font-bold text-white">{plan.name}</h4>
              <p className="mt-2">
                <span className="text-3xl font-extrabold text-white">{plan.price}</span>
                <span className="text-surface-300 text-sm">{plan.period}</span>
              </p>
              <p className="text-sm text-surface-300 mt-1">{plan.credits}</p>
              <ul className="mt-5 space-y-2.5">
                {plan.features.map((f, fi) => (
                  <li key={fi} className="text-sm text-surface-200 flex items-center gap-2">
                    <span className="text-accent-green text-xs">✓</span> {f}
                  </li>
                ))}
              </ul>
              <Link href="/register"
                className={`block w-full text-center mt-6 py-2.5 rounded-lg text-sm font-semibold transition ${
                  plan.popular ? "bg-gradient-to-r from-brand-500 to-purple-500 text-white hover:from-brand-600 hover:to-purple-600 shadow-lg shadow-brand-500/20" : "glass text-surface-200 hover:text-white"
                }`}>{plan.cta}</Link>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 relative perspective-container">
        <div className="absolute inset-0 bg-gradient-to-r from-brand-500/[0.06] via-purple-500/[0.04] to-pink-500/[0.06] pointer-events-none" />
        {/* 3D floating decorations */}
        <div className="absolute top-8 left-[20%] w-12 h-12 rounded-xl border border-brand-500/15 bg-brand-500/5 float-3d pointer-events-none hidden md:block" />
        <div className="absolute bottom-12 right-[25%] w-16 h-16 rounded-full border border-purple-500/15 bg-purple-500/5 float-3d-reverse pointer-events-none hidden md:block" />
        <div className="max-w-2xl mx-auto text-center px-6 relative">
          <h3 className="text-3xl md:text-4xl font-bold tracking-tight">
            Ready to <span className="gradient-text">Direct</span> with AI?
          </h3>
          <p className="text-surface-200 mt-4 text-lg">
            Your AI production crew is standing by. Give them a script and watch the magic.
          </p>
          <Link href="/register"
            className="inline-block mt-8 px-10 py-4 rounded-xl bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500 hover:from-brand-600 hover:via-purple-600 hover:to-pink-600 text-white font-bold text-lg transition shadow-2xl shadow-brand-500/25">
            Start Directing — Free →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#1e1e30]/50 py-10">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center font-bold text-white text-[10px]">O</div>
            <span className="text-sm text-surface-300">© 2025 Ominou Studio</span>
          </div>
          <div className="flex gap-6 text-sm text-surface-300">
            <a href="#" className="hover:text-white transition">Privacy</a>
            <a href="#" className="hover:text-white transition">Terms</a>
            <a href="#" className="hover:text-white transition">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
