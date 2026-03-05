"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Plus,
  Video,
  Clock,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Download,
  Trash2,
  LayoutDashboard,
  Settings,
  CreditCard,
  LogOut,
  ChevronRight,
  Mic,
  Camera,
} from "lucide-react";
import { getCloneStatus, getVideoDownloadUrl } from "@/lib/api";

interface CloneJob {
  id: string;
  status: string;
  progress: number;
  created_at: string;
  script_preview: string;
  language: string;
  duration?: number;
}

// Build demo jobs lazily (called only on client via useEffect)
function createDemoJobs(): CloneJob[] {
  return [
    {
      id: "demo-1",
      status: "completed",
      progress: 100,
      created_at: new Date(Date.now() - 3600000).toISOString(),
      script_preview: "Welcome to our product launch! Today we're excited to unveil...",
      language: "en",
      duration: 45,
    },
    {
      id: "demo-2",
      status: "completed",
      progress: 100,
      created_at: new Date(Date.now() - 7200000).toISOString(),
      script_preview: "Hola a todos, bienvenidos a nuestro canal de YouTube...",
      language: "es",
      duration: 30,
    },
    {
      id: "demo-3",
      status: "processing",
      progress: 62,
      created_at: new Date(Date.now() - 300000).toISOString(),
      script_preview: "This tutorial will walk you through the setup process...",
      language: "en",
    },
  ];
}

const STATUS_MAP: Record<
  string,
  { label: string; icon: typeof CheckCircle; color: string }
> = {
  completed: { label: "Completed", icon: CheckCircle, color: "text-green-400" },
  processing: { label: "Processing", icon: Loader2, color: "text-primary" },
  queued: { label: "Queued", icon: Clock, color: "text-yellow-400" },
  failed: { label: "Failed", icon: AlertTriangle, color: "text-red-400" },
};

export default function DashboardPage() {
  const [jobs, setJobs] = useState<CloneJob[]>([]);
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<"all" | "completed" | "processing">("all");

  // Hydrate demo data only on client to avoid SSR mismatch
  useEffect(() => {
    setJobs(createDemoJobs());
    setMounted(true);
  }, []);

  const filteredJobs =
    activeTab === "all" ? jobs : jobs.filter((j) => j.status === activeTab);

  const stats = {
    total: jobs.length,
    completed: jobs.filter((j) => j.status === "completed").length,
    processing: jobs.filter((j) => j.status === "processing" || j.status === "queued").length,
    totalDuration: jobs.reduce((acc, j) => acc + (j.duration || 0), 0),
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card p-6 sticky top-0 h-screen">
        <Link href="/" className="flex items-center gap-2 mb-10">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-cyan-400 flex items-center justify-center">
            <Video className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-lg">CloneAI Pro</span>
        </Link>

        <nav className="flex-1 space-y-1">
          {[
            { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard", active: true },
            { icon: Plus, label: "Create Clone", href: "/dashboard/create", active: false },
            { icon: Mic, label: "Voice Library", href: "/dashboard/voice-library", active: false },
            { icon: Camera, label: "Avatars", href: "/dashboard/avatars", active: false },
            { icon: Settings, label: "Settings", href: "/dashboard/settings", active: false },
            { icon: CreditCard, label: "Billing", href: "/dashboard/billing", active: false },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
                item.active
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          ))}
        </nav>

        <button className="flex items-center gap-3 px-3 py-2.5 text-sm text-muted-foreground hover:text-foreground transition mt-auto">
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-6 md:p-10 max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Manage your AI avatar videos
            </p>
          </div>
          <Link
            href="/dashboard/create"
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-xl font-semibold text-sm hover:bg-primary/90 transition"
          >
            <Plus className="w-4 h-4" />
            New Video
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Videos", value: stats.total, icon: Video },
            { label: "Completed", value: stats.completed, icon: CheckCircle },
            { label: "In Progress", value: stats.processing, icon: Loader2 },
            {
              label: "Total Duration",
              value: `${Math.floor(stats.totalDuration / 60)}m ${stats.totalDuration % 60}s`,
              icon: Clock,
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className="bg-card border border-border rounded-xl p-4"
            >
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <stat.icon className="w-4 h-4" />
                <span className="text-xs font-medium">{stat.label}</span>
              </div>
              <p className="text-2xl font-bold">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 bg-card border border-border rounded-xl p-1 mb-6 w-fit">
          {(["all", "completed", "processing"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm rounded-lg transition capitalize ${
                activeTab === tab
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Job list */}
        <div className="space-y-3">
          {filteredJobs.length === 0 ? (
            <div className="text-center py-20 bg-card border border-border rounded-xl">
              <Video className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                No videos in this category yet
              </p>
              <Link
                href="/dashboard/create"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-xl font-semibold text-sm hover:bg-primary/90 transition"
              >
                <Plus className="w-4 h-4" />
                Create Your First Video
              </Link>
            </div>
          ) : (
            filteredJobs.map((job) => {
              const statusInfo = STATUS_MAP[job.status] || STATUS_MAP.queued;
              const StatusIcon = statusInfo.icon;
              const timeAgo = getTimeAgo(job.created_at);

              return (
                <div
                  key={job.id}
                  className="bg-card border border-border rounded-xl p-5 flex items-center gap-4 hover:border-primary/30 transition group"
                >
                  {/* Thumbnail placeholder */}
                  <div className="w-16 h-16 bg-gradient-to-br from-primary/20 to-cyan-400/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Video className="w-6 h-6 text-primary/60" />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {job.script_preview}
                    </p>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                      <span className={`flex items-center gap-1 ${statusInfo.color}`}>
                        <StatusIcon
                          className={`w-3 h-3 ${
                            job.status === "processing" ? "animate-spin" : ""
                          }`}
                        />
                        {statusInfo.label}
                      </span>
                      <span>{job.language.toUpperCase()}</span>
                      {job.duration && <span>{job.duration}s</span>}
                      <span suppressHydrationWarning>{mounted ? timeAgo : ""}</span>
                    </div>

                    {/* Progress bar for processing */}
                    {job.status === "processing" && (
                      <div className="mt-2 h-1.5 bg-border rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-500"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition">
                    {job.status === "completed" && (
                      <a
                        href={getVideoDownloadUrl(job.id)}
                        className="p-2 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20 transition"
                        title="Download"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    )}
                    <button
                      className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                </div>
              );
            })
          )}
        </div>
      </main>
    </div>
  );
}

function getTimeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
