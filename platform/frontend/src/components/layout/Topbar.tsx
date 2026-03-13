"use client";
import { useStore } from "@/store";

export default function Topbar() {
  const { user, notification, clearNotification, logout } = useStore();

  return (
    <>
      <header className="h-16 border-b border-[#2a2a4a] bg-[#0d0d1a]/80 backdrop-blur flex items-center justify-between px-6 sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold text-surface-200">Studio</h1>
        </div>

        <div className="flex items-center gap-4">
          {/* Credits Badge */}
          {user && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#1a1a2e] border border-[#2a2a4a]">
              <span className="text-xs text-surface-500">Credits:</span>
              <span className="text-sm font-semibold text-brand-400">{user.credits_remaining}</span>
            </div>
          )}

          {/* Plan Badge */}
          {user && (
            <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-brand-600/20 text-brand-400 border border-brand-600/30 uppercase">
              {user.plan}
            </span>
          )}

          {/* User */}
          {user && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-white text-sm font-semibold">
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              <button
                onClick={logout}
                className="text-xs text-surface-500 hover:text-surface-300 transition"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div
          className={`fixed top-4 right-4 z-[100] px-4 py-3 rounded-lg border shadow-lg fade-in ${
            notification.type === "success"
              ? "bg-green-900/80 border-green-700 text-green-200"
              : notification.type === "error"
              ? "bg-red-900/80 border-red-700 text-red-200"
              : "bg-blue-900/80 border-blue-700 text-blue-200"
          }`}
        >
          <div className="flex items-center gap-3">
            <span className="text-sm">{notification.message}</span>
            <button onClick={clearNotification} className="text-xs opacity-60 hover:opacity-100">✕</button>
          </div>
        </div>
      )}
    </>
  );
}
