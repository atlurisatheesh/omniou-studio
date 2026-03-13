"use client";
import { useState } from "react";

const plans = [
  { id: "free", name: "Free", price: 0, credits: 50, features: ["50 credits/month", "Basic voice & text", "720p exports", "Community support"] },
  { id: "pro", name: "Pro", price: 29, credits: 2000, features: ["2,000 credits/month", "All studios", "4K exports", "API access", "Priority support"], popular: true },
  { id: "team", name: "Team", price: 79, credits: 10000, features: ["10,000 credits/month", "5 team seats", "Custom models", "Workflow automation", "Dedicated support"] },
  { id: "enterprise", name: "Enterprise", price: -1, credits: -1, features: ["Unlimited credits", "Unlimited seats", "On-premise option", "Custom integrations", "SLA guarantee"] },
];

export default function SettingsPage() {
  const [tab, setTab] = useState<"profile" | "billing" | "api" | "team">("profile");
  const [name, setName] = useState("John Doe");
  const [email, setEmail] = useState("john@example.com");

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold">⚙️ Settings</h1>
        <p className="text-surface-500 mt-1">Manage your account, billing, and API keys</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[#2a2a4a] pb-0">
        {(["profile", "billing", "api", "team"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium transition border-b-2 -mb-[1px] ${
              tab === t ? "border-brand-500 text-white" : "border-transparent text-surface-500 hover:text-white"
            }`}
          >
            {t === "profile" ? "👤 Profile" : t === "billing" ? "💳 Billing" : t === "api" ? "🔑 API Keys" : "👥 Team"}
          </button>
        ))}
      </div>

      {tab === "profile" && (
        <div className="space-y-6">
          <div className="glass rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Profile Information</h3>
            <div className="flex items-center gap-6 mb-6">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white">
                JD
              </div>
              <button className="px-4 py-2 rounded-lg bg-[#1a1a2e] text-surface-300 text-sm hover:text-white transition">
                Change Avatar
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-surface-400">Full Name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} className="w-full mt-1 bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500" />
              </div>
              <div>
                <label className="text-sm text-surface-400">Email</label>
                <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full mt-1 bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-brand-500" />
              </div>
            </div>
            <button className="mt-4 px-6 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 transition">
              Save Changes
            </button>
          </div>

          <div className="glass rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Change Password</h3>
            <div className="space-y-3 max-w-sm">
              <input type="password" placeholder="Current password" className="w-full bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500" />
              <input type="password" placeholder="New password" className="w-full bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500" />
              <input type="password" placeholder="Confirm new password" className="w-full bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500" />
            </div>
            <button className="mt-4 px-6 py-2.5 rounded-lg bg-[#1a1a2e] text-surface-300 text-sm hover:text-white transition">
              Update Password
            </button>
          </div>

          <div className="glass rounded-xl p-6 border border-red-500/20">
            <h3 className="text-lg font-semibold text-red-400 mb-2">Danger Zone</h3>
            <p className="text-sm text-surface-400 mb-4">Once you delete your account, there is no going back.</p>
            <button className="px-4 py-2 rounded-lg bg-red-600/20 text-red-400 text-sm hover:bg-red-600/30 transition">
              Delete Account
            </button>
          </div>
        </div>
      )}

      {tab === "billing" && (
        <div className="space-y-6">
          <div className="glass rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">Current Plan</h3>
                <p className="text-surface-400 text-sm">You are on the <span className="text-brand-400 font-medium">Free</span> plan</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-white">35 <span className="text-sm text-surface-400">/ 50 credits</span></p>
                <p className="text-xs text-surface-500">Resets in 18 days</p>
              </div>
            </div>
            <div className="h-2 bg-[#1a1a2e] rounded-full">
              <div className="h-full w-[70%] bg-brand-500 rounded-full" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {plans.map((plan) => (
              <div key={plan.id} className={`glass rounded-xl p-5 ${plan.popular ? "border border-brand-500/50 ring-1 ring-brand-500/20" : ""}`}>
                {plan.popular && <p className="text-xs text-brand-400 font-medium mb-2">Most Popular</p>}
                <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                <p className="text-2xl font-bold text-white mt-1">
                  {plan.price === -1 ? "Custom" : `$${plan.price}`}
                  {plan.price > 0 && <span className="text-sm text-surface-400">/mo</span>}
                </p>
                <ul className="mt-4 space-y-2">
                  {plan.features.map((f, i) => (
                    <li key={i} className="text-sm text-surface-400 flex items-center gap-2">
                      <span className="text-green-400">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <button className={`w-full mt-4 py-2 rounded-lg text-sm font-medium transition ${
                  plan.popular ? "bg-brand-600 text-white hover:bg-brand-700" :
                  plan.id === "free" ? "bg-[#1a1a2e] text-surface-400 cursor-default" :
                  "bg-[#1a1a2e] text-surface-300 hover:text-white"
                }`}>
                  {plan.id === "free" ? "Current Plan" : plan.price === -1 ? "Contact Sales" : "Upgrade"}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "api" && (
        <div className="space-y-6">
          <div className="glass rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">API Keys</h3>
              <button className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm">+ Create Key</button>
            </div>
            <div className="space-y-3">
              <div className="bg-[#12121a] rounded-lg p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-white font-medium">Production Key</p>
                  <p className="text-xs text-surface-500 font-mono mt-1">sk-omni-****************************3f8a</p>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 rounded text-xs bg-[#1a1a2e] text-surface-400">Copy</button>
                  <button className="px-3 py-1 rounded text-xs bg-red-600/20 text-red-400">Revoke</button>
                </div>
              </div>
              <div className="bg-[#12121a] rounded-lg p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-white font-medium">Development Key</p>
                  <p className="text-xs text-surface-500 font-mono mt-1">sk-omni-****************************9b2c</p>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 rounded text-xs bg-[#1a1a2e] text-surface-400">Copy</button>
                  <button className="px-3 py-1 rounded text-xs bg-red-600/20 text-red-400">Revoke</button>
                </div>
              </div>
            </div>
          </div>

          <div className="glass rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-3">API Usage</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-[#12121a] rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-white">1,247</p>
                <p className="text-xs text-surface-500">Requests today</p>
              </div>
              <div className="bg-[#12121a] rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-white">42ms</p>
                <p className="text-xs text-surface-500">Avg latency</p>
              </div>
              <div className="bg-[#12121a] rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-white">99.9%</p>
                <p className="text-xs text-surface-500">Uptime</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === "team" && (
        <div className="glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Team Members</h3>
            <button className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm">+ Invite Member</button>
          </div>
          <div className="space-y-3">
            <div className="bg-[#12121a] rounded-lg p-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-sm font-bold text-white">JD</div>
              <div className="flex-1">
                <p className="text-sm text-white font-medium">John Doe (You)</p>
                <p className="text-xs text-surface-500">john@example.com</p>
              </div>
              <span className="px-3 py-1 rounded-full text-xs bg-brand-600/20 text-brand-400">Owner</span>
            </div>
          </div>
          <p className="text-sm text-surface-500 mt-4">Upgrade to Team plan to invite up to 5 members.</p>
        </div>
      )}
    </div>
  );
}
