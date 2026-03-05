"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Video,
  Mic,
  Camera,
  Upload,
  Trash2,
  LayoutDashboard,
  Settings,
  CreditCard,
  LogOut,
  ImageIcon,
  User,
} from "lucide-react";

interface Avatar {
  id: string;
  name: string;
  type: "photo" | "video";
  created_at: string;
  usage_count: number;
}

const DEMO_AVATARS: Avatar[] = [
  {
    id: "a1",
    name: "Professional Headshot",
    type: "photo",
    created_at: "3 days ago",
    usage_count: 5,
  },
  {
    id: "a2",
    name: "Casual Portrait",
    type: "photo",
    created_at: "1 week ago",
    usage_count: 3,
  },
  {
    id: "a3",
    name: "Studio Photo",
    type: "photo",
    created_at: "2 weeks ago",
    usage_count: 1,
  },
];

export default function AvatarsPage() {
  const [avatars] = useState<Avatar[]>(DEMO_AVATARS);

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
            { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard", active: false },
            { icon: Plus, label: "Create Clone", href: "/dashboard/create", active: false },
            { icon: Mic, label: "Voice Library", href: "/dashboard/voice-library", active: false },
            { icon: Camera, label: "Avatars", href: "/dashboard/avatars", active: true },
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
            <h1 className="text-2xl font-bold">Avatars</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Manage your face photos and AI avatars
            </p>
          </div>
          <Link
            href="/dashboard/create"
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-xl font-semibold text-sm hover:bg-primary/90 transition"
          >
            <Upload className="w-4 h-4" />
            Upload Avatar
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <User className="w-4 h-4" />
              <span className="text-xs font-medium">Total Avatars</span>
            </div>
            <p className="text-2xl font-bold">{avatars.length}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <ImageIcon className="w-4 h-4" />
              <span className="text-xs font-medium">Total Usage</span>
            </div>
            <p className="text-2xl font-bold">
              {avatars.reduce((a, v) => a + v.usage_count, 0)} videos
            </p>
          </div>
        </div>

        {/* Avatar grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {avatars.map((avatar) => (
            <div
              key={avatar.id}
              className="bg-card border border-border rounded-xl overflow-hidden hover:border-primary/30 transition group"
            >
              {/* Placeholder image */}
              <div className="aspect-square bg-gradient-to-br from-primary/10 to-cyan-400/10 flex items-center justify-center">
                <User className="w-16 h-16 text-primary/30" />
              </div>

              {/* Info */}
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">{avatar.name}</p>
                  <button
                    className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition opacity-0 group-hover:opacity-100"
                    title="Delete"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                  <span className="capitalize">{avatar.type}</span>
                  <span>{avatar.usage_count} video{avatar.usage_count !== 1 ? "s" : ""}</span>
                  <span>{avatar.created_at}</span>
                </div>
              </div>
            </div>
          ))}

          {/* Upload card */}
          <Link
            href="/dashboard/create"
            className="bg-card border-2 border-dashed border-border rounded-xl flex flex-col items-center justify-center aspect-square hover:border-primary/50 transition text-muted-foreground hover:text-primary"
          >
            <Plus className="w-10 h-10 mb-2" />
            <span className="text-sm font-medium">Add New Avatar</span>
          </Link>
        </div>
      </main>
    </div>
  );
}
