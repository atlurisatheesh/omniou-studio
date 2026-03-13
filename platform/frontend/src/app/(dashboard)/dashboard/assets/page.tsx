"use client";
import { useState } from "react";

type AssetType = "all" | "image" | "audio" | "video" | "code" | "document";

const mockAssets = [
  { id: 1, name: "hero-banner.png", type: "image" as const, size: "2.4 MB", studio: "Design Studio", created: "2 hours ago", preview: "🖼️" },
  { id: 2, name: "podcast-intro.wav", type: "audio" as const, size: "8.1 MB", studio: "Music Studio", created: "5 hours ago", preview: "🎵" },
  { id: 3, name: "product-demo.mp4", type: "video" as const, size: "45 MB", studio: "Video Studio", created: "1 day ago", preview: "🎬" },
  { id: 4, name: "api-server.py", type: "code" as const, size: "12 KB", studio: "Code Studio", created: "1 day ago", preview: "💻" },
  { id: 5, name: "blog-post.md", type: "document" as const, size: "4.2 KB", studio: "AI Writer", created: "2 days ago", preview: "📝" },
  { id: 6, name: "voiceover-en.mp3", type: "audio" as const, size: "3.8 MB", studio: "Voice Studio", created: "2 days ago", preview: "🎤" },
  { id: 7, name: "social-post-ig.png", type: "image" as const, size: "1.1 MB", studio: "Design Studio", created: "3 days ago", preview: "🖼️" },
  { id: 8, name: "landing-page.tsx", type: "code" as const, size: "8 KB", studio: "Code Studio", created: "3 days ago", preview: "💻" },
  { id: 9, name: "jingle-v2.wav", type: "audio" as const, size: "5.2 MB", studio: "Music Studio", created: "4 days ago", preview: "🎵" },
  { id: 10, name: "explainer.mp4", type: "video" as const, size: "120 MB", studio: "Video Studio", created: "5 days ago", preview: "🎬" },
];

export default function AssetsPage() {
  const [filter, setFilter] = useState<AssetType>("all");
  const [search, setSearch] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");

  const filtered = mockAssets.filter((a) => {
    if (filter !== "all" && a.type !== filter) return false;
    if (search && !a.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const totalSize = "198.8 MB";

  return (
    <div className="max-w-6xl mx-auto space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">📁 Assets</h1>
          <p className="text-surface-500 mt-1">All your generated files in one place</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-surface-400">{mockAssets.length} files</p>
          <p className="text-xs text-surface-500">{totalSize} used</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex gap-2">
          {(["all", "image", "audio", "video", "code", "document"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-3 py-1.5 rounded-lg text-sm transition ${
                filter === t ? "bg-brand-600 text-white" : "bg-[#1a1a2e] text-surface-500 hover:text-white"
              }`}
            >
              {t === "all" ? "All" : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex-1" />

        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search files..."
          className="bg-[#12121a] border border-[#2a2a4a] rounded-lg px-3 py-1.5 text-white text-sm placeholder:text-surface-600 w-48 focus:outline-none focus:border-brand-500"
        />

        <div className="flex gap-1">
          <button
            onClick={() => setView("grid")}
            className={`p-2 rounded ${view === "grid" ? "text-white bg-[#2a2a4a]" : "text-surface-500"}`}
          >
            ▦
          </button>
          <button
            onClick={() => setView("list")}
            className={`p-2 rounded ${view === "list" ? "text-white bg-[#2a2a4a]" : "text-surface-500"}`}
          >
            ☰
          </button>
        </div>
      </div>

      {/* Assets */}
      {view === "grid" ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {filtered.map((asset) => (
            <div key={asset.id} className="glass rounded-xl p-4 card-hover cursor-pointer group">
              <div className="aspect-square bg-[#0a0a0f] rounded-lg flex items-center justify-center mb-3">
                <span className="text-4xl">{asset.preview}</span>
              </div>
              <p className="text-sm text-white font-medium truncate">{asset.name}</p>
              <div className="flex items-center justify-between mt-1">
                <p className="text-xs text-surface-500">{asset.size}</p>
                <p className="text-xs text-surface-600">{asset.created}</p>
              </div>
              <div className="opacity-0 group-hover:opacity-100 flex gap-2 mt-2 transition">
                <button className="flex-1 py-1 rounded text-xs bg-brand-600/20 text-brand-400">💾</button>
                <button className="flex-1 py-1 rounded text-xs bg-[#1a1a2e] text-surface-400">🗑️</button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((asset) => (
            <div key={asset.id} className="glass rounded-lg p-3 flex items-center gap-4 card-hover cursor-pointer">
              <span className="text-2xl w-10 text-center">{asset.preview}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white font-medium truncate">{asset.name}</p>
                <p className="text-xs text-surface-500">{asset.studio}</p>
              </div>
              <p className="text-xs text-surface-500 w-20 text-right">{asset.size}</p>
              <p className="text-xs text-surface-600 w-24 text-right">{asset.created}</p>
              <div className="flex gap-2">
                <button className="px-2 py-1 rounded text-xs bg-brand-600/20 text-brand-400">💾</button>
                <button className="px-2 py-1 rounded text-xs bg-[#1a1a2e] text-surface-400">🗑️</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {filtered.length === 0 && (
        <div className="glass rounded-xl p-12 text-center">
          <p className="text-4xl mb-3">📁</p>
          <p className="text-surface-400">No files found</p>
          <p className="text-sm text-surface-500 mt-1">Try changing your filter or search term</p>
        </div>
      )}
    </div>
  );
}
