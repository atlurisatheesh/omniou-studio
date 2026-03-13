"use client";

import Link from "next/link";
import {
  Bug,
  Droplets,
  CloudSun,
  CalendarDays,
  IndianRupee,
  Users,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";

const quickLinks = [
  {
    title: "Scan Crop Disease",
    desc: "Upload a photo for instant diagnosis",
    icon: Bug,
    href: "/dashboard/disease-detection",
    color: "bg-red-500",
  },
  {
    title: "Soil Analysis",
    desc: "Get fertilizer recommendations",
    icon: Droplets,
    href: "/dashboard/soil-health",
    color: "bg-amber-600",
  },
  {
    title: "Weather Forecast",
    desc: "7-day forecast & pest alerts",
    icon: CloudSun,
    href: "/dashboard/weather",
    color: "bg-blue-500",
  },
  {
    title: "Crop Calendar",
    desc: "Track your crop schedule",
    icon: CalendarDays,
    href: "/dashboard/crop-calendar",
    color: "bg-green-600",
  },
  {
    title: "Market Prices",
    desc: "Check today's mandi rates",
    icon: IndianRupee,
    href: "/dashboard/market-prices",
    color: "bg-purple-500",
  },
  {
    title: "Community",
    desc: "Ask experts & share knowledge",
    icon: Users,
    href: "/dashboard/community",
    color: "bg-teal-500",
  },
];

const recentAlerts = [
  {
    type: "pest",
    message: "Rice Blast risk HIGH — humid conditions expected next 3 days",
    time: "2 hours ago",
  },
  {
    type: "market",
    message: "Tomato prices up 12% at Azadpur Mandi",
    time: "5 hours ago",
  },
  {
    type: "calendar",
    message: "Wheat: Time for first irrigation (CRI stage, Day 21)",
    time: "Today",
  },
];

export default function DashboardPage() {
  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome to AgriSense
        </h1>
        <p className="text-gray-500 mt-1">
          Your agricultural intelligence dashboard
        </p>
      </div>

      {/* Quick Links Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-10">
        {quickLinks.map((link) => (
          <Link
            key={link.title}
            href={link.href}
            className="group bg-white rounded-xl border border-gray-100 p-6 card-hover"
          >
            <div className="flex items-start gap-4">
              <div
                className={`${link.color} w-12 h-12 rounded-xl flex items-center justify-center shrink-0`}
              >
                <link.icon className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 group-hover:text-agri-600 transition mb-1">
                  {link.title}
                </h3>
                <p className="text-sm text-gray-500">{link.desc}</p>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-agri-500 transition shrink-0 mt-1" />
            </div>
          </Link>
        ))}
      </div>

      {/* Alerts + Stats */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Alerts */}
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h2 className="font-bold text-lg text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Recent Alerts
          </h2>
          <div className="space-y-4">
            {recentAlerts.map((alert, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-lg bg-gray-50"
              >
                <div
                  className={`w-2 h-2 rounded-full mt-2 shrink-0 ${
                    alert.type === "pest"
                      ? "bg-red-500"
                      : alert.type === "market"
                      ? "bg-green-500"
                      : "bg-blue-500"
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-700">{alert.message}</p>
                  <p className="text-xs text-gray-400 mt-1">{alert.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h2 className="font-bold text-lg text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-agri-500" />
            Platform Stats
          </h2>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "Crops Supported", value: "7", sub: "Major Indian crops" },
              { label: "Diseases", value: "15+", sub: "Detection ready" },
              { label: "Commodities", value: "10", sub: "Live price tracking" },
              { label: "Soil Parameters", value: "11", sub: "ICAR standards" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-agri-50 rounded-lg p-4 text-center"
              >
                <div className="text-2xl font-bold text-agri-700">
                  {stat.value}
                </div>
                <div className="text-sm font-medium text-gray-700">
                  {stat.label}
                </div>
                <div className="text-xs text-gray-400">{stat.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
