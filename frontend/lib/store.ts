import { create } from "zustand";

interface User {
  id: string;
  name: string;
  phone: string;
  region: string;
}

interface AppState {
  user: User | null;
  token: string | null;
  sidebarOpen: boolean;

  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  toggleSidebar: () => void;
  logout: () => void;
}

export const useStore = create<AppState>((set) => ({
  user: null,
  token:
    typeof window !== "undefined"
      ? localStorage.getItem("agri_token")
      : null,
  sidebarOpen: true,

  setUser: (user) => set({ user }),

  setToken: (token) => {
    if (token) {
      localStorage.setItem("agri_token", token);
    } else {
      localStorage.removeItem("agri_token");
    }
    set({ token });
  },

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  logout: () => {
    localStorage.removeItem("agri_token");
    set({ user: null, token: null });
  },
}));
