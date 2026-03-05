"use client";

import { useState } from "react";
import { Image, Check } from "lucide-react";

interface BackgroundSelectorProps {
  value: string;
  onChange: (bg: string) => void;
  className?: string;
}

const BACKGROUNDS = [
  {
    id: "original",
    label: "Original",
    description: "Keep the original background",
    preview: "bg-gradient-to-br from-gray-800 to-gray-900",
  },
  {
    id: "blur",
    label: "Blurred",
    description: "Soft blur on background",
    preview: "bg-gradient-to-br from-blue-900/50 to-purple-900/50",
  },
  {
    id: "office",
    label: "Office",
    description: "Professional office setting",
    preview: "bg-gradient-to-br from-amber-900/30 to-stone-900",
  },
  {
    id: "studio",
    label: "Studio",
    description: "Clean studio backdrop",
    preview: "bg-gradient-to-br from-neutral-900 to-neutral-800",
  },
  {
    id: "green_screen",
    label: "Green Screen",
    description: "Solid green for editing",
    preview: "bg-green-600",
  },
  {
    id: "gradient",
    label: "Gradient",
    description: "Modern gradient backdrop",
    preview: "bg-gradient-to-br from-violet-600/40 to-cyan-500/40",
  },
  {
    id: "remove",
    label: "Transparent",
    description: "Remove background entirely",
    preview: "bg-[conic-gradient(#333_25%,#555_0,#555_50%,#333_0,#333_75%,#555_0)] bg-[length:16px_16px]",
  },
];

export function BackgroundSelector({ value, onChange, className = "" }: BackgroundSelectorProps) {
  return (
    <div className={`space-y-3 ${className}`}>
      <label className="flex items-center gap-2 text-sm font-medium">
        <Image className="w-4 h-4 text-primary" />
        Background
      </label>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {BACKGROUNDS.map((bg) => {
          const selected = value === bg.id;
          return (
            <button
              key={bg.id}
              onClick={() => onChange(bg.id)}
              className={`relative flex flex-col items-center gap-2 p-3 rounded-xl border transition ${
                selected
                  ? "border-primary bg-primary/5 ring-2 ring-primary/30"
                  : "border-border bg-card hover:border-primary/50"
              }`}
            >
              {selected && (
                <div className="absolute top-2 right-2">
                  <Check className="w-3.5 h-3.5 text-primary" />
                </div>
              )}
              <div className={`w-full aspect-video rounded-lg ${bg.preview}`} />
              <span className="text-xs font-medium">{bg.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
