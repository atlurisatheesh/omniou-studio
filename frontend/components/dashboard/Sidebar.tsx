"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Leaf,
  LayoutDashboard,
  Bug,
  Droplets,
  CloudSun,
  CalendarDays,
  IndianRupee,
  Users,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import { useStore } from "@/lib/store";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/disease-detection", label: "Disease Detection", icon: Bug },
  { href: "/dashboard/soil-health", label: "Soil Health", icon: Droplets },
  { href: "/dashboard/weather", label: "Weather & Pests", icon: CloudSun },
  { href: "/dashboard/crop-calendar", label: "Crop Calendar", icon: CalendarDays },
  { href: "/dashboard/market-prices", label: "Market Prices", icon: IndianRupee },
  { href: "/dashboard/community", label: "Community", icon: Users },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar, logout } = useStore();

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={toggleSidebar}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md"
        aria-label="Toggle sidebar"
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/30 z-30"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full z-40 w-64 bg-white border-r border-gray-200 flex flex-col transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-6 py-5 border-b border-gray-100">
          <Leaf className="w-7 h-7 text-agri-600" />
          <span className="text-xl font-bold text-agri-800 tracking-tight">
            AgriSense
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => {
                  if (window.innerWidth < 1024) toggleSidebar();
                }}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg mb-1 text-sm font-medium transition-colors ${
                  active
                    ? "bg-agri-50 text-agri-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                <item.icon
                  className={`w-5 h-5 ${active ? "text-agri-600" : "text-gray-400"}`}
                />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-100">
          <button
            onClick={logout}
            className="flex items-center gap-2 w-full px-4 py-2 rounded-lg text-sm text-gray-500 hover:bg-red-50 hover:text-red-600 transition"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}
