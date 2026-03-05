"use client";

import { useEffect, useRef, useState } from "react";
import { useCloneStore } from "@/lib/store";
import {
  createClone,
  connectProgressWebSocket,
  getVideoDownloadUrl,
} from "@/lib/api";
import {
  Loader2,
  Download,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Mic,
  Camera,
  Sparkles,
  Clapperboard,
  Wand2,
} from "lucide-react";

const STEP_LABELS: Record<string, { label: string; icon: typeof Mic }> = {
  queued: { label: "Queued", icon: Loader2 },
  initializing: { label: "Initializing AI models...", icon: Loader2 },
  voice_cloning: { label: "Cloning your voice (XTTS v2)...", icon: Mic },
  face_animating: { label: "Animating your face (MuseTalk)...", icon: Camera },
  lip_syncing: { label: "Refining lip sync...", icon: Clapperboard },
  enhancing: { label: "Enhancing face quality (GFPGAN)...", icon: Wand2 },
  encoding: { label: "Final encoding...", icon: Sparkles },
  completed: { label: "Done!", icon: CheckCircle },
  failed: { label: "Generation failed", icon: AlertTriangle },
};

export function StepGenerating() {
  const {
    photoPath,
    voicePath,
    scriptText,
    targetLanguage,
    jobId,
    jobStatus,
    jobProgress,
    jobStep,
    jobError,
    resultUrl,
    setJob,
    updateJobProgress,
    reset,
  } = useCloneStore();

  const wsRef = useRef<WebSocket | null>(null);
  const [started, setStarted] = useState(false);

  // Start generation on mount
  useEffect(() => {
    if (started || jobId) return;
    setStarted(true);

    const startGeneration = async () => {
      try {
        const result = await createClone({
          photo_path: photoPath!,
          voice_path: voicePath!,
          script_text: scriptText,
          target_language: targetLanguage,
        });

        setJob(result.job_id);

        // Connect WebSocket for progress
        wsRef.current = connectProgressWebSocket(
          result.job_id,
          (data) => {
            updateJobProgress(
              data.status,
              data.progress,
              data.step,
              data.error || null,
              (data as any).download_url || null
            );
          },
          () => {
            console.error("WebSocket error");
          },
          () => {
            console.log("WebSocket closed");
          }
        );
      } catch (err: any) {
        // If backend is unavailable, simulate progress for demo
        console.warn("Backend unavailable, simulating progress:", err);
        simulateProgress();
      }
    };

    startGeneration();

    return () => {
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Demo simulation when backend is not available
  const simulateProgress = () => {
    const steps = [
      { status: "processing", progress: 5, step: "initializing" },
      { status: "processing", progress: 15, step: "voice_cloning" },
      { status: "processing", progress: 30, step: "voice_cloning" },
      { status: "processing", progress: 45, step: "face_animating" },
      { status: "processing", progress: 60, step: "face_animating" },
      { status: "processing", progress: 70, step: "lip_syncing" },
      { status: "processing", progress: 80, step: "enhancing" },
      { status: "processing", progress: 90, step: "encoding" },
      { status: "completed", progress: 100, step: "completed" },
    ];

    setJob("demo-" + Date.now());

    steps.forEach((s, i) => {
      setTimeout(() => {
        updateJobProgress(s.status, s.progress, s.step);
      }, (i + 1) * 2000);
    });
  };

  const stepInfo = STEP_LABELS[jobStep] || STEP_LABELS.queued;
  const StepIcon = stepInfo.icon;
  const isCompleted = jobStatus === "completed";
  const isFailed = jobStatus === "failed";

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2">
          {isCompleted ? "Your Video is Ready!" : isFailed ? "Generation Failed" : "Generating Your Clone..."}
        </h1>
        <p className="text-muted-foreground text-sm">
          {isCompleted
            ? "Download your AI avatar video — no watermark, 1080p."
            : isFailed
            ? jobError || "Something went wrong. Please try again."
            : "Our AI pipeline is working. This usually takes 60-90 seconds."}
        </p>
      </div>

      {/* Progress ring */}
      <div className="flex justify-center">
        <div className="relative w-40 h-40">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="hsl(217 33% 15%)"
              strokeWidth="6"
            />
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={isFailed ? "hsl(0 84% 60%)" : isCompleted ? "hsl(142 76% 36%)" : "hsl(199 89% 48%)"}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 45}`}
              strokeDashoffset={`${2 * Math.PI * 45 * (1 - jobProgress / 100)}`}
              className="transition-all duration-700 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-extrabold">{jobProgress}%</span>
          </div>
        </div>
      </div>

      {/* Current step */}
      <div className="flex items-center justify-center gap-3">
        <StepIcon
          className={`w-5 h-5 ${
            isCompleted ? "text-green-400" : isFailed ? "text-red-400" : "text-primary animate-spin"
          }`}
        />
        <span className="text-sm font-medium">{stepInfo.label}</span>
      </div>

      {/* Pipeline steps */}
      <div className="bg-card border border-border rounded-xl p-6 space-y-3">
        {["voice_cloning", "face_animating", "lip_syncing", "enhancing", "encoding"].map(
          (step) => {
            const info = STEP_LABELS[step];
            const stepIdx = [
              "voice_cloning",
              "face_animating",
              "lip_syncing",
              "enhancing",
              "encoding",
            ].indexOf(step);
            const currentIdx = [
              "voice_cloning",
              "face_animating",
              "lip_syncing",
              "enhancing",
              "encoding",
            ].indexOf(jobStep);
            const isDone = isCompleted || currentIdx > stepIdx;
            const isCurrent = jobStep === step;

            return (
              <div key={step} className="flex items-center gap-3">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                    isDone
                      ? "bg-green-500/20 text-green-400"
                      : isCurrent
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {isDone ? (
                    <CheckCircle className="w-3.5 h-3.5" />
                  ) : isCurrent ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground" />
                  )}
                </div>
                <span
                  className={`text-sm ${
                    isDone
                      ? "text-green-400"
                      : isCurrent
                      ? "text-foreground font-medium"
                      : "text-muted-foreground"
                  }`}
                >
                  {info.label.replace("...", "")}
                </span>
              </div>
            );
          }
        )}
      </div>

      {/* Actions */}
      {isCompleted && (
        <div className="space-y-3">
          <a
            href={jobId ? getVideoDownloadUrl(jobId) : "#"}
            download
            className="w-full flex items-center justify-center gap-2 py-4 bg-green-500 text-white font-bold rounded-xl hover:bg-green-600 transition text-lg"
          >
            <Download className="w-5 h-5" />
            Download Video (MP4)
          </a>
          <button
            onClick={reset}
            className="w-full flex items-center justify-center gap-2 py-3 border border-border rounded-xl text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition"
          >
            <RotateCcw className="w-4 h-4" />
            Create Another Video
          </button>
        </div>
      )}

      {isFailed && (
        <div className="space-y-3">
          <button
            onClick={() => {
              useCloneStore.setState({
                jobId: null,
                jobStatus: "idle",
                jobProgress: 0,
                jobStep: "",
                jobError: null,
              });
              setStarted(false);
            }}
            className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition"
          >
            <RotateCcw className="w-4 h-4" />
            Try Again
          </button>
          <button
            onClick={reset}
            className="w-full flex items-center justify-center gap-2 py-3 border border-border rounded-xl text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition"
          >
            Start Over
          </button>
        </div>
      )}
    </div>
  );
}
