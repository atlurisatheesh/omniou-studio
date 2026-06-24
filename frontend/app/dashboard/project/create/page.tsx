"use client";

/**
 * CLONEAI PRO — Create Long-Form Video Project
 * 6-step wizard: Avatar → Identity Preview → Script → Scene Review → Settings → Generate
 */

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { project, uploadPhoto, uploadVoice } from "@/lib/api";

const EMOTIONS = ["neutral", "happy", "serious", "excited", "professional"];
const BACKGROUNDS = ["original", "blur", "studio", "office", "custom"];
const SPLIT_METHODS = [
  { value: "sentence_group", label: "Auto (Sentence Groups)" },
  { value: "paragraph", label: "By Paragraphs" },
  { value: "ai", label: "AI-Powered (Best)" },
];

export default function CreateProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Avatar
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPath, setPhotoPath] = useState("");
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [voiceFile, setVoiceFile] = useState<File | null>(null);
  const [voicePath, setVoicePath] = useState("");

  // Step 3: Script
  const [projectName, setProjectName] = useState("My Long-Form Video");
  const [scriptText, setScriptText] = useState("");
  const [targetDuration, setTargetDuration] = useState(3);

  // Step 4: Scene Review (populated after analysis)
  const [scenes, setScenes] = useState<any[]>([]);

  // Step 5: Settings
  const [defaultEmotion, setDefaultEmotion] = useState("neutral");
  const [background, setBackground] = useState("original");
  const [splitMethod, setSplitMethod] = useState("sentence_group");
  const [transitionType, setTransitionType] = useState("crossfade");
  const [identityThreshold, setIdentityThreshold] = useState(0.75);
  const [autoCorrect, setAutoCorrect] = useState(true);

  // Step 6: Result
  const [projectId, setProjectId] = useState<string | null>(null);

  const wordCount = scriptText.trim().split(/\s+/).filter(Boolean).length;
  const estimatedDuration = Math.ceil(wordCount / 2.5);
  const estimatedMinutes = (estimatedDuration / 60).toFixed(1);

  // Upload handlers
  const handlePhotoUpload = useCallback(async (file: File) => {
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
    try {
      const res = await uploadPhoto(file);
      setPhotoPath(res.path);
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  const handleVoiceUpload = useCallback(async (file: File) => {
    setVoiceFile(file);
    try {
      const res = await uploadVoice(file);
      setVoicePath(res.path);
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  // Create project (submits to backend which analyzes script + creates anchor)
  const handleCreateProject = async () => {
    if (!photoPath || !scriptText.trim()) return;
    
    setLoading(true);
    setError(null);

    try {
      const result = await project.create({
        name: projectName,
        script_text: scriptText,
        target_duration_minutes: targetDuration,
        avatar_config: {
          photo_path: photoPath,
          voice_path: voicePath || undefined,
        },
        consistency_settings: {
          identity_threshold: identityThreshold,
          auto_correct: autoCorrect,
        },
        settings: {
          scene_split_method: splitMethod,
          transition_type: transitionType,
          default_emotion: defaultEmotion,
          background: background,
        },
      });

      setProjectId(result.id);
      setScenes(result.scenes || []);
      setStep(4); // Jump to scene review
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Start generation
  const handleGenerate = async () => {
    if (!projectId) return;
    
    setLoading(true);
    try {
      await project.generate(projectId);
      router.push(`/dashboard/project/${projectId}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950 text-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
            Create Long-Form Video
          </h1>
          <p className="mt-2 text-gray-400">
            Generate identity-locked videos from 1 to 10 minutes
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-2 mb-12">
          {["Avatar", "Script", "Analyze", "Scenes", "Settings", "Generate"].map((label, i) => (
            <div key={i} className="flex items-center gap-2">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                  step > i + 1
                    ? "bg-green-500 text-white"
                    : step === i + 1
                    ? "bg-purple-500 text-white ring-2 ring-purple-300"
                    : "bg-gray-800 text-gray-500"
                }`}
              >
                {step > i + 1 ? "✓" : i + 1}
              </div>
              {i < 5 && (
                <div className={`w-8 h-0.5 ${step > i + 1 ? "bg-green-500" : "bg-gray-700"}`} />
              )}
            </div>
          ))}
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Step 1: Avatar Upload */}
        {step === 1 && (
          <div className="space-y-8">
            <div className="bg-gray-800/50 backdrop-blur rounded-2xl border border-gray-700/50 p-8">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <span className="text-3xl">📸</span>Upload Your Photo
              </h2>
              <div className="border-2 border-dashed border-gray-600 rounded-xl p-10 text-center hover:border-purple-500/50 transition-colors">
                {photoPreview ? (
                  <div className="flex flex-col items-center gap-4">
                    <img src={photoPreview} alt="Preview" className="w-48 h-48 rounded-2xl object-cover ring-4 ring-purple-500/30" />
                    <p className="text-green-400 font-medium">✅ Photo uploaded</p>
                  </div>
                ) : (
                  <label className="cursor-pointer block">
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => e.target.files?.[0] && handlePhotoUpload(e.target.files[0])}
                    />
                    <div className="text-6xl mb-3">🖼️</div>
                    <p className="text-gray-300 font-medium">Click to upload your face photo</p>
                    <p className="text-gray-500 text-sm mt-1">This will be your character identity for the entire video</p>
                  </label>
                )}
              </div>
            </div>

            <div className="bg-gray-800/50 backdrop-blur rounded-2xl border border-gray-700/50 p-8">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <span className="text-3xl">🎙️</span>Upload Voice Sample
              </h2>
              <div className="border-2 border-dashed border-gray-600 rounded-xl p-10 text-center hover:border-purple-500/50 transition-colors">
                {voiceFile ? (
                  <div className="flex flex-col items-center gap-2">
                    <p className="text-green-400 font-medium">✅ {voiceFile.name}</p>
                    <p className="text-gray-500 text-sm">Voice will be locked across all scenes</p>
                  </div>
                ) : (
                  <label className="cursor-pointer block">
                    <input
                      type="file"
                      accept="audio/*"
                      className="hidden"
                      onChange={(e) => e.target.files?.[0] && handleVoiceUpload(e.target.files[0])}
                    />
                    <div className="text-6xl mb-3">🎤</div>
                    <p className="text-gray-300 font-medium">Click to upload voice sample (min 6 seconds)</p>
                    <p className="text-gray-500 text-sm mt-1">Optional — provides voice consistency across scenes</p>
                  </label>
                )}
              </div>
            </div>

            <button
              onClick={() => setStep(2)}
              disabled={!photoPath}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 font-bold text-lg disabled:opacity-40 hover:opacity-90 transition-all"
            >
              Next → Write Script
            </button>
          </div>
        )}

        {/* Step 2: Script */}
        {step === 2 && (
          <div className="space-y-8">
            <div className="bg-gray-800/50 backdrop-blur rounded-2xl border border-gray-700/50 p-8">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <span className="text-3xl">📝</span> Your Script
              </h2>

              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="Project name..."
                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-xl text-white mb-4 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />

              <textarea
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                placeholder="Paste your full script here... The AI will automatically split it into scenes."
                rows={12}
                className="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-xl text-white resize-y focus:outline-none focus:ring-2 focus:ring-purple-500"
              />

              <div className="flex items-center justify-between mt-4 text-sm text-gray-400">
                <span>{wordCount} words</span>
                <span>~{estimatedMinutes} min estimated duration</span>
              </div>

              <div className="mt-6">
                <label className="block text-sm text-gray-300 mb-2">Target Duration (minutes)</label>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={targetDuration}
                  onChange={(e) => setTargetDuration(Number(e.target.value))}
                  className="w-full accent-purple-500"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>1 min</span>
                  <span className="text-purple-400 font-bold">{targetDuration} min</span>
                  <span>10 min</span>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <button onClick={() => setStep(1)} className="flex-1 py-4 rounded-xl bg-gray-800 font-bold hover:bg-gray-700 transition-all">
                ← Back
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={!scriptText.trim()}
                className="flex-1 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 font-bold disabled:opacity-40 hover:opacity-90 transition-all"
              >
                Next → Settings
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Settings */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="bg-gray-800/50 backdrop-blur rounded-2xl border border-gray-700/50 p-8">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <span className="text-3xl">⚙️</span> Generation Settings
              </h2>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm text-gray-300 mb-2">Default Emotion</label>
                  <select
                    value={defaultEmotion}
                    onChange={(e) => setDefaultEmotion(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white"
                  >
                    {EMOTIONS.map((e) => (
                      <option key={e} value={e}>{e.charAt(0).toUpperCase() + e.slice(1)}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">Background</label>
                  <select
                    value={background}
                    onChange={(e) => setBackground(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white"
                  >
                    {BACKGROUNDS.map((b) => (
                      <option key={b} value={b}>{b.charAt(0).toUpperCase() + b.slice(1)}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">Scene Split Method</label>
                  <select
                    value={splitMethod}
                    onChange={(e) => setSplitMethod(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white"
                  >
                    {SPLIT_METHODS.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-gray-300 mb-2">Transition</label>
                  <select
                    value={transitionType}
                    onChange={(e) => setTransitionType(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white"
                  >
                    <option value="crossfade">Crossfade</option>
                    <option value="cut">Hard Cut</option>
                    <option value="dissolve">Dissolve</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Identity Lock Settings */}
            <div className="bg-gray-800/50 backdrop-blur rounded-2xl border border-purple-500/20 p-8">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <span className="text-3xl">🔒</span> Character Consistency
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-2">
                    Identity Threshold: <span className="text-purple-400 font-bold">{identityThreshold}</span>
                  </label>
                  <input
                    type="range"
                    min={0.5}
                    max={0.95}
                    step={0.05}
                    value={identityThreshold}
                    onChange={(e) => setIdentityThreshold(Number(e.target.value))}
                    className="w-full accent-purple-500"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Relaxed (0.5)</span>
                    <span>Strict (0.95)</span>
                  </div>
                </div>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoCorrect}
                    onChange={(e) => setAutoCorrect(e.target.checked)}
                    className="w-5 h-5 accent-purple-500 rounded"
                  />
                  <span className="text-gray-300">Auto-correct drifted frames</span>
                </label>
              </div>
            </div>

            <div className="flex gap-4">
              <button onClick={() => setStep(2)} className="flex-1 py-4 rounded-xl bg-gray-800 font-bold hover:bg-gray-700 transition-all">
                ← Back
              </button>
              <button
                onClick={handleCreateProject}
                disabled={loading}
                className="flex-1 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 font-bold disabled:opacity-40 hover:opacity-90 transition-all"
              >
                {loading ? "🔍 Analyzing Script & Creating Identity..." : "Analyze Script →"}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Scene Review */}
        {step === 4 && (
          <div className="space-y-6">
            <div className="bg-gray-800/50 backdrop-blur rounded-2xl border border-gray-700/50 p-8">
              <h2 className="text-2xl font-semibold mb-2 flex items-center gap-3">
                <span className="text-3xl">🎬</span> Scene Breakdown
              </h2>
              <p className="text-gray-400 mb-6">
                {scenes.length} scenes • ~{estimatedMinutes} min total • Identity anchor created ✅
              </p>

              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {scenes.map((scene: any, i: number) => (
                  <div
                    key={i}
                    className="bg-gray-900/60 rounded-xl p-4 border border-gray-700/50 hover:border-purple-500/30 transition-all"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-purple-400 font-bold text-sm">Scene {i + 1}</span>
                      <span className="text-gray-500 text-xs">
                        {scene.duration_seconds?.toFixed(0)}s • {scene.script_text?.split(" ").length} words
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm line-clamp-2">{scene.script_text}</p>
                    <div className="flex gap-2 mt-2">
                      <span className="text-xs bg-gray-800 px-2 py-1 rounded-lg text-gray-400">{scene.emotion}</span>
                      <span className="text-xs bg-gray-800 px-2 py-1 rounded-lg text-gray-400">{scene.transition_type}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-4">
              <button onClick={() => setStep(3)} className="flex-1 py-4 rounded-xl bg-gray-800 font-bold hover:bg-gray-700 transition-all">
                ← Edit Settings
              </button>
              <button
                onClick={handleGenerate}
                disabled={loading || scenes.length === 0}
                className="flex-1 py-4 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 font-bold text-lg disabled:opacity-40 hover:opacity-90 transition-all animate-pulse"
              >
                {loading ? "⏳ Starting..." : `🚀 Generate ${scenes.length} Scenes`}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
