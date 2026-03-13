"use client";
import { useState } from "react";

const modes = [
  { id: "clone", name: "Face Swap / Clone", desc: "Swap faces in any video using AI", icon: "🎭", credits: 15 },
  { id: "generate", name: "AI Video Gen", desc: "Generate videos from text prompts", icon: "🎬", credits: 20 },
  { id: "edit", name: "Video Editor", desc: "Edit, trim, and enhance videos", icon: "✂️", credits: 5 },
  { id: "upscale", name: "Video Upscale", desc: "Upscale to 4K with AI", icon: "📺", credits: 10 },
];

const styles = ["Cinematic", "Documentary", "Animation", "Slow Motion", "Time Lapse", "Vlog", "Commercial", "Music Video"];

export default function VideoStudioPage() {
  const [mode, setMode] = useState("clone");
  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(15);
  const [style, setStyle] = useState("Cinematic");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(false);

  const activeMode = modes.find((m) => m.id === mode)!;

  const handleGenerate = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 2500));
    setResult(true);
    setLoading(false);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">🎬 Video Studio</h1>
        <p className="text-surface-500 mt-1">AI video generation, face swap, editing, and upscaling</p>
      </div>

      {/* Mode Selection */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {modes.map((m) => (
          <button
            key={m.id}
            onClick={() => { setMode(m.id); setResult(false); }}
            className={`p-4 rounded-xl text-left transition ${
              mode === m.id ? "bg-brand-600/20 border border-brand-500/50" : "glass card-hover"
            }`}
          >
            <span className="text-2xl">{m.icon}</span>
            <h3 className="font-semibold text-white mt-2 text-sm">{m.name}</h3>
            <p className="text-xs text-surface-500 mt-0.5">{m.desc}</p>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="lg:col-span-1 space-y-4">
          {mode === "clone" && (
            <div className="glass rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-semibold text-surface-300">Upload Files</h3>
              <div className="border-2 border-dashed border-[#2a2a4a] rounded-lg p-6 text-center">
                <p className="text-3xl mb-2">📹</p>
                <p className="text-sm text-surface-400">Drop source video</p>
                <p className="text-xs text-surface-600">MP4, MOV up to 500MB</p>
              </div>
              <div className="border-2 border-dashed border-[#2a2a4a] rounded-lg p-6 text-center">
                <p className="text-3xl mb-2">🖼️</p>
                <p className="text-sm text-surface-400">Drop target face image</p>
                <p className="text-xs text-surface-600">PNG, JPG up to 10MB</p>
              </div>
            </div>
          )}

          {(mode === "generate" || mode === "edit") && (
            <div className="glass rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-semibold text-surface-300">
                {mode === "generate" ? "Describe your video" : "Upload video to edit"}
              </h3>
              {mode === "generate" ? (
                <>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="A drone shot flying over snow-capped mountains at sunrise..."
                    className="w-full h-28 bg-[#12121a] border border-[#2a2a4a] rounded-lg p-3 text-white text-sm placeholder:text-surface-600 resize-none focus:outline-none focus:border-brand-500"
                  />
                  <div>
                    <label className="text-xs text-surface-400">Style</label>
                    <div className="grid grid-cols-2 gap-2 mt-1">
                      {styles.map((s) => (
                        <button
                          key={s}
                          onClick={() => setStyle(s)}
                          className={`px-3 py-1.5 rounded-lg text-xs transition ${
                            style === s ? "bg-brand-600 text-white" : "bg-[#1a1a2e] text-surface-400 hover:text-white"
                          }`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-surface-400">Duration: {duration}s</label>
                    <input
                      type="range"
                      min={5}
                      max={60}
                      value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                      className="w-full mt-1 accent-brand-500"
                    />
                    <div className="flex justify-between text-xs text-surface-600">
                      <span>5s</span>
                      <span>60s</span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="border-2 border-dashed border-[#2a2a4a] rounded-lg p-6 text-center">
                  <p className="text-3xl mb-2">📹</p>
                  <p className="text-sm text-surface-400">Drop video to edit</p>
                  <p className="text-xs text-surface-600">MP4, MOV, AVI up to 2GB</p>
                </div>
              )}
            </div>
          )}

          {mode === "upscale" && (
            <div className="glass rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-semibold text-surface-300">Upload video</h3>
              <div className="border-2 border-dashed border-[#2a2a4a] rounded-lg p-6 text-center">
                <p className="text-3xl mb-2">📹</p>
                <p className="text-sm text-surface-400">Drop video to upscale</p>
                <p className="text-xs text-surface-600">MP4, MOV up to 1GB</p>
              </div>
              <div>
                <label className="text-xs text-surface-400">Target Resolution</label>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  {["1080p", "2K", "4K", "8K"].map((r) => (
                    <button
                      key={r}
                      className="px-3 py-2 rounded-lg text-sm bg-[#1a1a2e] text-surface-400 hover:bg-brand-600/20 hover:text-brand-400 transition"
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold disabled:opacity-50 transition"
          >
            {loading ? "⏳ Processing..." : `${activeMode.icon} ${activeMode.name} — ${activeMode.credits} Credits`}
          </button>
        </div>

        {/* Preview */}
        <div className="lg:col-span-2">
          <div className="glass rounded-xl p-5 h-full">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">Preview</h3>
            <div className="aspect-video bg-[#0a0a0f] rounded-lg flex items-center justify-center">
              {loading ? (
                <div className="text-center">
                  <div className="w-12 h-12 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin mx-auto mb-3" />
                  <p className="text-surface-400">Processing video...</p>
                  <p className="text-xs text-surface-500/80 mt-1">This may take a few minutes</p>
                </div>
              ) : result ? (
                <div className="text-center">
                  <p className="text-6xl mb-4">✅</p>
                  <p className="text-white font-semibold">Video Ready!</p>
                  <p className="text-sm text-surface-400 mt-1">Your {activeMode.name.toLowerCase()} video is ready</p>
                  <div className="flex gap-3 mt-4 justify-center">
                    <button className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm">▶ Play</button>
                    <button className="px-4 py-2 rounded-lg bg-[#1a1a2e] text-surface-300 text-sm">💾 Download</button>
                  </div>
                </div>
              ) : (
                <div className="text-center text-surface-500">
                  <p className="text-5xl mb-3">🎬</p>
                  <p className="text-sm">Your video preview will appear here</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
