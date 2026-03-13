"use client";
import Link from "next/link";

const modules = [
  {
    id: "voice",
    name: "Voice Studio",
    icon: "🎙️",
    description: "Text-to-speech, voice cloning, multilingual dubbing",
    color: "from-blue-600 to-blue-400",
    href: "/dashboard/voice-studio",
    stats: { label: "Voices Generated", value: "12" },
  },
  {
    id: "design",
    name: "Design Studio",
    icon: "🎨",
    description: "AI image generation, templates, background removal",
    color: "from-pink-600 to-pink-400",
    href: "/dashboard/design-studio",
    stats: { label: "Designs Created", value: "8" },
  },
  {
    id: "code",
    name: "Code Studio",
    icon: "💻",
    description: "AI code generation, browser IDE, one-click deploy",
    color: "from-green-600 to-green-400",
    href: "/dashboard/code-studio",
    stats: { label: "Code Generated", value: "23" },
  },
  {
    id: "video",
    name: "Video Studio",
    icon: "🎬",
    description: "Video cloning, text-to-video, auto-subtitles",
    color: "from-purple-600 to-purple-400",
    href: "/dashboard/video-studio",
    stats: { label: "Videos Created", value: "5" },
  },
  {
    id: "writer",
    name: "AI Writer",
    icon: "✍️",
    description: "Blog posts, ad copy, scripts, SEO content",
    color: "from-yellow-600 to-yellow-400",
    href: "/dashboard/ai-writer",
    stats: { label: "Articles Written", value: "15" },
  },
  {
    id: "music",
    name: "Music Studio",
    icon: "🎵",
    description: "AI music, jingles, sound effects, remixes",
    color: "from-cyan-600 to-cyan-400",
    href: "/dashboard/music-studio",
    stats: { label: "Tracks Created", value: "3" },
  },
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
    <div className="max-w-7xl mx-auto space-y-8 fade-in">
      {/* Welcome */}
      <div>
        <h1 className="text-3xl font-bold mb-2">
          Welcome to <span className="gradient-text">Ominou Studio</span>
        </h1>
        <p className="text-surface-500">Your all-in-one AI creative platform. Pick a module to get started.</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Projects", value: "66", change: "+12 this week" },
          { label: "Credits Used", value: "23", change: "27 remaining" },
          { label: "Time Saved", value: "48h", change: "this month" },
          { label: "Assets Created", value: "142", change: "+28 this week" },
        ].map((stat) => (
          <div key={stat.label} className="glass rounded-xl p-4 card-hover">
            <div className="text-2xl font-bold text-white">{stat.value}</div>
            <div className="text-sm text-surface-500">{stat.label}</div>
            <div className="text-xs text-brand-400 mt-1">{stat.change}</div>
          </div>
        ))}
      </div>

      {/* Module Cards */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Creative Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {modules.map((mod) => (
            <Link
              key={mod.id}
              href={mod.href}
              className="glass rounded-xl p-5 card-hover group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${mod.color} flex items-center justify-center text-2xl`}>
                  {mod.icon}
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-white">{mod.stats.value}</div>
                  <div className="text-xs text-surface-500">{mod.stats.label}</div>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-white group-hover:text-brand-400 transition mb-1">
                {mod.name}
              </h3>
              <p className="text-sm text-surface-500">{mod.description}</p>
              <div className="mt-3 text-xs text-brand-400 opacity-0 group-hover:opacity-100 transition">
                Open module →
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Workflows CTA */}
      <div className="glass rounded-xl p-6 card-hover">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              🔗 Workflow Automation
            </h3>
            <p className="text-sm text-surface-500 mt-1">
              Chain modules together: Write a blog → Generate voiceover → Create thumbnail → all automatically.
            </p>
          </div>
          <Link
            href="/dashboard/workflows"
            className="px-5 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium transition"
          >
            Create Workflow
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <div className="glass rounded-xl divide-y divide-[#2a2a4a]">
          {recentActivity.map((item, i) => (
            <div key={i} className="flex items-center gap-4 p-4">
              <span className="text-xl">{item.icon}</span>
              <div className="flex-1">
                <div className="text-sm text-white">{item.action}</div>
                <div className="text-xs text-surface-500">{item.module}</div>
              </div>
              <div className="text-xs text-surface-500">{item.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
