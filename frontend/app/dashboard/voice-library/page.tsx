"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Video,
  Mic,
  Camera,
  Play,
  Pause,
  Trash2,
  Upload,
  Clock,
  Globe,
} from "lucide-react";

interface VoiceProfile {
  id: string;
  name: string;
  language: string;
  duration: string;
  created_at: string;
  samples: number;
}

const DEMO_VOICES: VoiceProfile[] = [
  {
    id: "v1",
    name: "My English Voice",
    language: "English",
    duration: "2m 15s",
    created_at: "2 days ago",
    samples: 3,
  },
  {
    id: "v2",
    name: "Professional Narration",
    language: "English",
    duration: "1m 45s",
    created_at: "1 week ago",
    samples: 2,
  },
  {
    id: "v3",
    name: "Spanish Voice Clone",
    language: "Spanish",
    duration: "1m 30s",
    created_at: "2 weeks ago",
    samples: 1,
  },
];

export default function VoiceLibraryPage() {
  const [voices] = useState<VoiceProfile[]>(DEMO_VOICES);
  const [playing, setPlaying] = useState<string | null>(null);

  return (
    <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Voice Library</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Manage your cloned voice profiles
            </p>
          </div>
          <Link
            href="/dashboard/create"
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-xl font-semibold text-sm hover:bg-primary/90 transition"
          >
            <Upload className="w-4 h-4" />
            New Voice
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <Mic className="w-4 h-4" />
              <span className="text-xs font-medium">Total Voices</span>
            </div>
            <p className="text-2xl font-bold">{voices.length}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <Globe className="w-4 h-4" />
              <span className="text-xs font-medium">Languages</span>
            </div>
            <p className="text-2xl font-bold">
              {new Set(voices.map((v) => v.language)).size}
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <Clock className="w-4 h-4" />
              <span className="text-xs font-medium">Total Samples</span>
            </div>
            <p className="text-2xl font-bold">
              {voices.reduce((a, v) => a + v.samples, 0)}
            </p>
          </div>
        </div>

        {/* Voice list */}
        <div className="space-y-3">
          {voices.map((voice) => (
            <div
              key={voice.id}
              className="bg-card border border-border rounded-xl p-5 flex items-center gap-4 hover:border-primary/30 transition group"
            >
              {/* Icon */}
              <div className="w-14 h-14 bg-gradient-to-br from-primary/20 to-cyan-400/20 rounded-xl flex items-center justify-center flex-shrink-0">
                <Mic className="w-6 h-6 text-primary/60" />
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{voice.name}</p>
                <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Globe className="w-3 h-3" />
                    {voice.language}
                  </span>
                  <span>{voice.duration}</span>
                  <span>{voice.samples} sample{voice.samples !== 1 ? "s" : ""}</span>
                  <span>{voice.created_at}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPlaying(playing === voice.id ? null : voice.id)}
                  className="p-2.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition"
                  title="Play sample"
                >
                  {playing === voice.id ? (
                    <Pause className="w-4 h-4" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                </button>
                <button
                  className="p-2.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition opacity-0 group-hover:opacity-100"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
    </div>
  );
}
