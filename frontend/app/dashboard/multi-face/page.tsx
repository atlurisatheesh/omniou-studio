"use client";

import { useState } from "react";
import { multiFace, uploadPhoto, uploadVoice } from "@/lib/api";
import {
  Users,
  Plus,
  Trash2,
  Upload,
  Play,
  Loader2,
  CheckCircle,
  AlertTriangle,
  LayoutGrid,
  List,
  Spotlight,
} from "lucide-react";

interface PersonEntry {
  id: string;
  name: string;
  faceFile: File | null;
  facePath: string | null;
  voiceFile: File | null;
  voicePath: string | null;
  script: string;
  language: string;
  emotion: string;
}

const LAYOUTS = [
  { value: "sequential", label: "Sequential", icon: List, desc: "Each person speaks in turn" },
  { value: "grid", label: "Grid", icon: LayoutGrid, desc: "All faces visible at once" },
  { value: "spotlight", label: "Spotlight", icon: Spotlight, desc: "Active speaker highlighted" },
];

function createPerson(): PersonEntry {
  return {
    id: crypto.randomUUID(),
    name: "",
    faceFile: null,
    facePath: null,
    voiceFile: null,
    voicePath: null,
    script: "",
    language: "en",
    emotion: "neutral",
  };
}

export default function MultiFacePage() {
  const [persons, setPersons] = useState<PersonEntry[]>([createPerson(), createPerson()]);
  const [layout, setLayout] = useState("sequential");
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("idle");
  const [jobProgress, setJobProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const updatePerson = (id: string, patch: Partial<PersonEntry>) => {
    setPersons((prev) => prev.map((p) => (p.id === id ? { ...p, ...patch } : p)));
  };

  const addPerson = () => {
    if (persons.length >= 6) return;
    setPersons((prev) => [...prev, createPerson()]);
  };

  const removePerson = (id: string) => {
    if (persons.length <= 2) return;
    setPersons((prev) => prev.filter((p) => p.id !== id));
  };

  const handleFileUpload = async (personId: string, type: "face" | "voice", file: File) => {
    updatePerson(personId, type === "face" ? { faceFile: file } : { voiceFile: file });
    try {
      const res = type === "face" ? await uploadPhoto(file) : await uploadVoice(file);
      updatePerson(personId, type === "face" ? { facePath: res.path } : { voicePath: res.path });
    } catch (err: any) {
      setError(`Upload failed: ${err.message}`);
    }
  };

  const handleGenerate = async () => {
    setError(null);

    // Validate
    for (const p of persons) {
      if (!p.facePath || !p.voicePath || !p.script.trim()) {
        setError("Each person needs a face photo, voice sample, and script.");
        return;
      }
    }

    setUploading(true);
    setJobStatus("processing");

    try {
      const specs = persons.map((p) => ({
        face_path: p.facePath!,
        voice_path: p.voicePath!,
        script: p.script,
        name: p.name || undefined,
        language: p.language,
        emotion: p.emotion,
      }));

      const result = await multiFace.create(specs, layout);
      setJobId(result.id);

      // Poll status
      const poll = setInterval(async () => {
        try {
          const status = await multiFace.status(result.id);
          setJobStatus(status.status);
          setJobProgress(status.progress || 0);
          if (status.status === "completed" || status.status === "failed") {
            clearInterval(poll);
            if (status.error) setError(status.error);
          }
        } catch {
          clearInterval(poll);
          setJobStatus("failed");
          setError("Status check failed");
        }
      }, 3000);
    } catch (err: any) {
      setError(err.message);
      setJobStatus("failed");
    } finally {
      setUploading(false);
    }
  };

  const isProcessing = jobStatus === "processing";
  const isCompleted = jobStatus === "completed";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Multi-Face Video</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Create group videos with multiple AI avatars
        </p>
      </div>

      {/* Layout selector */}
      <div>
        <label className="text-sm font-medium mb-3 block">Layout</label>
        <div className="grid grid-cols-3 gap-3">
          {LAYOUTS.map((l) => (
            <button
              key={l.value}
              onClick={() => setLayout(l.value)}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition ${
                layout === l.value
                  ? "border-primary bg-primary/5 text-primary"
                  : "border-border bg-card text-muted-foreground hover:border-primary/30"
              }`}
            >
              <l.icon className="w-5 h-5" />
              <span className="text-sm font-medium">{l.label}</span>
              <span className="text-[10px] text-muted-foreground">{l.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Person cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">
            People ({persons.length}/6)
          </label>
          <button
            onClick={addPerson}
            disabled={persons.length >= 6}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition disabled:opacity-50"
          >
            <Plus className="w-3 h-3" />
            Add Person
          </button>
        </div>

        {persons.map((person, idx) => (
          <div
            key={person.id}
            className="bg-card border border-border rounded-xl p-5 space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
                  {idx + 1}
                </div>
                <input
                  type="text"
                  value={person.name}
                  onChange={(e) => updatePerson(person.id, { name: e.target.value })}
                  placeholder={`Person ${idx + 1}`}
                  className="bg-transparent border-none text-sm font-medium focus:outline-none placeholder:text-muted-foreground"
                />
              </div>
              {persons.length > 2 && (
                <button
                  onClick={() => removePerson(person.id)}
                  className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/10 transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              {/* Face upload */}
              <label className="relative flex flex-col items-center gap-2 p-4 border-2 border-dashed border-border rounded-xl cursor-pointer hover:border-primary/30 transition">
                <Upload className="w-5 h-5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  {person.faceFile ? person.faceFile.name : "Face Photo"}
                </span>
                {person.facePath && <CheckCircle className="w-4 h-4 text-green-400 absolute top-2 right-2" />}
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleFileUpload(person.id, "face", f);
                  }}
                />
              </label>

              {/* Voice upload */}
              <label className="relative flex flex-col items-center gap-2 p-4 border-2 border-dashed border-border rounded-xl cursor-pointer hover:border-primary/30 transition">
                <Upload className="w-5 h-5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  {person.voiceFile ? person.voiceFile.name : "Voice Sample"}
                </span>
                {person.voicePath && <CheckCircle className="w-4 h-4 text-green-400 absolute top-2 right-2" />}
                <input
                  type="file"
                  accept="audio/*"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleFileUpload(person.id, "voice", f);
                  }}
                />
              </label>
            </div>

            <textarea
              value={person.script}
              onChange={(e) => updatePerson(person.id, { script: e.target.value })}
              placeholder="Enter this person's script..."
              rows={3}
              className="w-full p-3 bg-secondary/50 border border-border rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/50"
            />

            <div className="flex gap-3">
              <select
                value={person.language}
                onChange={(e) => updatePerson(person.id, { language: e.target.value })}
                className="flex-1 p-2 bg-card border border-border rounded-lg text-sm"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="hi">Hindi</option>
                <option value="ja">Japanese</option>
                <option value="ko">Korean</option>
                <option value="zh">Chinese</option>
              </select>
              <select
                value={person.emotion}
                onChange={(e) => updatePerson(person.id, { emotion: e.target.value })}
                className="flex-1 p-2 bg-card border border-border rounded-lg text-sm"
              >
                <option value="neutral">Neutral</option>
                <option value="happy">Happy</option>
                <option value="sad">Sad</option>
                <option value="angry">Angry</option>
                <option value="surprised">Surprised</option>
              </select>
            </div>
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Generate button */}
      {!isProcessing && !isCompleted && (
        <button
          onClick={handleGenerate}
          disabled={uploading}
          className="w-full flex items-center justify-center gap-2 py-4 bg-primary text-primary-foreground font-bold rounded-xl hover:bg-primary/90 transition text-lg disabled:opacity-50"
        >
          {uploading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Play className="w-5 h-5" />
          )}
          Generate Group Video
        </button>
      )}

      {/* Processing */}
      {isProcessing && (
        <div className="text-center space-y-4 py-8">
          <Loader2 className="w-10 h-10 animate-spin text-primary mx-auto" />
          <p className="text-sm font-medium">Processing {persons.length}-person video…</p>
          <div className="h-2 bg-border rounded-full max-w-xs mx-auto overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all"
              style={{ width: `${jobProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Completed */}
      {isCompleted && (
        <div className="text-center space-y-4 py-8">
          <CheckCircle className="w-10 h-10 text-green-400 mx-auto" />
          <p className="text-sm font-medium text-green-400">Group video ready!</p>
        </div>
      )}
    </div>
  );
}
