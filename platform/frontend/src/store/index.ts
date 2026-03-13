import { create } from "zustand";
import type { User, ModuleName } from "@/types";

interface StudioState {
  // Auth
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  // Navigation
  activeModule: ModuleName | "dashboard" | "assets" | "settings";
  sidebarCollapsed: boolean;

  // UI
  isLoading: boolean;
  notification: { type: "success" | "error" | "info"; message: string } | null;

  // Actions
  setUser: (user: User, token: string) => void;
  logout: () => void;
  setActiveModule: (module: ModuleName | "dashboard" | "assets" | "settings") => void;
  toggleSidebar: () => void;
  setLoading: (loading: boolean) => void;
  notify: (type: "success" | "error" | "info", message: string) => void;
  clearNotification: () => void;
  updateCredits: (credits: number) => void;
}

export const useStore = create<StudioState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  activeModule: "dashboard",
  sidebarCollapsed: false,
  isLoading: false,
  notification: null,

  setUser: (user, token) => {
    if (typeof window !== "undefined") localStorage.setItem("ominou_token", token);
    set({ user, token, isAuthenticated: true });
  },

  logout: () => {
    if (typeof window !== "undefined") localStorage.removeItem("ominou_token");
    set({ user: null, token: null, isAuthenticated: false });
  },

  setActiveModule: (module) => set({ activeModule: module }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setLoading: (loading) => set({ isLoading: loading }),

  notify: (type, message) => {
    set({ notification: { type, message } });
    setTimeout(() => set({ notification: null }), 4000);
  },

  clearNotification: () => set({ notification: null }),

  updateCredits: (credits) =>
    set((s) => (s.user ? { user: { ...s.user, credits_remaining: credits } } : {})),
}));
