/**
 * CLONEAI PRO — API Client
 * TypeScript client for the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UploadResponse {
  status: string;
  type: string;
  file_id: string;
  filename: string;
  path: string;
  size_bytes: number;
  content_type: string;
}

export interface CloneCreateResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface CloneStatusResponse {
  job_id: string;
  status: string;
  progress: number;
  step: string;
  result_url?: string;
  error?: string;
}

export interface Language {
  code: string;
  name: string;
}

// ── Upload ──

export async function uploadPhoto(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/v1/upload/photo`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadVoice(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/v1/upload/voice`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Clone ──

export async function createClone(data: {
  photo_path: string;
  voice_path: string;
  script_text: string;
  target_language: string;
  emotion?: string;
  background?: string;
  voice_id?: string;
}): Promise<CloneCreateResponse> {
  const res = await fetch(`${API_BASE}/api/v1/clone/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCloneStatus(jobId: string): Promise<CloneStatusResponse> {
  const res = await fetch(`${API_BASE}/api/v1/clone/${jobId}/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function cancelClone(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/clone/${jobId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

// ── Voice ──

export async function getLanguages(): Promise<Language[]> {
  const res = await fetch(`${API_BASE}/api/v1/voice/languages`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.languages;
}

// ── Video ──

export function getVideoDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/v1/video/${jobId}/download`;
}

export function getVideoPreviewUrl(jobId: string): string {
  return `${API_BASE}/api/v1/video/${jobId}/preview`;
}

// ── WebSocket ──

export function connectProgressWebSocket(
  jobId: string,
  onMessage: (data: CloneStatusResponse) => void,
  onError?: (error: Event) => void,
  onClose?: () => void,
): WebSocket {
  const wsBase = API_BASE.replace("http", "ws");
  const ws = new WebSocket(`${wsBase}/api/v1/clone/${jobId}/ws`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.error("Failed to parse WebSocket message");
    }
  };

  ws.onerror = (event) => {
    console.error("WebSocket error:", event);
    onError?.(event);
  };

  ws.onclose = () => {
    onClose?.();
  };

  return ws;
}

// ── Health ──

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/v1/health`);
  return res.json();
}

// ── Script AI ──

export async function generateScript(data: {
  topic: string;
  tone?: string;
  duration_seconds?: number;
  language?: string;
}): Promise<{ script: string; word_count: number; estimated_duration: number }> {
  const res = await fetch(`${API_BASE}/api/v1/script/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Voice Profiles ──

export interface VoiceProfile {
  id: string;
  name: string;
  language: string;
  quality_score: number;
  duration_sec: number;
  created_at: string;
}

export async function getVoiceProfiles(): Promise<VoiceProfile[]> {
  const res = await fetch(`${API_BASE}/api/v1/voice/profiles`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createVoiceProfile(data: FormData): Promise<VoiceProfile> {
  const res = await fetch(`${API_BASE}/api/v1/voice/profiles`, {
    method: "POST",
    body: data,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteVoiceProfile(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/voice/profiles/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await res.text());
}

// ── Video Export ──

export async function exportVideo(
  jobId: string,
  format: string,
): Promise<{ download_url: string }> {
  const res = await fetch(`${API_BASE}/api/v1/video/${jobId}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Admin ──

export async function getAdminStats(): Promise<{
  total_users: number;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  active_jobs: number;
}> {
  const res = await fetch(`${API_BASE}/api/v1/admin/stats`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
