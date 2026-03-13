import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In — Ominou Studio",
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-brand-400 to-purple-400 bg-clip-text text-transparent">
            Ominou Studio
          </h1>
          <p className="text-surface-500 text-sm mt-1">All-in-one AI creative platform</p>
        </div>
        {children}
      </div>
    </div>
  );
}
