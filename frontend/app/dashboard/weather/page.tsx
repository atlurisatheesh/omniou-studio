"use client";

import { useState, useEffect } from "react";
import {
  CloudSun,
  Thermometer,
  Droplets,
  Wind,
  Bug,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { api } from "@/lib/api";

interface WeatherData {
  current: {
    temp_c: number;
    feels_like_c: number;
    humidity_pct: number;
    wind_speed_kmh: number;
    description: string;
    icon: string;
    rain_mm: number;
  };
  forecast: Array<{
    date: string;
    temp_max_c: number;
    temp_min_c: number;
    humidity_pct: number;
    rain_mm: number;
    description: string;
    icon: string;
    spray_window: boolean;
    spray_reason: string;
  }>;
  pest_risks: Array<{
    pest: string;
    risk: string;
    crops: string[];
    advisory: string;
  }>;
}

export default function WeatherPage() {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [sprayWindows, setSprayWindows] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadWeather();
  }, []);

  const loadWeather = async () => {
    setLoading(true);
    try {
      const [w, s] = await Promise.all([
        api.weather.forecast(),
        api.weather.sprayWindow(),
      ]);
      setWeather(w as WeatherData);
      setSprayWindows((s as { spray_windows: Array<Record<string, unknown>> }).spray_windows || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load weather");
    } finally {
      setLoading(false);
    }
  };

  const riskColor = (risk: string) => {
    if (risk.toLowerCase() === "high") return "bg-red-50 text-red-700 border-red-200";
    if (risk.toLowerCase() === "medium") return "bg-amber-50 text-amber-700 border-amber-200";
    return "bg-green-50 text-green-700 border-green-200";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-agri-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-xl">
        <AlertTriangle className="w-5 h-5" /> {error}
      </div>
    );
  }

  return (
    <div className="animate-fade-in max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <CloudSun className="w-8 h-8 text-blue-500" />
          Weather & Pest Forecast
        </h1>
        <p className="text-gray-500 mt-1">
          7-day forecast with pest risk alerts and spray window recommendations
        </p>
      </div>

      {weather && (
        <>
          {/* Current Weather */}
          <div className="bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl p-8 text-white mb-8">
            <div className="flex items-center justify-between flex-wrap gap-6">
              <div>
                <p className="text-blue-200 text-sm mb-1">Current Weather</p>
                <div className="text-6xl font-extrabold">
                  {weather.current.temp_c}°C
                </div>
                <p className="text-blue-100 text-lg capitalize mt-1">
                  {weather.current.description}
                </p>
              </div>
              <div className="grid grid-cols-3 gap-6">
                <div className="text-center">
                  <Droplets className="w-6 h-6 mx-auto mb-1 text-blue-200" />
                  <div className="text-2xl font-bold">
                    {weather.current.humidity_pct}%
                  </div>
                  <p className="text-blue-200 text-xs">Humidity</p>
                </div>
                <div className="text-center">
                  <Wind className="w-6 h-6 mx-auto mb-1 text-blue-200" />
                  <div className="text-2xl font-bold">
                    {weather.current.wind_speed_kmh}
                  </div>
                  <p className="text-blue-200 text-xs">km/h Wind</p>
                </div>
                <div className="text-center">
                  <Droplets className="w-6 h-6 mx-auto mb-1 text-blue-200" />
                  <div className="text-2xl font-bold">
                    {weather.current.rain_mm}
                  </div>
                  <p className="text-blue-200 text-xs">mm Rain</p>
                </div>
              </div>
            </div>
          </div>

          {/* 7-Day Forecast */}
          <div className="bg-white rounded-xl border border-gray-100 p-6 mb-8">
            <h2 className="font-bold text-lg text-gray-900 mb-4">
              7-Day Forecast
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {weather.forecast.map((day, i) => (
                <div
                  key={i}
                  className="bg-gray-50 rounded-xl p-4 text-center"
                >
                  <p className="text-xs text-gray-500 font-medium mb-2">
                    {new Date(day.date).toLocaleDateString("en-IN", {
                      weekday: "short",
                    })}
                  </p>
                  <div className="flex items-center justify-center gap-1 mb-2">
                    <Thermometer className="w-4 h-4 text-red-400" />
                    <span className="font-bold text-gray-800">
                      {day.temp_max_c}°
                    </span>
                    <span className="text-gray-400 text-sm">
                      {day.temp_min_c}°
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 capitalize mb-1">
                    {day.description}
                  </p>
                  <div className="flex items-center justify-center gap-1 text-xs text-blue-500">
                    <Droplets className="w-3 h-3" />
                    {day.rain_mm}mm
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pest Risks */}
          {weather.pest_risks.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-100 p-6 mb-8">
              <h2 className="font-bold text-lg text-gray-900 mb-4 flex items-center gap-2">
                <Bug className="w-5 h-5 text-red-500" />
                Pest Risk Alerts
              </h2>
              <div className="space-y-3">
                {weather.pest_risks.map((risk, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-4 p-4 rounded-xl border ${riskColor(
                      risk.risk
                    )}`}
                  >
                    <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold">
                        {risk.pest}{" "}
                        <span className="text-xs font-bold uppercase ml-1">
                          [{risk.risk}]
                        </span>
                      </div>
                      <p className="text-sm mt-0.5 opacity-80">
                        {risk.advisory}
                      </p>
                      <p className="text-xs mt-1">
                        Affects: {risk.crops.join(", ")}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Spray Windows */}
          {sprayWindows.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h2 className="font-bold text-lg text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-agri-500" />
                Spray Windows
              </h2>
              <div className="space-y-3">
                {sprayWindows.map((win, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-4 bg-agri-50 rounded-lg"
                  >
                    <CheckCircle2 className="w-5 h-5 text-agri-600 shrink-0 mt-0.5" />
                    <div>
                      <div className="font-medium text-gray-800">
                        {String(win.date || "")} — {win.safe_to_spray ? "Safe to spray" : String(win.reason || "Not recommended")}
                      </div>
                      <p className="text-sm text-gray-500">
                        Rain: {String(win.rain_mm || 0)} mm | Humidity:{" "}
                        {String(win.humidity_pct || "")}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
