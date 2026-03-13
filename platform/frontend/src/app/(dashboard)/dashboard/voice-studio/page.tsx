"use client";
import { useState } from "react";

const voices = [
  { id: "aria", name: "Aria", gender: "Female", accent: "American", style: "Professional" },
  { id: "marcus", name: "Marcus", gender: "Male", accent: "British", style: "Warm" },
  { id: "priya", name: "Priya", gender: "Female", accent: "Indian", style: "Friendly" },
  { id: "chen", name: "Chen", gender: "Male", accent: "Neutral", style: "Authoritative" },
  { id: "sofia", name: "Sofia", gender: "Female", accent: "Spanish", style: "Energetic" },
  { id: "kai", name: "Kai", gender: "Male", accent: "Australian", style: "Casual" },
  { id: "luna", name: "Luna", gender: "Female", accent: "British", style: "Calm" },
  { id: "ravi", name: "Ravi", gender: "Male", accent: "Indian", style: "Professional" },
];

export default function VoiceStudioPage() {
  const [tab, setTab] = useState<"tts" | "clone" | "dub">("tts");
  const [text, setText] = useState("");
  const [selectedVoice, setSelectedVoice] = useState("aria");
  const [speed, setSpeed] = useState(1.0);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise((r) => setTimeout(r, 1500));
    const voice = voices.find((v) => v.id === selectedVoice);
    setResult({
      file_id: `tts_${Date.now().toString(36)}`,
      voice: voice?.name,
      duration: `${(text.split(" ").length / 2.5 / speed).toFixed(1)}s`,
      words: text.split(" ").length,
      status: "completed",
    });
    setLoading(false);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">
          🎙️ Voice Studio
        </h1>
        <p className="text-surface-500 mt-1">Text-to-speech, voice cloning, and multilingual dubbing</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {(["tts", "clone", "dub"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t ? "bg-brand-600 text-white" : "bg-[#1a1a2e] text-surface-500 hover:text-white"
            }`}
          >
            {t === "tts" ? "Text to Speech" : t === "clone" ? "Voice Clone" : "Dubbing"}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass rounded-xl p-5">
            <label className="block text-sm font-medium text-surface-400 mb-2">
              {tab === "tts" ? "Enter text to convert" : tab === "clone" ? "Voice samples" : "Text to dub"}
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={
                tab === "tts"
                  ? "Type or paste your text here... (up to 5,000 characters)"
                  : tab === "dub"
                  ? "Enter text to translate and dub..."
                  : ""
              }
              className="w-full h-40 bg-[#12121a] border border-[#2a2a4a] rounded-lg p-4 text-white placeholder:text-surface-600 resize-none focus:outline-none focus:border-brand-500"
            />
            <div className="flex justify-between mt-2">
              <span className="text-xs text-surface-500">{text.length}/5000 characters</span>
              <span className="text-xs text-surface-500">{text.split(" ").filter(Boolean).length} words</span>
            </div>
          </div>

          {/* Controls */}
          <div className="glass rounded-xl p-5">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-surface-400 mb-2">Speed</label>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="text-xs text-surface-500 mt-1">{speed}x</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-surface-400 mb-2">Format</label>
                <select className="w-full bg-[#12121a] border border-[#2a2a4a] rounded-lg p-2.5 text-white text-sm">
                  <option>MP3 (recommended)</option>
                  <option>WAV (high quality)</option>
                  <option>OGG</option>
                </select>
              </div>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!text.trim() || loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-brand-600 to-purple-600 hover:from-brand-700 hover:to-purple-700 text-white font-semibold disabled:opacity-50 transition"
          >
            {loading ? "⏳ Generating..." : "🎙️ Generate Voice — 1 Credit"}
          </button>
        </div>

        {/* Voice Selection */}
        <div className="space-y-4">
          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">Select Voice</h3>
            <div className="space-y-2">
              {voices.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setSelectedVoice(v.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition ${
                    selectedVoice === v.id
                      ? "bg-brand-600/20 border border-brand-600/30"
                      : "bg-[#12121a] hover:bg-[#1a1a2e]"
                  }`}
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
                    {v.name[0]}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{v.name}</div>
                    <div className="text-xs text-surface-500">{v.gender} · {v.accent} · {v.style}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className="glass rounded-xl p-5 border-green-600/30 border">
              <h3 className="text-sm font-semibold text-green-400 mb-3">✅ Generated</h3>
              {Object.entries(result).map(([key, val]) => (
                <div key={key} className="flex justify-between text-sm py-1">
                  <span className="text-surface-500 capitalize">{key.replace(/_/g, " ")}</span>
                  <span className="text-white">{String(val)}</span>
                </div>
              ))}
              <button className="w-full mt-3 py-2 rounded-lg bg-green-600/20 text-green-400 text-sm hover:bg-green-600/30 transition">
                ▶ Play Audio
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
