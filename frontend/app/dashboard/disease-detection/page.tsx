"use client";

import { useState, useRef } from "react";
import {
  Camera,
  Upload,
  Bug,
  Loader2,
  AlertCircle,
  CheckCircle2,
  FlaskConical,
  Leaf,
  Shield,
} from "lucide-react";
import { api } from "@/lib/api";

const CROPS = ["rice", "wheat", "tomato", "cotton", "potato", "maize", "sugarcane"];

interface DiseaseResult {
  disease: string;
  confidence: number;
  severity: string;
  treatment: {
    chemical: string[];
    organic: string[];
    prevention: string[];
  };
  scan_id: string;
}

export default function DiseaseDetectionPage() {
  const [selectedCrop, setSelectedCrop] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiseaseResult | null>(null);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError("");
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(ev.target?.result as string);
    reader.readAsDataURL(f);
  };

  const handleScan = async () => {
    if (!file || !selectedCrop) {
      setError("Please select a crop and upload an image");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await api.disease.scan(file, selectedCrop);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  };

  const severityColor = (s: string) => {
    if (s === "Severe") return "text-red-600 bg-red-50";
    if (s === "Moderate") return "text-amber-600 bg-amber-50";
    return "text-green-600 bg-green-50";
  };

  return (
    <div className="animate-fade-in max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Bug className="w-8 h-8 text-red-500" />
          Disease Detection
        </h1>
        <p className="text-gray-500 mt-1">
          Upload a photo of your crop leaf to get instant disease diagnosis and
          treatment recommendations
        </p>
      </div>

      {/* Crop Selection */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          1. Select Your Crop
        </label>
        <div className="flex flex-wrap gap-2">
          {CROPS.map((crop) => (
            <button
              key={crop}
              onClick={() => setSelectedCrop(crop)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${
                selectedCrop === crop
                  ? "bg-agri-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {crop}
            </button>
          ))}
        </div>
      </div>

      {/* Image Upload */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          2. Upload Leaf Image
        </label>

        {preview ? (
          <div className="relative">
            <img
              src={preview}
              alt="Crop leaf preview"
              className="w-full max-h-80 object-contain rounded-lg bg-gray-50"
            />
            <button
              onClick={() => {
                setPreview(null);
                setFile(null);
                setResult(null);
              }}
              className="absolute top-3 right-3 bg-white/90 px-3 py-1 rounded-lg text-sm font-medium hover:bg-white"
            >
              Change
            </button>
          </div>
        ) : (
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-gray-200 rounded-xl p-12 text-center cursor-pointer hover:border-agri-400 hover:bg-agri-50/50 transition"
          >
            <Upload className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">
              Click to upload or drag & drop
            </p>
            <p className="text-sm text-gray-400 mt-1">
              JPG, PNG up to 10MB
            </p>
          </div>
        )}

        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Scan Button */}
      <button
        onClick={handleScan}
        disabled={loading || !file || !selectedCrop}
        className="w-full py-3.5 bg-agri-600 text-white font-bold rounded-xl hover:bg-agri-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2 mb-6"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" /> Analyzing...
          </>
        ) : (
          <>
            <Camera className="w-5 h-5" /> Scan for Disease
          </>
        )}
      </button>

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-xl mb-6">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Disease Info */}
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {result.disease}
                </h2>
                <p className="text-gray-500 capitalize">{selectedCrop}</p>
              </div>
              <span
                className={`px-3 py-1 rounded-full text-sm font-semibold ${severityColor(
                  result.severity
                )}`}
              >
                {result.severity}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-1 bg-gray-100 rounded-full h-3">
                <div
                  className="bg-agri-500 h-3 rounded-full transition-all"
                  style={{ width: `${result.confidence}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-600">
                {result.confidence.toFixed(1)}% confidence
              </span>
            </div>
          </div>

          {/* Treatment Cards */}
          <div className="grid md:grid-cols-3 gap-4">
            {/* Chemical */}
            <div className="bg-white rounded-xl border border-gray-100 p-5">
              <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                <FlaskConical className="w-5 h-5 text-blue-500" />
                Chemical Treatment
              </h3>
              <ul className="space-y-2">
                {result.treatment.chemical.map((t, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>

            {/* Organic */}
            <div className="bg-white rounded-xl border border-gray-100 p-5">
              <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Leaf className="w-5 h-5 text-green-500" />
                Organic Treatment
              </h3>
              <ul className="space-y-2">
                {result.treatment.organic.map((t, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>

            {/* Prevention */}
            <div className="bg-white rounded-xl border border-gray-100 p-5">
              <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Shield className="w-5 h-5 text-purple-500" />
                Prevention
              </h3>
              <ul className="space-y-2">
                {result.treatment.prevention.map((t, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle2 className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
