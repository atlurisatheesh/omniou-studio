"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Video,
  LayoutDashboard,
  Plus,
  Mic,
  Camera,
  Settings,
  CreditCard,
  LogOut,
  BarChart3,
  Layout,
  Users,
} from "lucide-react";

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: Plus, label: "Create Clone", href: "/dashboard/create" },
  { icon: Mic, label: "Voice Library", href: "/dashboard/voice-library" },
  { icon: Camera, label: "Avatars", href: "/dashboard/avatars" },
  { icon: BarChart3, label: "Analytics", href: "/dashboard/analytics", isNew: true },
  { icon: Layout, label: "Templates", href: "/dashboard/templates", isNew: true },
  { icon: Users, label: "Multi-Face", href: "/dashboard/multi-face", isNew: true },
  { icon: Settings, label: "Settings", href: "/dashboard/settings" },
  { icon: CreditCard, label: "Billing", href: "/dashboard/billing" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card p-6 sticky top-0 h-screen">
      <Link href="/" className="flex items-center gap-2 mb-10">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-cyan-400 flex items-center justify-center">
          <Video className="w-4 h-4 text-white" />
        </div>
        <span className="font-bold text-lg">CloneAI Pro</span>
      </Link>

      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition ${
                isActive
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              }`}
            >
              <item.icon className="w-4 h-4" />
              <span className="flex-1">{item.label}</span>
              {item.isNew && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-primary/20 text-primary uppercase">
                  New
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <button className="flex items-center gap-3 px-3 py-2.5 text-sm text-muted-foreground hover:text-foreground transition mt-auto">
        <LogOut className="w-4 h-4" />
        Sign Out
      </button>
    </aside>
  );
}
