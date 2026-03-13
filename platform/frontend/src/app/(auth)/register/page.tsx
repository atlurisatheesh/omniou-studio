"use client";
import { useState } from "react";
import Link from "next/link";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (password !== confirm) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: name }),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Registration failed");
        return;
      }

      // Auto-login after register
      const loginRes = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (loginRes.ok) {
        const data = await loginRes.json();
        localStorage.setItem("token", data.access_token);
        window.location.href = "/dashboard";
      } else {
        window.location.href = "/login";
      }
    } catch {
      setError("Connection error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-2xl p-8">
      <h2 className="text-xl font-bold text-white mb-6">Create your account</h2>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-600/20 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleRegister} className="space-y-4">
        <div>
          <label className="text-sm text-surface-400">Full Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full mt-1 bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500"
            placeholder="John Doe"
          />
        </div>

        <div>
          <label className="text-sm text-surface-400">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full mt-1 bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label className="text-sm text-surface-400">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="w-full mt-1 bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500"
            placeholder="••••••••"
          />
        </div>

        <div>
          <label className="text-sm text-surface-400">Confirm Password</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
            className="w-full mt-1 bg-[#12121a] border border-[#2a2a4a] rounded-lg px-4 py-2.5 text-white placeholder:text-surface-600 focus:outline-none focus:border-brand-500"
            placeholder="••••••••"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg bg-gradient-to-r from-brand-600 to-purple-600 hover:from-brand-700 hover:to-purple-700 text-white font-semibold disabled:opacity-50 transition"
        >
          {loading ? "Creating account..." : "Create Account — Free Plan"}
        </button>
      </form>

      <p className="text-xs text-surface-600 text-center mt-4">
        By signing up, you agree to our Terms of Service and Privacy Policy.
      </p>

      <p className="text-sm text-surface-500 text-center mt-4">
        Already have an account?{" "}
        <Link href="/login" className="text-brand-400 hover:text-brand-300">
          Sign in
        </Link>
      </p>
    </div>
  );
}
