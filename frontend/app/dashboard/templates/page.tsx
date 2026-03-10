"use client";

import { useEffect, useState } from "react";
import { templates as templatesApi } from "@/lib/api";
import { useCloneStore } from "@/lib/store";
import type { Template } from "@/lib/api";
import { useRouter } from "next/navigation";
import {
  Layout,
  Search,
  X,
  Play,
  ArrowRight,
  Loader2,
  Tag,
} from "lucide-react";

const CATEGORIES = ["All", "Marketing", "Education", "Social", "Business", "Entertainment"];

export default function TemplatesPage() {
  const [allTemplates, setAllTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [preview, setPreview] = useState<Template | null>(null);
  const applyTemplate = useCloneStore((s) => s.applyTemplate);
  const router = useRouter();

  useEffect(() => {
    async function load() {
      try {
        const list = await templatesApi.list();
        setAllTemplates(list);
      } catch {
        // Demo built-in templates
        setAllTemplates([
          {
            id: "builtin-product-demo",
            name: "Product Demo",
            description: "Professional product walkthrough video",
            category: "Marketing",
            script_text: "Welcome! Let me show you the amazing features of our product...",
            language: "en",
            emotion: "confident",
            background: "office",
            tags: ["marketing", "product", "demo"],
            is_builtin: true,
          },
          {
            id: "builtin-course-intro",
            name: "Course Intro",
            description: "Engaging online course introduction",
            category: "Education",
            script_text: "Welcome to this course! Over the next few modules...",
            language: "en",
            emotion: "friendly",
            background: "classroom",
            tags: ["education", "course", "intro"],
            is_builtin: true,
          },
          {
            id: "builtin-linkedin-post",
            name: "LinkedIn Post",
            description: "Professional LinkedIn video post",
            category: "Social",
            script_text: "I wanted to share something important with my network...",
            language: "en",
            emotion: "professional",
            background: "minimal",
            tags: ["social", "linkedin", "professional"],
            is_builtin: true,
          },
          {
            id: "builtin-youtube-intro",
            name: "YouTube Intro",
            description: "Eye-catching YouTube channel introduction",
            category: "Entertainment",
            script_text: "Hey everyone! Welcome back to the channel...",
            language: "en",
            emotion: "energetic",
            background: "studio",
            tags: ["youtube", "intro", "entertainment"],
            is_builtin: true,
          },
          {
            id: "builtin-cold-outreach",
            name: "Cold Outreach",
            description: "Personalized sales outreach video",
            category: "Business",
            script_text: "Hi there! I noticed your company is doing incredible work...",
            language: "en",
            emotion: "warm",
            background: "office",
            tags: ["sales", "outreach", "business"],
            is_builtin: true,
          },
          {
            id: "builtin-team-announcement",
            name: "Team Announcement",
            description: "Internal team update video",
            category: "Business",
            script_text: "Team, I have an exciting update to share with you all...",
            language: "en",
            emotion: "upbeat",
            background: "boardroom",
            tags: ["team", "announcement", "internal"],
            is_builtin: true,
          },
          {
            id: "builtin-news-update",
            name: "News Update",
            description: "Professional news-style update",
            category: "Entertainment",
            script_text: "Good evening. Here are today's top headlines...",
            language: "en",
            emotion: "neutral",
            background: "newsroom",
            tags: ["news", "update", "broadcast"],
            is_builtin: true,
          },
          {
            id: "builtin-tutorial",
            name: "Tutorial",
            description: "Step-by-step tutorial video",
            category: "Education",
            script_text: "In this tutorial, I'll walk you through the process step by step...",
            language: "en",
            emotion: "friendly",
            background: "screen-share",
            tags: ["tutorial", "howto", "education"],
            is_builtin: true,
          },
        ]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = allTemplates.filter((t) => {
    if (category !== "All" && t.category !== category) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.tags.some((tag) => tag.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const handleUseTemplate = (template: Template) => {
    applyTemplate({
      script_text: template.script_text,
      language: template.language,
      emotion: template.emotion,
      background: template.background,
    });
    router.push("/dashboard/create");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Templates</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Start fast with pre-built video templates
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search templates..."
            className="w-full pl-10 pr-4 py-2.5 bg-card border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
        <div className="flex items-center gap-1 bg-card border border-border rounded-xl p-1">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-3 py-1.5 text-xs rounded-lg transition ${
                category === cat
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Template grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((t) => (
          <div
            key={t.id}
            className="bg-card border border-border rounded-xl p-5 hover:border-primary/30 transition group cursor-pointer"
            onClick={() => setPreview(t)}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-cyan-400/20 flex items-center justify-center">
                <Layout className="w-5 h-5 text-primary" />
              </div>
              {t.is_builtin && (
                <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-primary/10 text-primary">
                  BUILT-IN
                </span>
              )}
            </div>
            <h3 className="font-semibold text-sm mb-1">{t.name}</h3>
            <p className="text-muted-foreground text-xs mb-3 line-clamp-2">
              {t.description}
            </p>
            <div className="flex items-center gap-1.5 flex-wrap">
              {t.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 bg-secondary text-muted-foreground text-[10px] rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16 bg-card border border-border rounded-xl">
          <Layout className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground text-sm">No templates found</p>
        </div>
      )}

      {/* Preview modal */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-card border border-border rounded-2xl max-w-lg w-full p-6 space-y-4 relative">
            <button
              onClick={() => setPreview(null)}
              title="Close preview"
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
            >
              <X className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-xl font-bold">{preview.name}</h2>
              <p className="text-muted-foreground text-sm mt-1">{preview.description}</p>
            </div>
            <div className="bg-secondary/50 rounded-xl p-4 text-sm leading-relaxed max-h-40 overflow-y-auto">
              {preview.script_text}
            </div>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3" /> {preview.category}
              </span>
              <span>Language: {preview.language}</span>
              <span>Emotion: {preview.emotion}</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  handleUseTemplate(preview);
                  setPreview(null);
                }}
                className="flex-1 flex items-center justify-center gap-2 py-3 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition"
              >
                <ArrowRight className="w-4 h-4" />
                Use This Template
              </button>
              <button
                onClick={() => setPreview(null)}
                className="px-5 py-3 border border-border rounded-xl text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
