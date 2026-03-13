"use client";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import { useStore } from "@/store";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { sidebarCollapsed } = useStore();

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <Sidebar />
      <div className={`transition-all duration-300 ${sidebarCollapsed ? "ml-[68px]" : "ml-[240px]"}`}>
        <Topbar />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
