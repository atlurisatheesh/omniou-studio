"use client";
import { useState } from "react";

const styles = [
  "photorealistic", "digital_art", "watercolor", "oil_painting", "sketch",
  "anime", "3d_render", "pop_art", "minimalist", "cyberpunk", "fantasy", "pixel_art",
];

const sizes = [
  { label: "Square (1:1)", width: 1024, height: 1024 },
  { label: "Landscape (16:9)", width: 1920, height: 1080 },
  { label: "Portrait (9:16)", width: 1080, height: 1920 },
  { label: "Instagram Post", width: 1080, height: 1080 },
  { label: "YouTube Thumbnail", width: 1280, height: 720 },
  { label: "Facebook Cover", width: 1200, height: 630 },
];

export default function DesignStudioPage() {
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [selectedStyle, setSelectedStyle] = useState("photorealistic");
  const [selectedSize, setSelectedSize] = useState(sizes[0]);
  const [tab, setTab] = useState<"generate" | "template" | "tools">("generate");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 2000));
    setResult({
      file_id: `img_${Date.now().toString(36)}`,
      style: selectedStyle,
      size: `${selectedSize.width}×${selectedSize.height}`,
      prompt: prompt.slice(0, 50) + "...",
      status: "completed",
    });
    setLoading(false);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">🎨 Design Studio</h1>
        <p className="text-surface-500 mt-1">AI image generation, templates, and graphic design tools</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {(["generate", "template", "tools"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t ? "bg-brand-600 text-white" : "bg-[#1a1a2e] text-surface-500 hover:text-white"
            }`}
          >
            {t === "generate" ? "AI Generate" : t === "template" ? "Templates" : "Edit Tools"}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {/* Prompt */}
          <div className="glass rounded-xl p-5">
            <label className="block text-sm font-medium text-surface-400 mb-2">Describe your image</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="A futuristic city skyline at sunset with flying cars..."
              className="w-full h-28 bg-[#12121a] border border-[#2a2a4a] rounded-lg p-4 text-white placeholder:text-surface-600 resize-none focus:outline-none focus:border-brand-500"
            />
          </div>

          {/* Negative Prompt */}
          <div className="glass rounded-xl p-5">
            <label className="block text-sm font-medium text-surface-400 mb-2">Negative prompt (things to avoid)</label>
            <input
              value={negativePrompt}
              onChange={(e) => setNegativePrompt(e.target.value)}
              placeholder="blurry, low quality, text, watermark..."
              className="w-full bg-[#12121a] border border-[#2a2a4a] rounded-lg p-3 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500 text-sm"
            />
          </div>

          {/* Style Grid */}
          <div className="glass rounded-xl p-5">
            <label className="block text-sm font-medium text-surface-400 mb-3">Art Style</label>
            <div className="grid grid-cols-4 gap-2">
              {styles.map((s) => (
                <button
                  key={s}
                  onClick={() => setSelectedStyle(s)}
                  className={`py-2 px-3 rounded-lg text-xs font-medium transition ${
                    selectedStyle === s
                      ? "bg-brand-600 text-white"
                      : "bg-[#12121a] text-surface-500 hover:text-white hover:bg-[#1a1a2e]"
                  }`}
                >
                  {s.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 text-white font-semibold disabled:opacity-50 transition"
          >
            {loading ? "⏳ Generating image..." : "🎨 Generate Image — 3 Credits"}
          </button>
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          {/* Size */}
          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">Image Size</h3>
            <div className="space-y-2">
              {sizes.map((s) => (
                <button
                  key={s.label}
                  onClick={() => setSelectedSize(s)}
                  className={`w-full p-3 rounded-lg text-left text-sm transition ${
                    selectedSize.label === s.label
                      ? "bg-brand-600/20 border border-brand-600/30 text-white"
                      : "bg-[#12121a] text-surface-500 hover:text-white"
                  }`}
                >
                  <div className="font-medium">{s.label}</div>
                  <div className="text-xs text-surface-500">{s.width} × {s.height}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Quick Tools */}
          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">Quick Tools</h3>
            <div className="space-y-2">
              {["Remove Background", "Upscale 2x", "Upscale 4x", "Apply Filter"].map((tool) => (
                <button
                  key={tool}
                  className="w-full py-2 px-3 rounded-lg bg-[#12121a] text-surface-400 text-sm hover:text-white hover:bg-[#1a1a2e] transition text-left"
                >
                  {tool}
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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
