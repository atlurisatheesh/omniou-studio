"use client";
import { useStore } from "@/store";
import Link from "next/link";
import { usePathname } from "next/navigation";

const modules = [
  { id: "dashboard", label: "Dashboard", icon: "⚡", href: "/dashboard" },
  { id: "voice", label: "Voice Studio", icon: "🎙️", href: "/dashboard/voice-studio" },
  { id: "design", label: "Design Studio", icon: "🎨", href: "/dashboard/design-studio" },
  { id: "code", label: "Code Studio", icon: "💻", href: "/dashboard/code-studio" },
  { id: "video", label: "Video Studio", icon: "🎬", href: "/dashboard/video-studio" },
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
      className={`fixed left-0 top-0 h-screen bg-[#0d0d1a] border-r border-[#2a2a4a] transition-all duration-300 z-50 flex flex-col ${
        sidebarCollapsed ? "w-[68px]" : "w-[240px]"
      }`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-[#2a2a4a]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center font-bold text-white text-sm">
            O
          </div>
          {!sidebarCollapsed && (
            <span className="font-bold text-lg gradient-text">Ominou</span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {modules.map((mod) => {
          const isActive = pathname === mod.href || (mod.href !== "/dashboard" && pathname?.startsWith(mod.href));
          return (
            <Link
              key={mod.id}
              href={mod.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                isActive
                  ? "bg-brand-600/20 text-brand-400 border border-brand-600/30"
                  : "text-surface-500 hover:text-surface-300 hover:bg-[#1a1a2e]"
              }`}
              title={sidebarCollapsed ? mod.label : undefined}
            >
              <span className="text-lg">{mod.icon}</span>
              {!sidebarCollapsed && <span>{mod.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Credits & User */}
      <div className="border-t border-[#2a2a4a] p-3">
        {!sidebarCollapsed && user && (
          <div className="mb-3 px-2">
            <div className="text-xs text-surface-500 mb-1">Credits</div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-[#1a1a2e] rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 to-purple-500 rounded-full"
                  style={{ width: `${Math.min((user.credits_remaining / 50) * 100, 100)}%` }}
                />
              </div>
              <span className="text-xs font-medium text-surface-400">{user.credits_remaining}</span>
            </div>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center py-2 text-surface-500 hover:text-surface-300 transition"
        >
          {sidebarCollapsed ? "→" : "←"}
        </button>
      </div>
    </aside>
  );
}
