"use client";
import { useState } from "react";

const templates = [
  { id: "content_campaign", name: "Content Campaign", desc: "Write → Design → Schedule → Publish", icon: "📢", steps: 4 },
  { id: "video_production", name: "Video Production", desc: "Script → Voice → Video → Edit", icon: "🎬", steps: 4 },
  { id: "brand_kit", name: "Brand Kit", desc: "Logo → Colors → Templates → Assets", icon: "🎨", steps: 4 },
  { id: "podcast_pipeline", name: "Podcast Pipeline", desc: "Script → Record → Music → Publish", icon: "🎙️", steps: 4 },
];

const mockWorkflows = [
  { id: 1, name: "Q4 Marketing Campaign", status: "running", progress: 65, steps: 6, completedSteps: 4, created: "2 hours ago" },
  { id: 2, name: "Product Launch Video", status: "completed", progress: 100, steps: 4, completedSteps: 4, created: "1 day ago" },
  { id: 3, name: "Weekly Blog Pipeline", status: "paused", progress: 33, steps: 3, completedSteps: 1, created: "3 days ago" },
];

const stepTypes = [
  { id: "voice_tts", name: "Text to Speech", service: "Voice Studio", icon: "🎤" },
  { id: "design_generate", name: "Generate Image", service: "Design Studio", icon: "🎨" },
  { id: "code_generate", name: "Generate Code", service: "Code Studio", icon: "💻" },
  { id: "writer_generate", name: "Write Content", service: "AI Writer", icon: "✍️" },
  { id: "music_generate", name: "Generate Music", service: "Music Studio", icon: "🎵" },
  { id: "video_generate", name: "Generate Video", service: "Video Studio", icon: "🎬" },
];

export default function WorkflowsPage() {
  const [tab, setTab] = useState<"workflows" | "templates" | "builder">("workflows");

  return (
    <div className="max-w-6xl mx-auto space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">⚡ Workflows</h1>
          <p className="text-surface-500 mt-1">Automate multi-step AI pipelines across all studios</p>
        </div>
        <button
          onClick={() => setTab("builder")}
          className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition"
        >
          + New Workflow
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {(["workflows", "templates", "builder"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t ? "bg-brand-600 text-white" : "bg-[#1a1a2e] text-surface-500 hover:text-white"
            }`}
          >
            {t === "workflows" ? "📋 My Workflows" : t === "templates" ? "📦 Templates" : "🔧 Builder"}
          </button>
        ))}
      </div>

      {tab === "workflows" && (
        <div className="space-y-3">
          {mockWorkflows.map((wf) => (
            <div key={wf.id} className="glass rounded-xl p-5 card-hover">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-white">{wf.name}</h3>
                  <p className="text-xs text-surface-500">Created {wf.created}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    wf.status === "running"
                      ? "bg-green-500/20 text-green-400"
                      : wf.status === "completed"
                      ? "bg-blue-500/20 text-blue-400"
                      : "bg-yellow-500/20 text-yellow-400"
                  }`}
                >
                  {wf.status}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="h-2 bg-[#1a1a2e] rounded-full">
                    <div
                      className={`h-full rounded-full transition-all ${
                        wf.status === "completed" ? "bg-blue-500" : "bg-brand-500"
                      }`}
                      style={{ width: `${wf.progress}%` }}
                    />
                  </div>
                </div>
                <span className="text-xs text-surface-400">{wf.completedSteps}/{wf.steps} steps</span>
                <div className="flex gap-2">
                  {wf.status === "running" && (
                    <button className="px-3 py-1 rounded text-xs bg-yellow-600/20 text-yellow-400">⏸ Pause</button>
                  )}
                  {wf.status === "paused" && (
                    <button className="px-3 py-1 rounded text-xs bg-green-600/20 text-green-400">▶ Resume</button>
                  )}
                  <button className="px-3 py-1 rounded text-xs bg-[#1a1a2e] text-surface-400 hover:text-white">View</button>
                </div>
              </div>
            </div>
          ))}

          {mockWorkflows.length === 0 && (
            <div className="glass rounded-xl p-12 text-center">
              <p className="text-4xl mb-3">⚡</p>
              <p className="text-surface-400">No workflows yet</p>
              <p className="text-sm text-surface-500 mt-1">Create your first workflow to automate AI tasks</p>
            </div>
          )}
        </div>
      )}

      {tab === "templates" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {templates.map((t) => (
            <div key={t.id} className="glass rounded-xl p-6 card-hover">
              <div className="flex items-start gap-4">
                <span className="text-3xl">{t.icon}</span>
                <div className="flex-1">
                  <h3 className="font-semibold text-white text-lg">{t.name}</h3>
                  <p className="text-sm text-surface-400 mt-1">{t.desc}</p>
                  <p className="text-xs text-surface-500 mt-2">{t.steps} automated steps</p>
                  <button className="mt-3 px-4 py-2 rounded-lg bg-brand-600/20 text-brand-400 text-sm hover:bg-brand-600/30 transition">
                    Use Template
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "builder" && (
        <div className="space-y-4">
          <div className="glass rounded-xl p-5">
            <label className="text-sm font-medium text-surface-400">Workflow Name</label>
            <input
              placeholder="My Awesome Workflow"
              className="w-full mt-2 bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500"
            />
          </div>

          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">Add Steps</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {stepTypes.map((st) => (
                <button
                  key={st.id}
                  className="p-4 rounded-lg bg-[#12121a] text-left hover:bg-brand-600/10 transition group"
                >
                  <span className="text-2xl">{st.icon}</span>
                  <p className="text-sm text-white font-medium mt-2">{st.name}</p>
                  <p className="text-xs text-surface-500">{st.service}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">Pipeline Preview</h3>
            <div className="flex items-center gap-3 py-4 overflow-x-auto">
              <div className="flex-shrink-0 w-32 p-3 rounded-lg bg-green-600/20 border border-green-500/30 text-center">
                <p className="text-xs text-green-400">Start</p>
              </div>
              <span className="text-surface-500">→</span>
              <div className="flex-shrink-0 w-32 p-3 rounded-lg border-2 border-dashed border-[#2a2a4a] text-center">
                <p className="text-xs text-surface-500">Add step</p>
              </div>
              <span className="text-surface-500">→</span>
              <div className="flex-shrink-0 w-32 p-3 rounded-lg bg-blue-600/20 border border-blue-500/30 text-center">
                <p className="text-xs text-blue-400">End</p>
              </div>
            </div>
          </div>

          <button className="w-full py-3 rounded-lg bg-gradient-to-r from-brand-600 to-purple-600 text-white font-semibold">
            🚀 Create Workflow
          </button>
        </div>
      )}
    </div>
  );
}
