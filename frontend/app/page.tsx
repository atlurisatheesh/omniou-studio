"use client";

import Link from "next/link";
import {
  Leaf,
  Bug,
  Droplets,
  CloudSun,
  CalendarDays,
  IndianRupee,
  Users,
  ArrowRight,
  Smartphone,
} from "lucide-react";

const features = [
  {
    icon: Bug,
    title: "Disease Detection",
    desc: "Snap a photo of your crop — get instant diagnosis with treatment recommendations",
    color: "bg-red-50 text-red-600",
    href: "/dashboard/disease-detection",
  },
  {
    icon: Droplets,
    title: "Soil Health Analysis",
    desc: "Enter your soil test values — get precise fertilizer recommendations per crop",
    color: "bg-amber-50 text-amber-700",
    href: "/dashboard/soil-health",
  },
  {
    icon: CloudSun,
    title: "Weather & Pest Forecast",
    desc: "7-day weather forecast with pest risk alerts and spray window suggestions",
    color: "bg-blue-50 text-blue-600",
    href: "/dashboard/weather",
  },
  {
    icon: CalendarDays,
    title: "Crop Calendar",
    desc: "Day-by-day growing schedule for your crop — never miss a critical activity",
    color: "bg-green-50 text-green-700",
    href: "/dashboard/crop-calendar",
  },
  {
    icon: IndianRupee,
    title: "Market Prices",
    desc: "Live mandi prices, MSP comparison, and intelligent selling advisory",
    color: "bg-purple-50 text-purple-600",
    href: "/dashboard/market-prices",
  },
  {
    icon: Users,
    title: "Farmer Community",
    desc: "Ask questions, share knowledge, and connect with experts and fellow farmers",
    color: "bg-teal-50 text-teal-600",
    href: "/dashboard/community",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <header className="relative bg-gradient-to-br from-agri-800 via-agri-700 to-agri-900 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-agri-400 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-20 w-96 h-96 bg-agri-300 rounded-full blur-3xl" />
        </div>

        <nav className="relative z-10 flex items-center justify-between max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center gap-2">
            <Leaf className="w-8 h-8 text-agri-300" />
            <span className="text-2xl font-bold tracking-tight">AgriSense</span>
          </div>
          <div className="flex gap-4">
            <Link
              href="/login"
              className="px-5 py-2 rounded-lg border border-white/30 hover:bg-white/10 transition"
            >
              Log In
            </Link>
            <Link
              href="/dashboard"
              className="px-5 py-2 rounded-lg bg-white text-agri-800 font-semibold hover:bg-agri-100 transition"
            >
              Dashboard
            </Link>
          </div>
        </nav>

        <div className="relative z-10 max-w-7xl mx-auto px-6 pt-16 pb-24 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-agri-600/40 border border-agri-400/30 text-agri-200 text-sm mb-6">
            <Smartphone className="w-4 h-4" />
            AI-Powered Agriculture
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-6">
            Farm Smarter
            <br />
            <span className="text-agri-300">with AgriSense</span>
          </h1>
          <p className="text-xl text-agri-200 max-w-2xl mx-auto mb-10">
            India&apos;s most comprehensive agricultural intelligence platform.
            Disease detection, soil analysis, weather forecasts, crop calendar,
            market prices & community — all in one place.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-agri-800 font-bold rounded-xl hover:bg-agri-100 transition text-lg"
            >
              Get Started <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Features Grid */}
      <section className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Everything Your Farm Needs
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            6 powerful tools designed by agricultural scientists with 50+ years
            of field experience, built for Indian farming conditions
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((f) => (
            <Link
              key={f.title}
              href={f.href}
              className="group bg-white rounded-2xl p-8 border border-gray-100 card-hover"
            >
              <div
                className={`w-14 h-14 rounded-xl ${f.color} flex items-center justify-center mb-5`}
              >
                <f.icon className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold mb-2 group-hover:text-agri-600 transition">
                {f.title}
              </h3>
              <p className="text-gray-500 leading-relaxed">{f.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Stats */}
      <section className="bg-agri-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { n: "7+", l: "Crops Supported" },
            { n: "15+", l: "Diseases Detected" },
            { n: "10", l: "Market Commodities" },
            { n: "100%", l: "Free for Farmers" },
          ].map((s) => (
            <div key={s.l}>
              <div className="text-4xl font-extrabold text-agri-300 mb-1">
                {s.n}
              </div>
              <div className="text-agri-200 text-sm">{s.l}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Leaf className="w-5 h-5 text-agri-500" />
            <span className="font-semibold text-white">AgriSense</span>
          </div>
          <p className="text-sm">
            &copy; {new Date().getFullYear()} AgriSense. Built for Indian
            farmers.
          </p>
        </div>
      </footer>
    </div>
  );
}
