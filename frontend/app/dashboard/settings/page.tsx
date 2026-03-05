"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Video,
  Mic,
  Camera,
  LayoutDashboard,
  Settings as SettingsIcon,
  CreditCard,
  LogOut,
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Save,
  Check,
} from "lucide-react";

export default function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState({
    name: "Demo User",
    email: "demo@cloneai.pro",
    language: "en",
    theme: "dark",
    notifications: {
      email: true,
      videoComplete: true,
      newsletter: false,
    },
    privacy: {
      deleteDataOnCancel: true,
      shareAnalytics: false,
    },
  });

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

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
            { icon: Camera, label: "Avatars", href: "/dashboard/avatars", active: false },
            { icon: SettingsIcon, label: "Settings", href: "/dashboard/settings", active: true },
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
      <main className="flex-1 p-6 md:p-10 max-w-3xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Settings</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Manage your account and preferences
            </p>
          </div>
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-xl font-semibold text-sm hover:bg-primary/90 transition"
          >
            {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {saved ? "Saved!" : "Save Changes"}
          </button>
        </div>

        <div className="space-y-6">
          {/* Profile Section */}
          <section className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold">Profile</h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Display Name
                </label>
                <input
                  type="text"
                  value={settings.name}
                  onChange={(e) => setSettings({ ...settings, name: e.target.value })}
                  className="w-full bg-background border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  value={settings.email}
                  onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                  className="w-full bg-background border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
            </div>
          </section>

          {/* Appearance */}
          <section className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Palette className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold">Appearance</h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Theme
                </label>
                <select
                  value={settings.theme}
                  onChange={(e) => setSettings({ ...settings, theme: e.target.value })}
                  className="w-full bg-background border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="system">System</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                  Default Language
                </label>
                <select
                  value={settings.language}
                  onChange={(e) => setSettings({ ...settings, language: e.target.value })}
                  className="w-full bg-background border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="pt">Portuguese</option>
                  <option value="hi">Hindi</option>
                  <option value="zh">Chinese</option>
                  <option value="ja">Japanese</option>
                  <option value="ko">Korean</option>
                </select>
              </div>
            </div>
          </section>

          {/* Notifications */}
          <section className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Bell className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold">Notifications</h2>
            </div>
            <div className="space-y-3">
              {[
                { key: "email" as const, label: "Email notifications", desc: "Receive updates via email" },
                { key: "videoComplete" as const, label: "Video completion alerts", desc: "Get notified when your video is ready" },
                { key: "newsletter" as const, label: "Newsletter", desc: "Receive product updates and tips" },
              ].map((item) => (
                <label
                  key={item.key}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-secondary/50 transition cursor-pointer"
                >
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
                  </div>
                  <div
                    onClick={(e) => {
                      e.preventDefault();
                      setSettings({
                        ...settings,
                        notifications: {
                          ...settings.notifications,
                          [item.key]: !settings.notifications[item.key],
                        },
                      });
                    }}
                    className={`w-10 h-6 rounded-full flex items-center px-1 transition cursor-pointer ${
                      settings.notifications[item.key] ? "bg-primary" : "bg-border"
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform ${
                        settings.notifications[item.key] ? "translate-x-4" : "translate-x-0"
                      }`}
                    />
                  </div>
                </label>
              ))}
            </div>
          </section>

          {/* Privacy */}
          <section className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold">Privacy & Data</h2>
            </div>
            <div className="space-y-3">
              {[
                { key: "deleteDataOnCancel" as const, label: "Delete data on account cancellation", desc: "All uploads and generated content will be permanently deleted" },
                { key: "shareAnalytics" as const, label: "Share anonymous usage analytics", desc: "Help us improve CloneAI Pro (no personal data is shared)" },
              ].map((item) => (
                <label
                  key={item.key}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-secondary/50 transition cursor-pointer"
                >
                  <div>
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
                  </div>
                  <div
                    onClick={(e) => {
                      e.preventDefault();
                      setSettings({
                        ...settings,
                        privacy: {
                          ...settings.privacy,
                          [item.key]: !settings.privacy[item.key],
                        },
                      });
                    }}
                    className={`w-10 h-6 rounded-full flex items-center px-1 transition cursor-pointer ${
                      settings.privacy[item.key] ? "bg-primary" : "bg-border"
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded-full bg-white transition-transform ${
                        settings.privacy[item.key] ? "translate-x-4" : "translate-x-0"
                      }`}
                    />
                  </div>
                </label>
              ))}
            </div>

            <div className="mt-6 pt-4 border-t border-border">
              <button className="px-4 py-2 bg-red-500/10 text-red-400 rounded-lg text-sm font-medium hover:bg-red-500/20 transition">
                Delete Account
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
