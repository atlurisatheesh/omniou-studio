"use client";

import { useState } from "react";
import {
  Droplets,
  Loader2,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { api } from "@/lib/api";

interface SoilParam {
  parameter: string;
  value: number;
  unit: string;
  status: string;
  ideal_range: string;
}

interface SoilResult {
  overall_score: number;
  health_status: string;
  parameters: SoilParam[];
  recommendations: Array<{ crop: string; fertilizer: string; quantity: string }>;
}

const SOIL_FIELDS = [
  { key: "ph", label: "pH", placeholder: "6.5", unit: "" },
  { key: "nitrogen", label: "Nitrogen (N)", placeholder: "280", unit: "kg/ha" },
  { key: "phosphorus", label: "Phosphorus (P)", placeholder: "22", unit: "kg/ha" },
  { key: "potassium", label: "Potassium (K)", placeholder: "200", unit: "kg/ha" },
  { key: "organic_carbon", label: "Organic Carbon", placeholder: "0.6", unit: "%" },
  { key: "ec", label: "EC", placeholder: "0.5", unit: "dS/m" },
  { key: "zinc", label: "Zinc (Zn)", placeholder: "1.2", unit: "ppm" },
  { key: "iron", label: "Iron (Fe)", placeholder: "5.0", unit: "ppm" },
  { key: "manganese", label: "Manganese (Mn)", placeholder: "3.0", unit: "ppm" },
  { key: "boron", label: "Boron (B)", placeholder: "0.7", unit: "ppm" },
  { key: "sulphur", label: "Sulphur (S)", placeholder: "12", unit: "ppm" },
];

export default function SoilHealthPage() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SoilResult | null>(null);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    const data: Record<string, number> = {};
    for (const field of SOIL_FIELDS) {
      const v = parseFloat(values[field.key] || "");
      if (!isNaN(v)) data[field.key] = v;
    }

    if (Object.keys(data).length < 3) {
      setError("Please enter at least pH, N, P, K values");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const res = await api.soil.analyze(data);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const statusIcon = (status: string) => {
    if (status === "High") return <TrendingUp className="w-4 h-4 text-amber-500" />;
    if (status === "Low") return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-green-500" />;
  };

  const scoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <div className="animate-fade-in max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Droplets className="w-8 h-8 text-amber-600" />
          Soil Health Analysis
        </h1>
        <p className="text-gray-500 mt-1">
          Enter your soil test report values to get ICAR-standard analysis and
          crop-specific fertilizer recommendations
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 mb-6">
        <h2 className="font-semibold text-gray-700 mb-4">Soil Test Values</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {SOIL_FIELDS.map((field) => (
            <div key={field.key}>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                {field.label} {field.unit && `(${field.unit})`}
              </label>
              <input
                type="number"
                step="any"
                placeholder={field.placeholder}
                value={values[field.key] || ""}
                onChange={(e) =>
                  setValues((v) => ({ ...v, [field.key]: e.target.value }))
                }
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-agri-500 focus:border-agri-500"
              />
            </div>
          ))}
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="mt-6 w-full py-3 bg-amber-600 text-white font-bold rounded-xl hover:bg-amber-700 disabled:opacity-50 transition flex items-center justify-center gap-2"
        >
          {loading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing...</>
          ) : (
            <><Droplets className="w-5 h-5" /> Analyze Soil</>
          )}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-xl mb-6">
          <AlertCircle className="w-5 h-5 shrink-0" /> {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Score */}
          <div className="bg-white rounded-xl border border-gray-100 p-6 text-center">
            <div className={`text-6xl font-extrabold ${scoreColor(result.overall_score)}`}>
              {result.overall_score}
            </div>
            <div className="text-lg font-semibold text-gray-700 mt-1">
              {result.health_status}
            </div>
            <div className="w-full max-w-md mx-auto mt-4 bg-gray-100 rounded-full h-4">
              <div
                className={`h-4 rounded-full transition-all ${
                  result.overall_score >= 80
                    ? "bg-green-500"
                    : result.overall_score >= 60
                    ? "bg-amber-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${result.overall_score}%` }}
              />
            </div>
          </div>

          {/* Parameters Table */}
          <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-bold text-gray-900">Parameter Analysis</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-500">
                  <tr>
                    <th className="text-left px-6 py-3">Parameter</th>
                    <th className="text-left px-6 py-3">Your Value</th>
                    <th className="text-left px-6 py-3">Ideal Range</th>
                    <th className="text-left px-6 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {result.parameters.map((p) => (
                    <tr key={p.parameter} className="hover:bg-gray-50">
                      <td className="px-6 py-3 font-medium text-gray-700">
                        {p.parameter}
                      </td>
                      <td className="px-6 py-3">
                        {p.value} {p.unit}
                      </td>
                      <td className="px-6 py-3 text-gray-500">{p.ideal_range}</td>
                      <td className="px-6 py-3">
                        <span className="flex items-center gap-1.5">
                          {statusIcon(p.status)}
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-100 p-6">
              <h3 className="font-bold text-gray-900 mb-4">
                Fertilizer Recommendations
              </h3>
              <div className="grid md:grid-cols-2 gap-3">
                {result.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-4 bg-agri-50 rounded-lg"
                  >
                    <CheckCircle2 className="w-5 h-5 text-agri-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-gray-800 capitalize">
                        {rec.crop}:
                      </span>{" "}
                      <span className="text-gray-600">
                        {rec.fertilizer} — {rec.quantity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
