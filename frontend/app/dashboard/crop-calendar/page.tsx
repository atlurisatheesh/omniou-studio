"use client";

import { useState, useEffect } from "react";
import {
  CalendarDays,
  Loader2,
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";

interface CropInfo {
  name: string;
  duration_days: number;
}

interface Activity {
  activity: string;
  day: number;
  details: string;
  upcoming: boolean;
}

interface Stage {
  stage: string;
  activities: Activity[];
}

export default function CropCalendarPage() {
  const [crops, setCrops] = useState<CropInfo[]>([]);
  const [selectedCrop, setSelectedCrop] = useState("");
  const [stages, setStages] = useState<Stage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sowingDate, setSowingDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [created, setCreated] = useState(false);

  useEffect(() => {
    api.calendar.crops().then((r) => setCrops(r.crops));
  }, []);

  const loadCalendar = async (crop: string) => {
    setSelectedCrop(crop);
    setLoading(true);
    setCreated(false);
    try {
      const res = await api.calendar.activities(crop);
      setStages(res.stages);
    } catch {
      setStages([]);
    } finally {
      setLoading(false);
    }
  };

  const createCalendar = async () => {
    if (!selectedCrop || !sowingDate) return;
    try {
      await api.calendar.create(selectedCrop, sowingDate);
      setCreated(true);
    } catch {
      // ignore
    }
  };

  const stageColors = [
    "border-green-400 bg-green-50",
    "border-blue-400 bg-blue-50",
    "border-amber-400 bg-amber-50",
    "border-purple-400 bg-purple-50",
    "border-red-400 bg-red-50",
    "border-teal-400 bg-teal-50",
    "border-pink-400 bg-pink-50",
  ];

  return (
    <div className="animate-fade-in max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <CalendarDays className="w-8 h-8 text-green-600" />
          Crop Calendar
        </h1>
        <p className="text-gray-500 mt-1">
          Day-by-day growing schedule with activities, inputs, and timing for
          your crop
        </p>
      </div>

      {/* Crop Selection */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-3">
          Select Crop
        </label>
        <div className="flex flex-wrap gap-2 mb-4">
          {crops.map((crop) => (
            <button
              key={crop.name}
              onClick={() => loadCalendar(crop.name)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${
                selectedCrop === crop.name
                  ? "bg-green-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {crop.name}{" "}
              <span className="text-xs opacity-70">({crop.duration_days}d)</span>
            </button>
          ))}
        </div>

        {selectedCrop && (
          <div className="flex items-end gap-4 pt-4 border-t border-gray-100">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Sowing Date
              </label>
              <input
                type="date"
                value={sowingDate}
                onChange={(e) => setSowingDate(e.target.value)}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-green-500"
              />
            </div>
            <button
              onClick={createCalendar}
              className="px-5 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition text-sm"
            >
              Save Calendar
            </button>
            {created && (
              <span className="text-green-600 text-sm flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" /> Saved!
              </span>
            )}
          </div>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="w-8 h-8 animate-spin text-green-500" />
        </div>
      )}

      {/* Timeline */}
      {!loading && stages.length > 0 && (
        <div className="space-y-6">
          {stages.map((stage, si) => (
            <div key={si} className="relative">
              {/* Stage Header */}
              <div
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold border-2 mb-4 ${
                  stageColors[si % stageColors.length]
                }`}
              >
                <CalendarDays className="w-4 h-4" />
                {stage.stage}
              </div>

              {/* Activities */}
              <div className="ml-6 border-l-2 border-gray-200 pl-6 space-y-3">
                {stage.activities.map((act, ai) => (
                  <div
                    key={ai}
                    className={`relative bg-white rounded-xl border p-4 ${
                      act.upcoming
                        ? "border-green-300 ring-2 ring-green-100"
                        : "border-gray-100"
                    }`}
                  >
                    {/* Dot on timeline */}
                    <div
                      className={`absolute -left-[33px] top-5 w-3 h-3 rounded-full border-2 border-white ${
                        act.upcoming ? "bg-green-500" : "bg-gray-300"
                      }`}
                    />

                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-800">
                            {act.activity}
                          </span>
                          {act.upcoming && (
                            <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                              UPCOMING
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          {act.details}
                        </p>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-400 shrink-0 ml-4">
                        <Clock className="w-3.5 h-3.5" />
                        Day {act.day}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && selectedCrop && stages.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-3" />
          <p>No calendar data available for this crop</p>
        </div>
      )}
    </div>
  );
}
