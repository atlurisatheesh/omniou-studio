"use client";

import { useState, useEffect } from "react";
import { useCloneStore } from "@/lib/store";
import { getLanguages } from "@/lib/api";
import { ArrowLeft, ArrowRight, Globe, FileText } from "lucide-react";

const DEFAULT_LANGUAGES = [
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "hi", name: "Hindi" },
  { code: "ar", name: "Arabic" },
  { code: "zh", name: "Chinese" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "ru", name: "Russian" },
  { code: "tr", name: "Turkish" },
  { code: "pl", name: "Polish" },
  { code: "nl", name: "Dutch" },
  { code: "cs", name: "Czech" },
  { code: "hu", name: "Hungarian" },
];

export function StepWriteScript() {
  const { scriptText, targetLanguage, setScript, setLanguage, setStep } = useCloneStore();
  const [languages, setLanguages] = useState(DEFAULT_LANGUAGES);
  const charCount = scriptText.length;
  const wordCount = scriptText.trim() ? scriptText.trim().split(/\s+/).length : 0;

  useEffect(() => {
    getLanguages()
      .then((langs) => {
        if (langs.length > 0) setLanguages(langs);
      })
      .catch(() => {
        // Use defaults
      });
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2">Write Your Script</h1>
        <p className="text-muted-foreground text-sm">
          Type what you want your AI clone to say. It will speak in your cloned voice.
        </p>
      </div>

      {/* Language selector */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium mb-2">
          <Globe className="w-4 h-4 text-primary" />
          Output Language
        </label>
        <select
          value={targetLanguage}
          onChange={(e) => setLanguage(e.target.value)}
          title="Output language"
          className="w-full bg-card border border-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          {languages.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.name} ({lang.code})
            </option>
          ))}
        </select>
      </div>

      {/* Script textarea */}
      <div>
        <label className="flex items-center gap-2 text-sm font-medium mb-2">
          <FileText className="w-4 h-4 text-primary" />
          Your Script
        </label>
        <textarea
          value={scriptText}
          onChange={(e) => setScript(e.target.value)}
          placeholder="Type what you want your clone to say..."
          maxLength={5000}
          rows={8}
          className="w-full bg-card border border-border rounded-xl px-4 py-3 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
        />
        <div className="flex justify-between mt-2 text-xs text-muted-foreground">
          <span>{wordCount} words • ~{Math.ceil(wordCount / 2.5)}s audio</span>
          <span className={charCount > 4500 ? "text-red-400" : ""}>{charCount}/5000</span>
        </div>
      </div>

      {/* Template scripts */}
      <div>
        <p className="text-xs uppercase tracking-widest text-muted-foreground mb-3">
          Quick Templates
        </p>
        <div className="grid grid-cols-2 gap-2">
          {[
            {
              label: "Product Demo",
              text: "Hey there! Welcome to our product demo. Today I'm going to show you how our AI-powered tool can help you create amazing content in minutes, not hours. Let me walk you through the key features.",
            },
            {
              label: "YouTube Intro",
              text: "What's up everyone! Welcome back to the channel. In today's video, we're going to dive deep into something really exciting. Make sure you hit that subscribe button and let's get started!",
            },
            {
              label: "Course Lesson",
              text: "Hello students! In this lesson, we'll be covering the fundamentals of machine learning. By the end of this module, you'll understand how neural networks process information and make predictions.",
            },
            {
              label: "Social Media",
              text: "I just discovered something incredible and I had to share it with you all. This free AI tool literally clones your voice and face in seconds. No watermark. No subscription. Let me show you how.",
            },
          ].map((t) => (
            <button
              key={t.label}
              onClick={() => setScript(t.text)}
              className="p-3 bg-card border border-border rounded-lg text-left hover:border-primary/30 transition text-xs"
            >
              <span className="font-medium text-foreground">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex gap-3">
        <button
          onClick={() => setStep("voice")}
          className="flex items-center gap-2 px-6 py-3 border border-border rounded-xl text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <button
          onClick={() => setStep("settings")}
          disabled={scriptText.trim().length < 10}
          className="flex-1 flex items-center justify-center gap-2 py-3 bg-primary text-primary-foreground font-semibold rounded-xl disabled:opacity-30 disabled:cursor-not-allowed hover:bg-primary/90 transition"
        >
          Next: Settings
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
