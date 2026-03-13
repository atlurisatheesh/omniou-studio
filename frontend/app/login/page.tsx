"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Leaf, Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useStore } from "@/lib/store";

export default function LoginPage() {
  const router = useRouter();
  const { setToken, setUser } = useStore();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [region, setRegion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (mode === "register") {
        await api.auth.register({ phone, password, name, region });
        setMode("login");
        setError("");
      }

      const res = await api.auth.login(phone, password);
      setToken(res.access_token);
      setUser(res.user as { id: string; name: string; phone: string; region: string });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-agri-800 via-agri-700 to-agri-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <Leaf className="w-10 h-10 text-agri-600" />
            <span className="text-3xl font-bold text-agri-800">AgriSense</span>
          </div>
          <p className="text-gray-500 text-sm">
            {mode === "login"
              ? "Sign in to your farm dashboard"
              : "Create your free account"}
          </p>
        </div>

        {/* Tabs */}
        <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
          <button
            onClick={() => setMode("login")}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
              mode === "login"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500"
            }`}
          >
            Login
          </button>
          <button
            onClick={() => setMode("register")}
            className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
              mode === "register"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500"
            }`}
          >
            Register
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg mb-4 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-agri-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Region
                </label>
                <input
                  type="text"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  placeholder="e.g., Punjab, Telangana"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-agri-500"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number
            </label>
            <input
              type="tel"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="10-digit mobile number"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-agri-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-agri-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-agri-600 text-white font-bold rounded-xl hover:bg-agri-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : mode === "login" ? (
              "Sign In"
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          Free for all Indian farmers. No charges ever.
        </p>
      </div>
    </div>
  );
}
