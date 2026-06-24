"use client";
import Link from "next/link";

const modules = [
  {
    id: "video",
    name: "Film Studio",
    icon: "🎬",
    description: "Script-to-video pipeline with your AI production crew",
    color: "from-indigo-500 to-blue-500",
    href: "/dashboard/video-studio",
    stats: { label: "Videos Created", value: "5" },
    featured: true,
  },
  {
    id: "voice",
    name: "Voice Studio",
    icon: "🎙️",
    description: "Text-to-speech, voice cloning, multilingual dubbing",
    color: "from-emerald-500 to-teal-500",
    href: "/dashboard/voice-studio",
    stats: { label: "Voices Generated", value: "12" },
  },
  {
    id: "design",
    name: "Design Studio",
    icon: "🎨",
    description: "AI image generation, templates, background removal",
    color: "from-amber-500 to-orange-500",
    href: "/dashboard/design-studio",
    stats: { label: "Designs Created", value: "8" },
  },
  {
    id: "code",
    name: "Code Studio",
    icon: "💻",
    description: "AI code generation, browser IDE, one-click deploy",
    color: "from-cyan-500 to-blue-500",
    href: "/dashboard/code-studio",
    stats: { label: "Code Generated", value: "23" },
  },
  {
    id: "writer",
    name: "AI Writer",
    icon: "✍️",
    description: "Blog posts, ad copy, scripts, SEO content",
    color: "from-yellow-500 to-amber-500",
    href: "/dashboard/ai-writer",
    stats: { label: "Articles Written", value: "15" },
  },
  {
    id: "music",
    name: "Music Studio",
    icon: "🎵",
    description: "AI music, jingles, sound effects, remixes",
    color: "from-purple-500 to-pink-500",
    href: "/dashboard/music-studio",
    stats: { label: "Tracks Created", value: "3" },
  },
];

const crewPreview = [
  { icon: "🎬", name: "Director" },
  { icon: "📷", name: "DOP" },
  { icon: "✍️", name: "Scriptwriter" },
  { icon: "🎵", name: "Music Dir." },
  { icon: "🎨", name: "Designer" },
  { icon: "✨", name: "VFX" },
  { icon: "💃", name: "Choreo." },
];

const recentActivity = [
  { time: "2 min ago", action: "Generated voice narration", module: "Voice Studio", icon: "🎙️" },
  { time: "15 min ago", action: "Created Instagram post design", module: "Design Studio", icon: "🎨" },
  { time: "1 hour ago", action: "Wrote blog post about AI", module: "AI Writer", icon: "✍️" },
  { time: "3 hours ago", action: "Generated background music", module: "Music Studio", icon: "🎵" },
  { time: "Yesterday", action: "Deployed Next.js project", module: "Code Studio", icon: "💻" },
];

export default function DashboardPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-6 fade-in perspective-container">
      {/* Welcome */}
      <div className="relative">
        {/* 3D floating decorations */}
        <div className="absolute -top-4 right-8 w-14 h-14 rounded-2xl border border-brand-500/15 bg-brand-500/5 float-3d pointer-events-none hidden lg:block" />
        <div className="absolute top-2 right-32 w-10 h-10 rounded-full border border-purple-500/15 bg-purple-500/5 float-3d-reverse pointer-events-none hidden lg:block" />
        <h1 className="text-2xl font-bold tracking-tight">
          Welcome to <span className="gradient-text">Ominou Studio</span>
        </h1>
        <p className="text-surface-300 text-sm mt-1">Your AI production crew is standing by.</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Total Projects", value: "66", change: "+12 this week", color: "text-brand-400" },
          { label: "Credits Used", value: "23", change: "27 remaining", color: "text-accent-purple" },
          { label: "Time Saved", value: "48h", change: "this month", color: "text-accent-green" },
          { label: "Assets Created", value: "142", change: "+28 this week", color: "text-accent-cyan" },
        ].map(stat => (
          <div key={stat.label} className="glass rounded-xl p-4 card-3d">
            <div className={`text-2xl font-extrabold ${stat.color}`}>{stat.value}</div>
            <div className="text-xs text-surface-200 font-medium mt-0.5">{stat.label}</div>
            <div className="text-[11px] text-surface-300 mt-1">{stat.change}</div>
          </div>
        ))}
      </div>

      {/* AI Crew Bar */}
      <div className="glass rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-surface-200">Your AI Crew</span>
          <Link href="/dashboard/video-studio" className="text-[11px] text-brand-400 hover:text-brand-300 transition">
            Open Film Studio →
          </Link>
        </div>
        <div className="flex items-center gap-4">
          {crewPreview.map(c => (
            <div key={c.name} className="text-center flex-shrink-0">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500/20 to-purple-500/20 border border-surface-600 flex items-center justify-center text-lg">
                {c.icon}
              </div>
              <p className="text-[10px] text-surface-300 mt-1">{c.name}</p>
            </div>
          ))}
          <div className="flex-1 ml-2 hidden md:block">
            <p className="text-xs text-surface-300">7 AI specialists ready — Director, DOP, Scriptwriter, Music Director, Designer, VFX, Choreographer</p>
          </div>
        </div>
      </div>

      {/* Module Cards */}
      <div>
        <h2 className="text-lg font-semibold mb-3 text-surface-100">Studios</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {modules.map((mod, i) => (
            <Link key={mod.id} href={mod.href}
              className={`glass rounded-xl p-5 card-3d group slide-up ${mod.featured ? "md:col-span-2 lg:col-span-1 border border-brand-500/20" : ""}`}
              style={{ animationDelay: `${i * 60}ms` }}>
              <div className="flex items-start justify-between mb-3">
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${mod.color} flex items-center justify-center text-xl shadow-lg`}>
                  {mod.icon}
                </div>
                <div className="text-right">
                  <div className="text-lg font-extrabold text-white">{mod.stats.value}</div>
                  <div className="text-[10px] text-surface-300">{mod.stats.label}</div>
                </div>
              </div>
              <h3 className="text-base font-semibold text-white group-hover:text-brand-400 transition">{mod.name}</h3>
              <p className="text-xs text-surface-300 mt-1">{mod.description}</p>
              <div className="mt-3 text-[11px] text-brand-400 opacity-0 group-hover:opacity-100 transition font-medium">Open →</div>
            </Link>
          ))}
        </div>
      </div>

      {/* Workflows CTA */}
      <div className="glass rounded-xl p-5 card-3d">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold flex items-center gap-2 text-white">
              🔗 Workflow Automation
            </h3>
            <p className="text-xs text-surface-300 mt-1">
              Chain studios: Write script → Generate voice → Create video → Add music → Publish
            </p>
          </div>
          <Link href="/dashboard/workflows"
            className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium transition shadow-sm">
            Create Workflow
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-lg font-semibold mb-3 text-surface-100">Recent Activity</h2>
        <div className="glass rounded-xl divide-y divide-surface-600/50">
          {recentActivity.map((item, i) => (
            <div key={i} className="flex items-center gap-4 px-4 py-3">
              <span className="text-lg">{item.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm text-white">{item.action}</div>
                <div className="text-[11px] text-surface-300">{item.module}</div>
              </div>
              <div className="text-[11px] text-surface-400 flex-shrink-0">{item.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
