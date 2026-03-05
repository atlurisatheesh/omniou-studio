"use client";

import { useState } from "react";
import { useCloneStore } from "@/lib/store";
import {
  ArrowLeft,
  ArrowRight,
  Smile,
  Frown,
  Meh,
  Angry,
  Heart,
  Zap,
  Image,
  Palette,
} from "lucide-react";

const EMOTIONS = [
  { id: "neutral", label: "Neutral", icon: Meh, color: "text-gray-400" },
  { id: "happy", label: "Happy", icon: Smile, color: "text-yellow-400" },
  { id: "sad", label: "Sad", icon: Frown, color: "text-blue-400" },
  { id: "angry", label: "Angry", icon: Angry, color: "text-red-400" },
  { id: "excited", label: "Excited", icon: Zap, color: "text-orange-400" },
  { id: "loving", label: "Loving", icon: Heart, color: "text-pink-400" },
];

const BACKGROUNDS = [
  { id: "original", label: "Original", preview: "bg-gradient-to-br from-gray-800 to-gray-900" },
  { id: "blur", label: "Blurred", preview: "bg-gradient-to-br from-blue-900/50 to-purple-900/50 backdrop-blur" },
  { id: "office", label: "Office", preview: "bg-gradient-to-br from-amber-900/30 to-stone-900" },
  { id: "studio", label: "Studio", preview: "bg-gradient-to-br from-neutral-900 to-neutral-800" },
  { id: "green_screen", label: "Green Screen", preview: "bg-green-600" },
  { id: "gradient", label: "Gradient", preview: "bg-gradient-to-br from-primary/30 to-cyan-500/30" },
];

export function StepSettingsExtra() {
  const { setStep } = useCloneStore();
  const [emotion, setEmotion] = useState("neutral");
  const [background, setBackground] = useState("original");

  // Store these in zustand — we extend the store in the next step
  // For now, we store in local state and pass via a custom event or context

  const handleNext = () => {
    // Dispatch settings to store
    if (typeof window !== "undefined") {
      (window as any).__cloneai_extra = { emotion, background };
    }
    setStep("generating");
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2">Fine-Tune Your Video</h1>
        <p className="text-muted-foreground text-sm">
          Choose the emotion and background for your AI clone video.
        </p>
      </div>

      {/* Emotion Selector */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium mb-3">
          <Palette className="w-4 h-4 text-primary" />
          Emotion
        </label>
        <div className="grid grid-cols-3 gap-3">
          {EMOTIONS.map((e) => {
            const Icon = e.icon;
            const selected = emotion === e.id;
            return (
              <button
                key={e.id}
                onClick={() => setEmotion(e.id)}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition ${
                  selected
                    ? "border-primary bg-primary/10 ring-2 ring-primary/30"
                    : "border-border bg-card hover:border-primary/50"
                }`}
              >
                <Icon className={`w-6 h-6 ${e.color}`} />
                <span className="text-xs font-medium">{e.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Background Selector */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium mb-3">
          <Image className="w-4 h-4 text-primary" />
          Background
        </label>
        <div className="grid grid-cols-3 gap-3">
          {BACKGROUNDS.map((bg) => {
            const selected = background === bg.id;
            return (
              <button
                key={bg.id}
                onClick={() => setBackground(bg.id)}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition ${
                  selected
                    ? "border-primary ring-2 ring-primary/30"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className={`w-12 h-12 rounded-lg ${bg.preview}`} />
                <span className="text-xs font-medium">{bg.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setStep("script")}
          className="px-6 py-3 text-sm font-medium text-muted-foreground hover:text-foreground border border-border rounded-xl transition flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={handleNext}
          className="px-8 py-3 text-sm font-semibold bg-gradient-to-r from-primary to-cyan-400 text-white rounded-xl hover:opacity-90 transition flex items-center gap-2 shadow-lg shadow-primary/25"
        >
          Generate
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
