"use client";

/**
 * CLONEAI PRO — Scene Editor with Identity Consistency Panel
 * Studio-grade project editor showing per-scene identity/color scores,
 * visual timeline, and side-by-side consistency comparison.
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { project as projectApi, connectProjectWebSocket } from "@/lib/api";
import type { Project, ProjectScene, ProjectProgress } from "@/lib/api";

export default function ProjectEditorPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [proj, setProj] = useState<Project | null>(null);
  const [activeScene, setActiveScene] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState<ProjectProgress | null>(null);

  // Load project
  useEffect(() => {
    if (!projectId) return;

    const load = async () => {
      try {
        const data = await projectApi.get(projectId);
        setProj(data);
        setGenerating(data.status === "generating");
      } catch (e) {
        console.error("Failed to load project:", e);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [projectId]);

  // Poll progress when generating
  useEffect(() => {
    if (!generating || !projectId) return;

    const interval = setInterval(async () => {
      try {
        const prog = await projectApi.progress(projectId);
        setProgress(prog);

        if (prog.status === "completed" || prog.status === "failed") {
          setGenerating(false);
          // Reload full project
          const data = await projectApi.get(projectId);
          setProj(data);
        }
      } catch (e) {
        console.error("Progress poll failed:", e);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [generating, projectId]);

  const handleGenerate = async () => {
    if (!projectId) return;
    try {
      await projectApi.generate(projectId);
      setGenerating(true);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleRegenerate = async (sceneIndex: number) => {
    if (!projectId) return;
    try {
      await projectApi.regenerateScene(projectId, sceneIndex);
      // Reload project
      const data = await projectApi.get(projectId);
      setProj(data);
    } catch (e: any) {
      alert(e.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading project...</p>
        </div>
      </div>
    );
  }

  if (!proj) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950 flex items-center justify-center">
        <p className="text-red-400 text-xl">Project not found</p>
      </div>
    );
  }

  const currentScene = proj.scenes?.[activeScene];
  const totalDuration = proj.scenes?.reduce((sum, s) => sum + (s.duration_seconds || 0), 0) || 0;
  const overallScore = proj.overall_identity_score ? Math.round(proj.overall_identity_score * 100) : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950 text-white">
      {/* Top Bar */}
      <div className="bg-gray-900/80 backdrop-blur border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ← Back
          </button>
          <h1 className="text-xl font-bold">{proj.name}</h1>
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
            proj.status === "completed" ? "bg-green-500/20 text-green-400" :
            proj.status === "generating" ? "bg-blue-500/20 text-blue-400" :
            proj.status === "failed" ? "bg-red-500/20 text-red-400" :
            "bg-gray-700 text-gray-400"
          }`}>
            {proj.status}
          </span>
        </div>

        <div className="flex items-center gap-4">
          {overallScore !== null && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Identity:</span>
              <span className={`font-bold text-lg ${
                overallScore >= 85 ? "text-green-400" :
                overallScore >= 70 ? "text-yellow-400" :
                "text-red-400"
              }`}>
                {overallScore}%
              </span>
              <span className="text-gray-400">🔒</span>
            </div>
          )}

          {proj.status === "draft" && (
            <button
              onClick={handleGenerate}
              className="px-6 py-2 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 font-bold hover:opacity-90 transition-all"
            >
              🚀 Generate All
            </button>
          )}

          {proj.output_path && (
            <a
              href={proj.output_path}
              className="px-6 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 font-bold hover:opacity-90 transition-all"
            >
              ⬇ Download
            </a>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-65px)]">
        {/* Left: Scene List */}
        <div className="w-72 bg-gray-900/50 border-r border-gray-800 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">
              Scenes ({proj.scenes?.length || 0})
            </h2>

            <div className="space-y-2">
              {proj.scenes?.map((scene, i) => (
                <button
                  key={scene.id}
                  onClick={() => setActiveScene(i)}
                  className={`w-full text-left rounded-xl p-3 transition-all ${
                    activeScene === i
                      ? "bg-purple-500/20 border border-purple-500/40"
                      : "bg-gray-800/50 border border-transparent hover:bg-gray-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-purple-400 font-bold text-xs">Scene {i + 1}</span>
                    <span className={`text-xs ${
                      scene.status === "completed" ? "text-green-400" :
                      scene.status === "generating" ? "text-blue-400" :
                      scene.status === "failed" ? "text-red-400" :
                      "text-gray-500"
                    }`}>
                      {scene.status === "completed" ? "✅" :
                       scene.status === "generating" ? "🔄" :
                       scene.status === "failed" ? "❌" : "⏳"}
                    </span>
                  </div>

                  <p className="text-gray-300 text-xs line-clamp-2">{scene.script_text}</p>

                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] text-gray-500">{scene.duration_seconds?.toFixed(0)}s</span>
                    {scene.identity_score !== null && (
                      <span className={`text-[10px] font-bold ${
                        scene.identity_score >= 0.85 ? "text-green-400" :
                        scene.identity_score >= 0.70 ? "text-yellow-400" :
                        "text-red-400"
                      }`}>
                        🎭{Math.round(scene.identity_score * 100)}%
                      </span>
                    )}
                    {scene.color_consistency_score !== null && (
                      <span className={`text-[10px] font-bold ${
                        scene.color_consistency_score >= 0.85 ? "text-green-400" :
                        scene.color_consistency_score >= 0.70 ? "text-yellow-400" :
                        "text-red-400"
                      }`}>
                        🎨{Math.round(scene.color_consistency_score * 100)}%
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Center: Preview + Consistency */}
        <div className="flex-1 overflow-y-auto">
          {currentScene && (
            <div className="p-8 space-y-6">
              {/* Preview Area */}
              <div className="bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6">
                <div className="aspect-video bg-gray-900 rounded-xl flex items-center justify-center mb-4">
                  {currentScene.status === "completed" ? (
                    <div className="text-center">
                      <div className="text-6xl mb-3">🎬</div>
                      <p className="text-gray-300">Scene {activeScene + 1} Generated</p>
                    </div>
                  ) : currentScene.status === "generating" ? (
                    <div className="text-center">
                      <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-3" />
                      <p className="text-blue-400">Generating...</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <div className="text-6xl mb-3">🎥</div>
                      <p className="text-gray-500">Preview will appear after generation</p>
                    </div>
                  )}
                </div>

                {/* Scene Details */}
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="bg-gray-900/50 rounded-xl p-3">
                    <span className="text-gray-500 block text-xs">Duration</span>
                    <span className="text-white font-bold">{currentScene.duration_seconds?.toFixed(0)}s</span>
                  </div>
                  <div className="bg-gray-900/50 rounded-xl p-3">
                    <span className="text-gray-500 block text-xs">Emotion</span>
                    <span className="text-white font-bold">{currentScene.emotion}</span>
                  </div>
                  <div className="bg-gray-900/50 rounded-xl p-3">
                    <span className="text-gray-500 block text-xs">Transition</span>
                    <span className="text-white font-bold">{currentScene.transition_type}</span>
                  </div>
                </div>
              </div>

              {/* Script */}
              <div className="bg-gray-800/50 rounded-2xl border border-gray-700/50 p-6">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">Script</h3>
                <p className="text-gray-200 leading-relaxed">{currentScene.script_text}</p>
                <p className="text-gray-500 text-xs mt-2">
                  {currentScene.script_text?.split(" ").length} words
                </p>
              </div>

              {/* Consistency Panel */}
              <div className="bg-gray-800/50 rounded-2xl border border-purple-500/20 p-6">
                <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  🔒 Character Consistency
                </h3>

                {currentScene.identity_score !== null ? (
                  <div className="space-y-4">
                    {/* Identity Score */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-300">Face Match</span>
                        <span className={`font-bold ${
                          (currentScene.identity_score || 0) >= 0.85 ? "text-green-400" :
                          (currentScene.identity_score || 0) >= 0.70 ? "text-yellow-400" :
                          "text-red-400"
                        }`}>
                          {Math.round((currentScene.identity_score || 0) * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all duration-500 ${
                            (currentScene.identity_score || 0) >= 0.85 ? "bg-green-500" :
                            (currentScene.identity_score || 0) >= 0.70 ? "bg-yellow-500" :
                            "bg-red-500"
                          }`}
                          style={{ width: `${(currentScene.identity_score || 0) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Color Score */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-300">Color Consistency</span>
                        <span className={`font-bold ${
                          (currentScene.color_consistency_score || 0) >= 0.85 ? "text-green-400" :
                          (currentScene.color_consistency_score || 0) >= 0.70 ? "text-yellow-400" :
                          "text-red-400"
                        }`}>
                          {Math.round((currentScene.color_consistency_score || 0) * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all duration-500 ${
                            (currentScene.color_consistency_score || 0) >= 0.85 ? "bg-green-500" :
                            (currentScene.color_consistency_score || 0) >= 0.70 ? "bg-yellow-500" :
                            "bg-red-500"
                          }`}
                          style={{ width: `${(currentScene.color_consistency_score || 0) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Cross-Scene Score */}
                    {currentScene.cross_scene_score !== null && (
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-300">Cross-Scene Match</span>
                          <span className="font-bold text-blue-400">
                            {Math.round((currentScene.cross_scene_score || 0) * 100)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-3">
                          <div
                            className="h-3 rounded-full bg-blue-500 transition-all duration-500"
                            style={{ width: `${(currentScene.cross_scene_score || 0) * 100}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Drift Info */}
                    {currentScene.drift_frame_count > 0 && (
                      <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-3">
                        <p className="text-yellow-300 text-sm">
                          ⚠️ {currentScene.drift_frame_count} frames were auto-corrected for identity drift
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">Scores will appear after generation</p>
                )}

                {/* Actions */}
                <div className="mt-4 flex gap-3">
                  <button
                    onClick={() => handleRegenerate(currentScene.scene_index)}
                    className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-sm transition-all"
                  >
                    🔄 Regenerate
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom: Timeline */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900/90 backdrop-blur border-t border-gray-800 px-6 py-3">
        <div className="flex items-center gap-2 mb-2">
          {proj.scenes?.map((scene, i) => {
            const width = totalDuration > 0
              ? `${(scene.duration_seconds / totalDuration) * 100}%`
              : `${100 / proj.scenes.length}%`;

            const scoreColor = scene.identity_score !== null
              ? scene.identity_score >= 0.85 ? "bg-green-500" :
                scene.identity_score >= 0.70 ? "bg-yellow-500" :
                "bg-red-500"
              : scene.status === "generating" ? "bg-blue-500 animate-pulse"
              : "bg-gray-700";

            return (
              <button
                key={i}
                onClick={() => setActiveScene(i)}
                className={`h-8 rounded-lg ${scoreColor} transition-all hover:opacity-80 ${
                  activeScene === i ? "ring-2 ring-white" : ""
                }`}
                style={{ width }}
                title={`Scene ${i + 1}: ${scene.duration_seconds?.toFixed(0)}s`}
              />
            );
          })}
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>0:00</span>
          <span>
            {generating && progress
              ? `Generating: ${progress.completed_scenes}/${progress.total_scenes} scenes (${progress.progress_percent?.toFixed(0)}%)`
              : `${Math.floor(totalDuration / 60)}:${String(Math.floor(totalDuration % 60)).padStart(2, "0")} total`}
          </span>
          <span>{Math.floor(totalDuration / 60)}:{String(Math.floor(totalDuration % 60)).padStart(2, "0")}</span>
        </div>
      </div>
    </div>
  );
}
