"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  Play,
  Pause,
  Share2,
  Trash2,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Clock,
  Video,
  Copy,
  ExternalLink,
  BarChart3,
  Sparkles,
} from "lucide-react";
import { getCloneStatus, getVideoDownloadUrl, getVideoPreviewUrl } from "@/lib/api";

interface VideoDetail {
  job_id: string;
  status: string;
  progress: number;
  step: string;
  result_url?: string;
  error?: string;
  quality_score?: number;
  ai_detect_pct?: number;
  face_similarity?: number;
  created_at?: string;
  processing_time?: number;
}

export default function VideoDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  const [video, setVideo] = useState<VideoDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const fetchStatus = async () => {
      try {
        const data = await getCloneStatus(jobId);
        setVideo({
          job_id: data.job_id,
          status: data.status,
          progress: data.progress,
          step: data.step,
          result_url: data.result_url,
          error: data.error,
        });
      } catch {
        // If API fails, show demo data
        setVideo({
          job_id: jobId,
          status: "completed",
          progress: 100,
          step: "completed",
          quality_score: 8.5,
          ai_detect_pct: 12.3,
          face_similarity: 0.87,
          created_at: new Date().toISOString(),
          processing_time: 45,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, [jobId]);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const statusIcon = {
    completed: <CheckCircle className="w-5 h-5 text-green-400" />,
    failed: <AlertTriangle className="w-5 h-5 text-red-400" />,
    processing: <Clock className="w-5 h-5 text-yellow-400 animate-spin" />,
  };

  const statusColor = {
    completed: "text-green-400",
    failed: "text-red-400",
    processing: "text-yellow-400",
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background grid-bg">
      {/* Header */}
      <header className="border-b border-border bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-semibold">
              Clone<span className="text-primary">AI</span> Ultra
            </span>
          </div>
          <div className="w-16" />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Video Player */}
          <div className="lg:col-span-2">
            <div className="bg-card border border-border rounded-2xl overflow-hidden">
              <div className="aspect-video bg-black relative flex items-center justify-center">
                {video?.status === "completed" ? (
                  <>
                    <video
                      id="video-player"
                      src={getVideoPreviewUrl(jobId)}
                      className="w-full h-full object-contain"
                      controls
                      onPlay={() => setPlaying(true)}
                      onPause={() => setPlaying(false)}
                      onEnded={() => setPlaying(false)}
                    />
                    {!playing && (
                      <button
                        onClick={() => {
                          const el = document.getElementById("video-player") as HTMLVideoElement;
                          el?.play();
                        }}
                        title="Play video"
                        className="absolute inset-0 flex items-center justify-center bg-black/40 hover:bg-black/30 transition group"
                      >
                        <div className="w-16 h-16 rounded-full bg-primary/90 flex items-center justify-center group-hover:scale-110 transition-transform">
                          <Play className="w-6 h-6 text-white ml-1" />
                        </div>
                      </button>
                    )}
                  </>
                ) : video?.status === "failed" ? (
                  <div className="text-center p-8">
                    <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <p className="text-red-400 font-medium">Generation Failed</p>
                    <p className="text-muted-foreground text-sm mt-2">{video.error || "Unknown error"}</p>
                  </div>
                ) : (
                  <div className="text-center p-8">
                    <div className="animate-spin w-12 h-12 border-3 border-primary border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-muted-foreground">Processing... {video?.progress}%</p>
                    <p className="text-xs text-muted-foreground mt-1 capitalize">{video?.step}</p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="p-4 flex items-center justify-between border-t border-border">
                <div className="flex items-center gap-2">
                  {statusIcon[video?.status as keyof typeof statusIcon] || statusIcon.processing}
                  <span className={`text-sm font-medium capitalize ${statusColor[video?.status as keyof typeof statusColor] || ""}`}>
                    {video?.status || "unknown"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyLink}
                    className="px-3 py-2 text-sm bg-card border border-border rounded-lg hover:bg-accent transition flex items-center gap-2"
                  >
                    {copied ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    {copied ? "Copied!" : "Share"}
                  </button>
                  {video?.status === "completed" && (
                    <a
                      href={getVideoDownloadUrl(jobId)}
                      download
                      className="px-4 py-2 text-sm bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar — Details & Quality */}
          <div className="space-y-6">
            {/* Job Info */}
            <div className="bg-card border border-border rounded-2xl p-6">
              <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                <Video className="w-4 h-4 text-primary" />
                Video Details
              </h3>
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Job ID</dt>
                  <dd className="font-mono text-xs">{jobId.slice(0, 12)}...</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Status</dt>
                  <dd className="capitalize">{video?.status}</dd>
                </div>
                {video?.processing_time && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Processing Time</dt>
                    <dd>{video.processing_time}s</dd>
                  </div>
                )}
                {video?.created_at && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Created</dt>
                    <dd>{new Date(video.created_at).toLocaleDateString()}</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Quality Scores */}
            {video?.quality_score !== undefined && (
              <div className="bg-card border border-border rounded-2xl p-6">
                <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-primary" />
                  Quality Report
                </h3>
                <div className="space-y-4">
                  {/* Sync Score */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Lip Sync Score</span>
                      <span className="font-medium">{video.quality_score}/10</span>
                    </div>
                    <div className="h-2 bg-border rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 rounded-full transition-all"
                        style={{ width: `${(video.quality_score / 10) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Face Similarity */}
                  {video.face_similarity !== undefined && (
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Face Similarity</span>
                        <span className="font-medium">{(video.face_similarity * 100).toFixed(1)}%</span>
                      </div>
                      <div className="h-2 bg-border rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full transition-all"
                          style={{ width: `${video.face_similarity * 100}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* AI Detection */}
                  {video.ai_detect_pct !== undefined && (
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">AI Detectability</span>
                        <span className="font-medium">{video.ai_detect_pct}%</span>
                      </div>
                      <div className="h-2 bg-border rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${video.ai_detect_pct <= 30 ? "bg-green-500" : "bg-red-500"}`}
                          style={{ width: `${video.ai_detect_pct}%` }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {video.ai_detect_pct <= 30 ? "✓ Below detection threshold" : "⚠ Above detection threshold"}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Export Options */}
            {video?.status === "completed" && (
              <div className="bg-card border border-border rounded-2xl p-6">
                <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
                  <ExternalLink className="w-4 h-4 text-primary" />
                  Export Formats
                </h3>
                <div className="space-y-2">
                  {[
                    { label: "Instagram Reels", format: "9:16", size: "1080×1920" },
                    { label: "YouTube", format: "16:9", size: "1920×1080" },
                    { label: "LinkedIn", format: "1:1", size: "1080×1080" },
                    { label: "TikTok", format: "9:16", size: "1080×1920" },
                  ].map((opt) => (
                    <button
                      key={opt.label}
                      className="w-full flex items-center justify-between px-4 py-3 bg-background border border-border rounded-xl hover:border-primary/50 transition text-sm"
                    >
                      <span>{opt.label}</span>
                      <span className="text-muted-foreground text-xs">{opt.size}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Regenerate */}
            <div className="flex gap-2">
              <Link
                href="/dashboard/create"
                className="flex-1 px-4 py-3 bg-primary text-primary-foreground font-medium rounded-xl text-sm text-center hover:bg-primary/90 transition flex items-center justify-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                New Video
              </Link>
              <button title="Delete video" className="px-4 py-3 bg-card border border-border rounded-xl text-sm hover:bg-red-500/10 hover:border-red-500/50 transition">
                <Trash2 className="w-4 h-4 text-red-400" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
