"use client";
import { useStore } from "@/store";

export default function Topbar() {
  const { user, notification, clearNotification, logout } = useStore();

  return (
    <>
      <header className="h-14 border-b border-[#1e1e30]/50 glass-strong flex items-center justify-between px-6 sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <h1 className="text-sm font-semibold text-surface-200">Studio</h1>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-surface-700/50 border border-surface-600/50">
              <span className="text-[11px] text-surface-300">Credits</span>
              <span className="text-xs font-semibold text-brand-400">{user.credits_remaining}</span>
            </div>
          )}
          {user && (
            <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-brand-500/15 text-brand-400 border border-brand-500/25 uppercase tracking-wider">
              {user.plan}
            </span>
          )}
          {user && (
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-500 via-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-semibold shadow-sm">
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              <button onClick={logout} className="text-[11px] text-surface-300 hover:text-white transition">
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      {notification && (
        <div className={`fixed top-4 right-4 z-[100] px-4 py-3 rounded-xl border shadow-2xl fade-in glass ${
          notification.type === "success" ? "border-accent-green/30 text-accent-green" :
          notification.type === "error" ? "border-accent-red/30 text-accent-red" :
          "border-brand-500/30 text-brand-400"
        }`}>
          <div className="flex items-center gap-3">
            <span className="text-sm">{notification.message}</span>
            <button onClick={clearNotification} className="text-xs opacity-60 hover:opacity-100">✕</button>
          </div>
        </div>
      )}
    </>
  );
}
