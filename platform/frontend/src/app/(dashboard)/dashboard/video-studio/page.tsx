"use client";
import { useState, useEffect, useRef } from "react";

/* ═══════════════════════════════════════════════════════════════
   DATA
   ═══════════════════════════════════════════════════════════════ */

const tabs = [
  { id: "studio", label: "Film Studio", icon: "🎬", desc: "Script → Full Video" },
  { id: "clone", label: "Clone Lab", icon: "🧬", desc: "Voice & Face Cloning" },
  { id: "crew", label: "AI Crew", icon: "🎯", desc: "Your Production Team" },
] as const;

type TabId = (typeof tabs)[number]["id"];

interface ChatMsg {
  role: "user" | "ai" | "system";
  content: string;
  timestamp: Date;
  type?: "text" | "scene-breakdown" | "crew-update" | "progress";
}

const crewMembers = [
  { id: "director", name: "Director", role: "Creative Vision & Pacing", icon: "🎬", color: "from-indigo-500 to-blue-500", status: "idle" as string },
  { id: "dop", name: "DOP", role: "Camera, Lighting & Composition", icon: "📷", color: "from-amber-500 to-orange-500", status: "idle" as string },
  { id: "scriptwriter", name: "Scriptwriter", role: "Dialogue, Structure & Narrative", icon: "✍️", color: "from-emerald-500 to-teal-500", status: "idle" as string },
  { id: "musicdir", name: "Music Director", role: "Score, SFX & Audio Design", icon: "🎵", color: "from-purple-500 to-pink-500", status: "idle" as string },
  { id: "designer", name: "Graphic Designer", role: "Titles, Overlays & Motion Graphics", icon: "🎨", color: "from-rose-500 to-red-500", status: "idle" as string },
  { id: "vfx", name: "VFX Artist", role: "Visual Effects & Compositing", icon: "✨", color: "from-cyan-500 to-blue-500", status: "idle" as string },
  { id: "choreographer", name: "Choreographer", role: "Movement, Blocking & Transitions", icon: "💃", color: "from-fuchsia-500 to-purple-500", status: "idle" as string },
];

const styles = ["Cinematic", "3D", "2D Animation", "Normal", "Documentary", "Slow Motion", "Time Lapse", "Vlog", "Commercial", "Music Video"];
const voices = [
  { id: "aria", name: "Aria", desc: "Professional, American" },
  { id: "marcus", name: "Marcus", desc: "Warm, British" },
  { id: "priya", name: "Priya", desc: "Friendly, Indian" },
  { id: "chen", name: "Chen", desc: "Authoritative, Neutral" },
  { id: "sofia", name: "Sofia", desc: "Energetic, Spanish" },
  { id: "luna", name: "Luna", desc: "Calm, British" },
];

const durationPresets = [
  { label: "1 min", value: 60 }, { label: "2 min", value: 120 }, { label: "3 min", value: 180 },
  { label: "5 min", value: 300 }, { label: "10 min", value: 600 }, { label: "Custom", value: -1 },
];

const publishPlatforms = [
  { id: "youtube", name: "YouTube", icon: "📺" },
  { id: "instagram", name: "Reels", icon: "📸" },
  { id: "tiktok", name: "TikTok", icon: "🎵" },
  { id: "x", name: "X", icon: "𝕏" },
  { id: "linkedin", name: "LinkedIn", icon: "💼" },
];

const promptTemplates = [
  { label: "Product Demo", prompt: "A sleek product reveal video showing a premium tech gadget rotating in dramatic lighting, transitioning to hands-on demonstration with close-up macro shots of details, ending with the product in a lifestyle setting." },
  { label: "Travel Vlog", prompt: "A sweeping drone shot over snow-capped mountains at golden hour, transitioning to a bustling ancient market with incense smoke and colorful flags, then a sunset timelapse over the ocean." },
  { label: "Brand Story", prompt: "A cinematic brand origin story: start with a single person working late in a garage workshop, transition to a growing team in a bright office, culminate in a crowd of happy customers using the product." },
  { label: "Music Video", prompt: "An artistic music video with dreamlike slow-motion sequences, neon-lit urban streets at night, silhouettes dancing in colorful smoke, and dramatic camera movements." },
  { label: "Documentary", prompt: "A documentary-style video opening with archival footage aesthetic, transitioning to modern-day interviews in natural light, interspersed with atmospheric B-roll of landscapes and cityscapes." },
  { label: "Social Ad", prompt: "A fast-paced 30-second social media ad: attention-grabbing hook in the first 3 seconds, dynamic product showcase with bold text overlays, and a clear call-to-action ending." },
];

/* ═══════════════════════════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════════════════════════ */

export default function VideoStudioPage() {
  const [activeTab, setActiveTab] = useState<TabId>("studio");

  // Film Studio state
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([
    { role: "ai", content: "Welcome to Film Studio. Paste your script, describe a video, or use a template — I'll break it into scenes and generate everything: video, narration, music, titles.", timestamp: new Date(), type: "text" },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [script, setScript] = useState("");
  const [inputMode, setInputMode] = useState<"chat" | "script">("chat");
  const [duration, setDuration] = useState(60);
  const [customDuration, setCustomDuration] = useState("");
  const [style, setStyle] = useState("Cinematic");
  const [resolution, setResolution] = useState("1080p");
  const [quality, setQuality] = useState("high");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [includeNarration, setIncludeNarration] = useState(true);
  const [includeMusic, setIncludeMusic] = useState(true);
  const [voice, setVoice] = useState("aria");
  const provider = "auto";
  const [enableLipSync, setEnableLipSync] = useState(false);
  const [publishTo, setPublishTo] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [crew, setCrew] = useState(crewMembers);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Clone Lab state
  const [cloneType, setCloneType] = useState<"voice" | "face">("voice");

  const togglePlatform = (id: string) => {
    setPublishTo((prev) => prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]);
  };

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chatMessages]);

  // Poll progress
  useEffect(() => {
    if (!jobId || !loading) return;
    pollRef.current = setInterval(async () => {
      try {
        const token = localStorage.getItem("ominou_token");
        const res = await fetch(`http://localhost:1993/api/v1/video/progress/${jobId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setProgress(data.progress || 0);
          setProgressMessage(data.stage || "");
          // Simulate crew activity based on progress
          setCrew(prev => prev.map(c => {
            if (data.progress < 10) return { ...c, status: c.id === "scriptwriter" ? "active" : "idle" };
            if (data.progress < 25) return { ...c, status: ["scriptwriter", "director"].includes(c.id) ? "active" : c.id === "scriptwriter" ? "done" : "idle" };
            if (data.progress < 50) return { ...c, status: ["dop", "vfx", "designer"].includes(c.id) ? "active" : ["scriptwriter", "director"].includes(c.id) ? "done" : "idle" };
            if (data.progress < 80) return { ...c, status: ["musicdir", "choreographer"].includes(c.id) ? "active" : ["scriptwriter", "director", "dop", "vfx", "designer"].includes(c.id) ? "done" : "idle" };
            return { ...c, status: "done" };
          }));
          if (data.progress >= 100) clearInterval(pollRef.current!);
        }
      } catch { /* ignore */ }
    }, 2000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [jobId, loading]);

  const handleGenerate = async (inputText: string) => {
    if (!inputText.trim()) return;
    setLoading(true);
    setVideoUrl(null);
    setProgress(0);
    setProgressMessage("Assembling your AI crew...");
    setCrew(prev => prev.map(c => ({ ...c, status: c.id === "director" ? "active" : "idle" })));

    setChatMessages(prev => [...prev, {
      role: "system", content: "Production started. Your AI crew is assembling...", timestamp: new Date(), type: "progress"
    }]);

    try {
      const token = localStorage.getItem("ominou_token");
      const trimmed = inputText.trim();
      const isScript = inputMode === "script" || inputText.includes("SCENE") || inputText.includes("INT.") || inputText.includes("EXT.") || (trimmed.startsWith("{") && trimmed.endsWith("}"));
      const body: Record<string, unknown> = {
        prompt: isScript ? `Generate video from script: ${inputText.slice(0, 200)}` : inputText,
        duration: duration === -1 ? parseInt(customDuration) || 60 : duration,
        style: style.toLowerCase().replace(/ /g, "_"), resolution, quality,
        aspect_ratio: aspectRatio,
        include_narration: includeNarration, include_music: includeMusic, voice, provider,
        enable_lip_sync: enableLipSync, publish_to: publishTo.length > 0 ? publishTo : null,
      };
      if (isScript) body.script = inputText;

      const res = await fetch("http://localhost:1993/api/v1/video/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (data.data?.job_id) setJobId(data.data.job_id);
      const resultData = data.data || data;
      if (resultData.file_url) setVideoUrl(`http://localhost:1993${resultData.file_url}`);
      setProgress(100);
      setProgressMessage("Complete!");
      setCrew(prev => prev.map(c => ({ ...c, status: "done" })));

      setChatMessages(prev => [...prev, {
        role: "ai",
        content: resultData.error
          ? `Error: ${String(resultData.error)}`
          : `Video ready! ${duration === -1 ? customDuration + "s" : duration >= 60 ? Math.floor(duration / 60) + " min" : duration + "s"} ${style} • ${resolution} • ${aspectRatio} • ${quality}${resultData.scenes_generated ? ` • ${resultData.scenes_generated} scenes` : ""}`,
        timestamp: new Date(), type: "text"
      }]);
    } catch {
      setChatMessages(prev => [...prev, {
        role: "ai", content: "Generation failed. Check API keys and try again.", timestamp: new Date(), type: "text"
      }]);
    } finally {
      setLoading(false);
    }
  };

  const sendChat = () => {
    if (!chatInput.trim()) return;
    setChatMessages(prev => [...prev, { role: "user", content: chatInput, timestamp: new Date(), type: "text" }]);
    const text = chatInput;
    setChatInput("");

    // Analyze the input
    const hasSceneMarkers = /SCENE|INT\.|EXT\.|---/i.test(text);
    if (hasSceneMarkers || text.length > 300) {
      setScript(text);
      setInputMode("script");
      const sceneCount = (text.match(/SCENE|INT\.|EXT\.|---/gi) || []).length || 1;
      setChatMessages(prev => [...prev, {
        role: "ai",
        content: `Script detected — ${sceneCount} scene${sceneCount > 1 ? "s" : ""} found, ${text.length} characters. Ready to generate. Adjust settings on the right, then hit Generate or type "go".`,
        timestamp: new Date(), type: "scene-breakdown"
      }]);
    } else if (text.toLowerCase() === "go" || text.toLowerCase() === "generate") {
      handleGenerate(script || chatMessages.filter(m => m.role === "user").pop()?.content || "");
    } else {
      setChatMessages(prev => [...prev, {
        role: "ai",
        content: `Got it — "${text.slice(0, 80)}${text.length > 80 ? "..." : ""}". I'll use this as the creative brief. Adjust duration, style, and provider on the right, then type "go" or click Generate.`,
        timestamp: new Date(), type: "text"
      }]);
      setInputMode("chat");
    }
  };

  /* ─── Render helpers ──────────────────────────────────────── */
  const Toggle = ({ on, onToggle, label, sub }: { on: boolean; onToggle: () => void; label: string; sub: string }) => (
    <div className="flex items-center justify-between">
      <div><span className="text-xs text-surface-100 block">{label}</span><span className="text-[10px] text-surface-300">{sub}</span></div>
      <button onClick={onToggle} aria-label={`Toggle ${label}`} className={`w-10 h-5 rounded-full transition flex items-center px-0.5 ${on ? "bg-brand-500" : "bg-surface-600"}`}>
        <span className={`block w-4 h-4 bg-white rounded-full transition-transform ${on ? "translate-x-5" : ""}`} />
      </button>
    </div>
  );

  return (
    <div className="max-w-[1400px] mx-auto space-y-5 fade-in">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="gradient-text">Film Studio</span>
          </h1>
          <p className="text-surface-300 text-sm mt-0.5">
            Script → Video • AI Crew • Duration, Style, Quality & Aspect Ratio Controls
          </p>
        </div>
        <div className="flex gap-1 glass rounded-xl p-1">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === t.id ? "bg-brand-500/20 text-brand-400 shadow-sm" : "text-surface-300 hover:text-white hover:bg-white/[0.04]"
              }`}>
              <span>{t.icon}</span><span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════
         TAB: FILM STUDIO
         ════════════════════════════════════════════════════════ */}
      {activeTab === "studio" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left: Chat + Script Analyzer */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            {/* Input mode toggle */}
            <div className="flex gap-2">
              <button onClick={() => setInputMode("chat")}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${inputMode === "chat" ? "bg-brand-500/15 text-brand-400 border border-brand-500/25" : "glass text-surface-300 hover:text-white"}`}>
                💬 Chat Mode
              </button>
              <button onClick={() => setInputMode("script")}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${inputMode === "script" ? "bg-brand-500/15 text-brand-400 border border-brand-500/25" : "glass text-surface-300 hover:text-white"}`}>
                📜 Script Mode
              </button>
            </div>

            {inputMode === "chat" ? (
              /* ─ Chat Interface ─ */
              <div className="glass rounded-xl flex flex-col" style={{ height: "520px" }}>
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[85%] px-4 py-2.5 text-sm leading-relaxed ${
                        msg.role === "user" ? "chat-bubble-user text-white" :
                        msg.role === "system" ? "text-xs text-surface-300 italic px-0" :
                        "chat-bubble-ai text-surface-100"
                      }`}>
                        {msg.type === "scene-breakdown" && <span className="text-[10px] uppercase tracking-wider text-brand-400 block mb-1 font-semibold">Scene Analysis</span>}
                        {msg.type === "progress" && <span className="text-[10px] uppercase tracking-wider text-accent-green block mb-1 font-semibold">Production</span>}
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>
                <div className="border-t border-[#1e1e30] p-3 flex gap-2">
                  <input value={chatInput} onChange={e => setChatInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && sendChat()}
                    placeholder="Describe your video or paste a script..."
                    className="flex-1 bg-surface-800 border border-surface-600 rounded-lg px-3 py-2 text-sm text-white placeholder:text-surface-300 focus:outline-none focus:border-brand-500" />
                  <button onClick={sendChat} className="px-4 py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium transition">
                    Send
                  </button>
                </div>
              </div>
            ) : (
              /* ─ Script Editor ─ */
              <div className="glass rounded-xl p-4 flex flex-col" style={{ height: "520px" }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-surface-200 font-semibold">Script Editor</span>
                  <span className="text-[10px] text-surface-300">{script.length} chars</span>
                </div>
                <textarea value={script} onChange={e => setScript(e.target.value)}
                  placeholder={"SCENE 1: INT. COFFEE SHOP - MORNING\nA young woman sits alone at a window table, rain streaming down the glass.\n\nEMMA: (voiceover) It started like any other Tuesday...\n\nSCENE 2: EXT. CITY STREET - CONTINUOUS\nEmma walks briskly through the rain.\n\n---\nPaste your full script. Scene markers auto-detected."}
                  className="flex-1 bg-surface-800 border border-surface-600 rounded-lg p-3 text-white text-sm placeholder:text-surface-400 resize-none focus:outline-none focus:border-brand-500 font-mono leading-relaxed" />
                <div className="flex gap-2 mt-3">
                  <button onClick={() => {
                    if (script.trim()) {
                      setChatMessages(prev => [...prev, { role: "user", content: `[Script uploaded — ${script.length} chars]`, timestamp: new Date(), type: "text" }]);
                      const sc = (script.match(/SCENE|INT\.|EXT\.|---/gi) || []).length || 1;
                      setChatMessages(prev => [...prev, { role: "ai", content: `Analyzed ${sc} scene${sc > 1 ? "s" : ""}. Ready to generate.`, timestamp: new Date(), type: "scene-breakdown" }]);
                    }
                  }} className="flex-1 py-2 rounded-lg glass text-surface-200 text-sm hover:text-white transition font-medium">
                    🔍 Analyze Script
                  </button>
                  {script.trim() && <button onClick={() => setScript("")} className="px-3 py-2 rounded-lg text-red-400 hover:text-red-300 text-sm glass transition">Clear</button>}
                </div>
              </div>
            )}

            {/* Quick Templates */}
            <div className="glass rounded-xl p-4">
              <span className="text-xs text-surface-200 font-semibold block mb-2">Quick Templates</span>
              <div className="flex flex-wrap gap-1.5">
                {promptTemplates.map(t => (
                  <button key={t.label} onClick={() => {
                    setChatInput(t.prompt);
                    if (inputMode === "script") { setScript(t.prompt); setInputMode("chat"); }
                  }} className="text-[11px] px-2.5 py-1.5 rounded-lg bg-surface-700 text-surface-200 hover:text-brand-400 hover:bg-brand-500/10 transition font-medium">
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Middle: Preview */}
          <div className="lg:col-span-4 flex flex-col gap-4">
            <div className="glass rounded-xl p-4 flex-1 flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-surface-200 font-semibold">Preview</span>
                {videoUrl && <span className="text-[10px] text-accent-green font-medium">● Ready</span>}
              </div>
              <div className="aspect-video bg-surface-900 rounded-lg flex items-center justify-center overflow-hidden relative">
                {loading ? (
                  <div className="text-center w-full px-6">
                    <div className="w-10 h-10 border-3 border-brand-500/30 border-t-brand-500 rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-white text-sm font-medium">{progressMessage || "Processing..."}</p>
                    <div className="w-full bg-surface-700 rounded-full h-2 mt-3 overflow-hidden">
                      <div className="bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500 h-2 rounded-full transition-all duration-700" style={{ width: `${Math.max(2, progress)}%` }} />
                    </div>
                    <p className="text-[11px] text-surface-300 mt-2">{progress}%</p>
                  </div>
                ) : videoUrl ? (
                  <video ref={videoRef} src={videoUrl} controls className="w-full h-full rounded-lg object-contain" />
                ) : (
                  <div className="text-center text-surface-300">
                    <p className="text-4xl mb-2">🎬</p>
                    <p className="text-sm">Your video preview</p>
                    <p className="text-[11px] text-surface-400 mt-0.5">Up to 10 min • 3D / Cinematic / 2D • 4K</p>
                  </div>
                )}
              </div>

              {/* Pipeline Steps */}
              {loading && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {["Script AI", "Voice", "Video Gen", "Lip Sync", "Music", "Stitch", "Publish"].map((step, i) => {
                    const thresholds = [5, 15, 25, 72, 80, 85, 94];
                    const isDone = progress >= (thresholds[i + 1] || 100);
                    const isActive = progress >= thresholds[i] && !isDone;
                    return (
                      <span key={step} className={`pipeline-step text-[10px] px-2 py-1 rounded-lg border transition-all ${
                        isDone ? "done bg-accent-green/10 text-accent-green border-accent-green/20" :
                        isActive ? "active bg-brand-500/10 text-brand-400 border-brand-500/30 animate-pulse" :
                        "bg-surface-800 text-surface-400 border-surface-600"
                      }`}>
                        {isDone ? "✓" : isActive ? "⟳" : "○"} {step}
                      </span>
                    );
                  })}
                </div>
              )}

              {/* Actions */}
              {videoUrl && !loading && (
                <div className="flex gap-2 mt-3">
                  <a href={videoUrl} download className="flex-1 py-2 rounded-lg glass text-center text-sm text-surface-200 hover:text-white transition font-medium">
                    💾 Download
                  </a>
                  <button onClick={() => { setVideoUrl(null); setProgress(0); }}
                    className="flex-1 py-2 rounded-lg glass text-center text-sm text-surface-200 hover:text-white transition font-medium">
                    🔄 New
                  </button>
                </div>
              )}
            </div>

            {/* AI Crew Status (mini) */}
            <div className="glass rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-surface-200 font-semibold">AI Crew Status</span>
                <button onClick={() => setActiveTab("crew")} className="text-[10px] text-brand-400 hover:text-brand-300 transition">
                  View All →
                </button>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {crew.slice(0, 4).map(c => (
                  <div key={c.id} className="text-center">
                    <div className={`w-9 h-9 mx-auto rounded-full bg-gradient-to-br ${c.color} flex items-center justify-center text-sm ${
                      c.status === "active" ? "ring-2 ring-brand-400 ring-offset-2 ring-offset-surface-900 animate-pulse" :
                      c.status === "done" ? "ring-2 ring-accent-green/40 ring-offset-1 ring-offset-surface-900" : "opacity-50"
                    }`}>
                      {c.icon}
                    </div>
                    <p className="text-[10px] text-surface-300 mt-1 truncate">{c.name}</p>
                    <p className={`text-[9px] font-medium ${c.status === "active" ? "text-brand-400" : c.status === "done" ? "text-accent-green" : "text-surface-400"}`}>
                      {c.status === "active" ? "Working" : c.status === "done" ? "Done" : "Standby"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Controls */}
          <div className="lg:col-span-3 space-y-3 max-h-[760px] overflow-y-auto pr-1">
            {/* Duration */}
            <div className="glass rounded-xl p-4 space-y-3">
              <span className="text-xs text-surface-200 font-semibold block">Duration</span>
              <div className="grid grid-cols-3 gap-1.5">
                {durationPresets.map(d => (
                  <button key={d.value} onClick={() => setDuration(d.value)}
                    className={`py-2 rounded-lg text-center text-xs font-medium transition ${
                      duration === d.value ? "bg-brand-500 text-white" : "bg-surface-700 text-surface-200 hover:text-white"
                    }`}>{d.label}</button>
                ))}
              </div>
              {duration === -1 && (
                <div className="flex items-center gap-2 mt-2">
                  <input type="number" min="10" max="600" value={customDuration} onChange={e => setCustomDuration(e.target.value)}
                    placeholder="Seconds (10–600)"
                    className="flex-1 bg-surface-800 border border-surface-600 rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-surface-400 focus:outline-none focus:border-brand-500" />
                  <span className="text-[10px] text-surface-400">sec</span>
                </div>
              )}
            </div>

            {/* Aspect Ratio */}
            <div className="glass rounded-xl p-4 space-y-3">
              <span className="text-xs text-surface-200 font-semibold block">Aspect Ratio</span>
              <div className="grid grid-cols-4 gap-1.5">
                {[
                  { id: "16:9", label: "16:9", sub: "Landscape" },
                  { id: "9:16", label: "9:16", sub: "Portrait" },
                  { id: "1:1", label: "1:1", sub: "Square" },
                  { id: "4:3", label: "4:3", sub: "Classic" },
                ].map(ar => (
                  <button key={ar.id} onClick={() => setAspectRatio(ar.id)}
                    className={`py-2 rounded-lg text-center transition ${
                      aspectRatio === ar.id ? "bg-brand-500/20 border border-brand-500/40 text-brand-400" : "bg-surface-700 text-surface-200 hover:text-white"
                    }`}>
                    <span className="text-xs font-semibold block">{ar.label}</span>
                    <span className="text-[9px] text-surface-300">{ar.sub}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Style */}
            <div className="glass rounded-xl p-4 space-y-3">
              <span className="text-xs text-surface-200 font-semibold block">Video Style</span>
              <div className="grid grid-cols-2 gap-1.5">
                {styles.map(s => (
                  <button key={s} onClick={() => setStyle(s)}
                    className={`py-1.5 rounded-lg text-xs font-medium transition ${
                      style === s ? "bg-brand-500 text-white" : "bg-surface-700 text-surface-200 hover:text-white"
                    }`}>{s}</button>
                ))}
              </div>
            </div>

            {/* Resolution & Quality */}
            <div className="glass rounded-xl p-4 space-y-3">
              <span className="text-xs text-surface-200 font-semibold block">Resolution</span>
              <div className="grid grid-cols-3 gap-1.5">
                {["1080p", "2K", "4K"].map(r => (
                  <button key={r} onClick={() => setResolution(r)}
                    className={`py-1.5 rounded-lg text-xs font-medium transition ${
                      resolution === r ? "bg-brand-500 text-white" : "bg-surface-700 text-surface-200 hover:text-white"
                    }`}>{r}</button>
                ))}
              </div>
              <span className="text-xs text-surface-200 font-semibold block mt-2">Quality</span>
              <div className="grid grid-cols-3 gap-1.5">
                {[{ id: "standard", icon: "⚡" }, { id: "high", icon: "🎯" }, { id: "ultra", icon: "💎" }].map(q => (
                  <button key={q.id} onClick={() => setQuality(q.id)}
                    className={`py-2 rounded-lg text-xs font-medium transition text-center ${
                      quality === q.id ? "bg-brand-500/20 border border-brand-500/40 text-brand-400" : "bg-surface-700 text-surface-200 hover:text-white"
                    }`}>{q.icon} {q.id.charAt(0).toUpperCase() + q.id.slice(1)}</button>
                ))}
              </div>
            </div>

            {/* Toggles */}
            <div className="glass rounded-xl p-4 space-y-3">
              <Toggle on={includeNarration} onToggle={() => setIncludeNarration(!includeNarration)} label="AI Narration" sub="Auto voiceover" />
              {includeNarration && (
                <div className="grid grid-cols-2 gap-1.5">
                  {voices.map(v => (
                    <button key={v.id} onClick={() => setVoice(v.id)}
                      className={`px-2 py-1.5 rounded-lg text-left transition ${
                        voice === v.id ? "bg-brand-500/15 border border-brand-500/25" : "bg-surface-700"
                      }`}>
                      <span className="text-[11px] font-medium text-white block">{v.name}</span>
                      <span className="text-[9px] text-surface-300">{v.desc}</span>
                    </button>
                  ))}
                </div>
              )}
              <Toggle on={includeMusic} onToggle={() => setIncludeMusic(!includeMusic)} label="Background Music" sub="AI soundtrack" />
              <Toggle on={enableLipSync} onToggle={() => setEnableLipSync(!enableLipSync)} label="Lip Sync AI" sub="Ominou Sync Engine" />
            </div>

            {/* Publish */}
            <div className="glass rounded-xl p-4 space-y-2">
              <span className="text-xs text-surface-200 font-semibold block">Auto-Publish</span>
              <div className="grid grid-cols-3 gap-1.5">
                {publishPlatforms.map(p => (
                  <button key={p.id} onClick={() => togglePlatform(p.id)}
                    className={`py-1.5 rounded-lg text-[11px] font-medium transition ${
                      publishTo.includes(p.id) ? "bg-accent-green/15 border border-accent-green/30 text-accent-green" : "bg-surface-700 text-surface-200 hover:text-white"
                    }`}>{p.icon} {p.name}</button>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <button onClick={() => handleGenerate(script || chatMessages.filter(m => m.role === "user").pop()?.content || chatInput)}
              disabled={loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500 hover:from-brand-600 hover:via-purple-600 hover:to-pink-600 text-white font-semibold text-sm disabled:opacity-50 transition shadow-lg shadow-brand-500/20">
              {loading ? "⏳ Generating..." : `🎬 Generate ${duration === -1 ? (customDuration ? customDuration + "s" : "") : duration >= 60 ? Math.floor(duration / 60) + " min" : duration + "s"} ${style} Video — 25 Credits`}
            </button>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
         TAB: CLONE LAB
         ════════════════════════════════════════════════════════ */}
      {activeTab === "clone" && (
        <div className="max-w-4xl mx-auto space-y-5">
          <div className="flex gap-2 justify-center">
            <button onClick={() => setCloneType("voice")}
              className={`px-6 py-3 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
                cloneType === "voice" ? "bg-brand-500/15 text-brand-400 border border-brand-500/25 shadow-sm" : "glass text-surface-300 hover:text-white"
              }`}>🎙️ Voice Cloning</button>
            <button onClick={() => setCloneType("face")}
              className={`px-6 py-3 rounded-xl text-sm font-medium transition flex items-center gap-2 ${
                cloneType === "face" ? "bg-brand-500/15 text-brand-400 border border-brand-500/25 shadow-sm" : "glass text-surface-300 hover:text-white"
              }`}>🎭 Face Cloning</button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Upload Section */}
            <div className="glass rounded-xl p-6 space-y-5">
              <h3 className="text-sm font-semibold text-surface-100">
                {cloneType === "voice" ? "Upload Voice Sample" : "Upload Face Reference"}
              </h3>
              <div className="border-2 border-dashed border-surface-600 rounded-xl p-8 text-center hover:border-brand-500/40 transition cursor-pointer">
                <p className="text-4xl mb-3">{cloneType === "voice" ? "🎙️" : "🖼️"}</p>
                <p className="text-sm text-surface-200 font-medium">
                  {cloneType === "voice" ? "Drop audio file or record" : "Drop face image"}
                </p>
                <p className="text-xs text-surface-400 mt-1">
                  {cloneType === "voice" ? "WAV, MP3 — 10s to 5min recommended" : "PNG, JPG — clear front-facing photo"}
                </p>
              </div>
              {cloneType === "voice" && (
                <button className="w-full py-3 rounded-lg glass text-surface-200 text-sm font-medium hover:text-white transition flex items-center justify-center gap-2">
                  🔴 Record Voice Sample
                </button>
              )}
            </div>

            {/* Target Section */}
            <div className="glass rounded-xl p-6 space-y-5">
              <h3 className="text-sm font-semibold text-surface-100">
                {cloneType === "voice" ? "Target: Text to Speak" : "Target: Video for Face Swap"}
              </h3>
              {cloneType === "voice" ? (
                <textarea placeholder="Type or paste the text you want the cloned voice to speak..."
                  className="w-full h-40 bg-surface-800 border border-surface-600 rounded-lg p-3 text-white text-sm placeholder:text-surface-400 resize-none focus:outline-none focus:border-brand-500" />
              ) : (
                <div className="border-2 border-dashed border-surface-600 rounded-xl p-8 text-center hover:border-brand-500/40 transition cursor-pointer">
                  <p className="text-4xl mb-3">📹</p>
                  <p className="text-sm text-surface-200 font-medium">Drop source video</p>
                  <p className="text-xs text-surface-400 mt-1">MP4, MOV — up to 500MB</p>
                </div>
              )}
              <button className="w-full py-3 rounded-xl bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500 text-white font-semibold text-sm shadow-lg shadow-brand-500/20 transition hover:from-brand-600 hover:via-purple-600 hover:to-pink-600">
                {cloneType === "voice" ? "🎙️ Clone & Speak — 15 Credits" : "🎭 Swap Face — 15 Credits"}
              </button>
            </div>
          </div>

          {/* Clone Preview */}
          <div className="glass rounded-xl p-6">
            <h3 className="text-sm font-semibold text-surface-100 mb-3">Preview</h3>
            <div className="aspect-video bg-surface-900 rounded-lg flex items-center justify-center">
              <div className="text-center text-surface-400">
                <p className="text-4xl mb-2">{cloneType === "voice" ? "🎙️" : "🎭"}</p>
                <p className="text-sm">Clone result will appear here</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════
         TAB: AI CREW
         ════════════════════════════════════════════════════════ */}
      {activeTab === "crew" && (
        <div className="max-w-5xl mx-auto space-y-5">
          <div className="text-center mb-2">
            <p className="text-surface-300 text-sm">Your virtual production team — 7 AI specialists working together</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {crew.map((c, i) => (
              <div key={c.id} className="glass rounded-xl p-5 card-hover slide-up" style={{ animationDelay: `${i * 80}ms` }}>
                <div className="flex items-start gap-3">
                  <div className={`avatar-ring flex-shrink-0 ${c.status === "active" ? "animate-pulse" : ""}`}>
                    <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${c.color} flex items-center justify-center text-xl`}>
                      {c.icon}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-white">{c.name}</h3>
                    <p className="text-[11px] text-surface-300 leading-snug">{c.role}</p>
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <span className={`text-[10px] font-semibold uppercase tracking-wider ${
                    c.status === "active" ? "text-brand-400" : c.status === "done" ? "text-accent-green" : "text-surface-400"
                  }`}>
                    {c.status === "active" ? "● Working" : c.status === "done" ? "✓ Complete" : "○ Standby"}
                  </span>
                  {c.status === "active" && (
                    <div className="flex gap-0.5">
                      <span className="w-1 h-1 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-1 h-1 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-1 h-1 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Crew Pipeline View */}
          <div className="glass rounded-xl p-6">
            <h3 className="text-sm font-semibold text-surface-100 mb-4">Production Pipeline</h3>
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {["Scriptwriter", "Director", "DOP", "VFX Artist", "Graphic Designer", "Music Director", "Choreographer"].map((name, i) => {
                const member = crew.find(c => c.name === name) || crew[i];
                return (
                  <div key={name} className="flex items-center gap-2 flex-shrink-0">
                    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all ${
                      member?.status === "active" ? "bg-brand-500/10 border-brand-500/30 shadow-sm shadow-brand-500/10" :
                      member?.status === "done" ? "bg-accent-green/5 border-accent-green/20" :
                      "bg-surface-800 border-surface-600"
                    }`}>
                      <span className="text-sm">{member?.icon}</span>
                      <span className={`text-[11px] font-medium ${
                        member?.status === "active" ? "text-brand-400" : member?.status === "done" ? "text-accent-green" : "text-surface-400"
                      }`}>{name}</span>
                    </div>
                    {i < 6 && <span className="text-surface-500 text-xs">→</span>}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Start from Crew */}
          <div className="text-center">
            <button onClick={() => setActiveTab("studio")}
              className="px-8 py-3 rounded-xl bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500 text-white font-semibold text-sm shadow-lg shadow-brand-500/20 transition hover:from-brand-600 hover:via-purple-600 hover:to-pink-600">
              🎬 Start Production → Film Studio
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
