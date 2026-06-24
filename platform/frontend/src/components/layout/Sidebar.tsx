"use client";
import { useStore } from "@/store";
import Link from "next/link";
import { usePathname } from "next/navigation";

const modules = [
  { id: "dashboard", label: "Dashboard", icon: "⚡", href: "/dashboard" },
  { id: "video", label: "Film Studio", icon: "🎬", href: "/dashboard/video-studio" },
  { id: "voice", label: "Voice Studio", icon: "🎙️", href: "/dashboard/voice-studio" },
  { id: "design", label: "Design Studio", icon: "🎨", href: "/dashboard/design-studio" },
  { id: "code", label: "Code Studio", icon: "💻", href: "/dashboard/code-studio" },
  { id: "writer", label: "AI Writer", icon: "✍️", href: "/dashboard/ai-writer" },
  { id: "music", label: "Music Studio", icon: "🎵", href: "/dashboard/music-studio" },
  { id: "workflow", label: "Workflows", icon: "🔗", href: "/dashboard/workflows" },
  { id: "assets", label: "Assets", icon: "📁", href: "/dashboard/assets" },
  { id: "settings", label: "Settings", icon: "⚙️", href: "/dashboard/settings" },
];

export default function Sidebar() {
  const { user, sidebarCollapsed, toggleSidebar } = useStore();
  const pathname = usePathname();

  return (
    <aside
      className={`fixed left-0 top-0 h-screen glass-strong transition-all duration-300 z-50 flex flex-col ${
        sidebarCollapsed ? "w-[68px]" : "w-[240px]"
      }`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-[#1e1e30]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 via-purple-500 to-pink-500 flex items-center justify-center font-bold text-white text-sm shadow-lg shadow-brand-500/20">
            O
          </div>
          {!sidebarCollapsed && (
            <span className="font-bold text-lg gradient-text tracking-tight">Ominou</span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-0.5 overflow-y-auto">
        {modules.map((mod) => {
          const isActive = pathname === mod.href || (mod.href !== "/dashboard" && pathname?.startsWith(mod.href));
          return (
            <Link
              key={mod.id}
              href={mod.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                isActive
                  ? "bg-brand-500/15 text-brand-400 border border-brand-500/25 shadow-sm shadow-brand-500/10"
                  : "text-surface-200 hover:text-white hover:bg-white/[0.04]"
              }`}
              title={sidebarCollapsed ? mod.label : undefined}
            >
              <span className="text-lg">{mod.icon}</span>
              {!sidebarCollapsed && <span className="font-medium">{mod.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Credits & User */}
      <div className="border-t border-[#1e1e30] p-3">
        {!sidebarCollapsed && user && (
          <div className="mb-3 px-2">
            <div className="text-xs text-surface-300 mb-1.5 font-medium">Credits</div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-surface-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 via-purple-500 to-pink-500 rounded-full transition-all"
                  title="Credits remaining"
                  style={{ width: `${Math.min((user.credits_remaining / 50) * 100, 100)}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-surface-200">{user.credits_remaining}</span>
            </div>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center py-2 text-surface-300 hover:text-white transition rounded-lg hover:bg-white/[0.04]"
        >
          {sidebarCollapsed ? "→" : "←"}
        </button>
      </div>
    </aside>
  );
}
