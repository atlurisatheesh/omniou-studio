"use client";
import { useState } from "react";

const genres = [
  "pop", "rock", "electronic", "hip_hop", "jazz", "classical",
  "ambient", "lofi", "cinematic", "country", "rnb", "metal",
  "reggae", "blues", "folk", "edm", "trap", "indie",
];

const moods = [
  "happy", "sad", "energetic", "calm", "dark", "uplifting",
  "romantic", "epic", "mysterious", "playful", "aggressive", "dreamy",
  "nostalgic", "triumphant", "peaceful", "intense",
];

const sfxCategories = [
  { id: "ui", name: "UI Sounds", examples: "clicks, notifications, transitions" },
  { id: "nature", name: "Nature", examples: "rain, wind, birds, thunder" },
  { id: "transition", name: "Transitions", examples: "whoosh, swoosh, impacts" },
  { id: "ambient", name: "Ambient", examples: "cafe, city, forest, ocean" },
  { id: "musical", name: "Musical", examples: "drums, bass drops, stingers" },
];

export default function MusicStudioPage() {
  const [tab, setTab] = useState<"music" | "jingle" | "sfx" | "remix">("music");
  const [prompt, setPrompt] = useState("");
  const [genre, setGenre] = useState("electronic");
  const [mood, setMood] = useState("energetic");
  const [duration, setDuration] = useState(30);
  const [bpm, setBpm] = useState(120);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 2000));
    setResult(true);
    setLoading(false);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">🎵 Music Studio</h1>
        <p className="text-surface-500 mt-1">AI music generation, jingles, sound effects, and remixing</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {([
          { id: "music", label: "🎵 Generate Music" },
          { id: "jingle", label: "🔔 Jingle Maker" },
          { id: "sfx", label: "🔊 Sound Effects" },
          { id: "remix", label: "🎛️ Remix" },
        ] as const).map((t) => (
          <button
            key={t.id}
            onClick={() => { setTab(t.id as any); setResult(false); }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              tab === t.id ? "bg-brand-600 text-white" : "bg-[#1a1a2e] text-surface-500 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <div className="space-y-4">
          {tab === "sfx" ? (
            <div className="glass rounded-xl p-5">
              <h3 className="text-sm font-semibold text-surface-300 mb-3">SFX Categories</h3>
              <div className="space-y-2">
                {sfxCategories.map((cat) => (
                  <button
                    key={cat.id}
                    className="w-full p-3 rounded-lg bg-[#12121a] text-left hover:bg-brand-600/10 transition"
                  >
                    <p className="text-sm text-white font-medium">{cat.name}</p>
                    <p className="text-xs text-surface-500">{cat.examples}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : tab === "remix" ? (
            <div className="glass rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-semibold text-surface-300">Upload Audio</h3>
              <div className="border-2 border-dashed border-[#2a2a4a] rounded-lg p-6 text-center">
                <p className="text-3xl mb-2">🎧</p>
                <p className="text-sm text-surface-400">Drop audio file</p>
                <p className="text-xs text-surface-600">MP3, WAV, FLAC up to 50MB</p>
              </div>
              <div>
                <label className="text-xs text-surface-400">Remix Style</label>
                <select className="w-full mt-1 bg-[#12121a] border border-[#2a2a4a] rounded-lg px-3 py-2 text-white text-sm">
                  <option>EDM Remix</option>
                  <option>Lo-fi Version</option>
                  <option>Acoustic Cover</option>
                  <option>Jazz Arrangement</option>
                  <option>Orchestral</option>
                </select>
              </div>
            </div>
          ) : (
            <>
              <div className="glass rounded-xl p-5">
                <label className="text-sm font-medium text-surface-400 mb-2 block">
                  {tab === "jingle" ? "Brand / Product Name" : "Describe your music"}
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder={
                    tab === "jingle"
                      ? "A catchy 5-second jingle for a tech startup..."
                      : "Upbeat electronic track with synth arpeggios..."
                  }
                  className="w-full h-24 bg-[#12121a] border border-[#2a2a4a] rounded-lg p-3 text-white text-sm placeholder:text-surface-600 resize-none focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="glass rounded-xl p-5">
                <label className="text-xs text-surface-400 mb-2 block">Genre</label>
                <div className="grid grid-cols-3 gap-1.5 max-h-[140px] overflow-y-auto">
                  {genres.map((g) => (
                    <button
                      key={g}
                      onClick={() => setGenre(g)}
                      className={`px-2 py-1.5 rounded text-xs transition ${
                        genre === g ? "bg-brand-600 text-white" : "bg-[#12121a] text-surface-400 hover:text-white"
                      }`}
                    >
                      {g.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>

              <div className="glass rounded-xl p-5">
                <label className="text-xs text-surface-400 mb-2 block">Mood</label>
                <div className="grid grid-cols-2 gap-1.5 max-h-[140px] overflow-y-auto">
                  {moods.map((m) => (
                    <button
                      key={m}
                      onClick={() => setMood(m)}
                      className={`px-2 py-1.5 rounded text-xs transition ${
                        mood === m ? "bg-purple-600 text-white" : "bg-[#12121a] text-surface-400 hover:text-white"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              <div className="glass rounded-xl p-4 space-y-3">
                <div>
                  <label className="text-xs text-surface-400">Duration: {duration}s</label>
                  <input type="range" min={5} max={180} value={duration} onChange={(e) => setDuration(Number(e.target.value))} className="w-full accent-brand-500" />
                </div>
                <div>
                  <label className="text-xs text-surface-400">BPM: {bpm}</label>
                  <input type="range" min={60} max={200} value={bpm} onChange={(e) => setBpm(Number(e.target.value))} className="w-full accent-brand-500" />
                </div>
              </div>
            </>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white font-semibold disabled:opacity-50 transition"
          >
            {loading ? "⏳ Generating..." : `🎵 Generate — ${tab === "sfx" ? 1 : tab === "jingle" ? 3 : 5} Credits`}
          </button>
        </div>

        {/* Visualizer / Result */}
        <div className="lg:col-span-2">
          <div className="glass rounded-xl p-5 h-full">
            <h3 className="text-sm font-semibold text-surface-300 mb-3">Audio Player</h3>
            <div className="h-[300px] bg-[#0a0a0f] rounded-lg flex items-center justify-center mb-4">
              {loading ? (
                <div className="text-center">
                  <div className="flex gap-1 justify-center mb-4">
                    {Array.from({ length: 20 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-1.5 bg-brand-500 rounded-full animate-pulse"
                        style={{ height: `${20 + Math.random() * 60}px`, animationDelay: `${i * 0.1}s` }}
                      />
                    ))}
                  </div>
                  <p className="text-surface-400 text-sm">Composing your track...</p>
                </div>
              ) : result ? (
                <div className="text-center w-full px-8">
                  <div className="flex gap-0.5 justify-center mb-6">
                    {Array.from({ length: 60 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-1 bg-gradient-to-t from-brand-600 to-purple-400 rounded-full"
                        style={{ height: `${10 + Math.sin(i * 0.3) * 30 + Math.random() * 20}px` }}
                      />
                    ))}
                  </div>
                  <div className="flex items-center justify-center gap-4 mb-4">
                    <button className="w-12 h-12 rounded-full bg-brand-600 flex items-center justify-center text-xl">▶</button>
                    <div className="flex-1 max-w-xs">
                      <div className="h-1.5 bg-[#2a2a4a] rounded-full">
                        <div className="h-full w-1/3 bg-brand-500 rounded-full" />
                      </div>
                      <div className="flex justify-between text-xs text-surface-500 mt-1">
                        <span>0:{String(Math.floor(duration / 3)).padStart(2, "0")}</span>
                        <span>0:{String(duration).padStart(2, "0")}</span>
                      </div>
                    </div>
                    <button className="text-surface-400 hover:text-white text-sm">💾</button>
                  </div>
                  <p className="text-xs text-surface-500">{genre} • {mood} • {bpm} BPM • {duration}s</p>
                </div>
              ) : (
                <div className="text-center text-surface-500">
                  <p className="text-5xl mb-3">🎵</p>
                  <p className="text-sm">Your generated audio will play here</p>
                </div>
              )}
            </div>

            {result && (
              <div className="grid grid-cols-3 gap-3">
                <button className="py-2 rounded-lg bg-[#1a1a2e] text-surface-300 text-sm hover:text-white transition">🔄 Regenerate</button>
                <button className="py-2 rounded-lg bg-[#1a1a2e] text-surface-300 text-sm hover:text-white transition">✂️ Edit</button>
                <button className="py-2 rounded-lg bg-brand-600 text-white text-sm">💾 Download WAV</button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
