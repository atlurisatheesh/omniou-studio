/**
 * CLONEAI PRO — API Client (Phase 12)
 * TypeScript client for the FastAPI backend with auth, analytics,
 * templates, multi-face, and streaming APIs.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Token management ──

let _accessToken: string | null = null;
let _refreshToken: string | null = null;

export function setTokens(access: string, refresh: string) {
  _accessToken = access;
  _refreshToken = refresh;
  if (typeof window !== "undefined") {
    localStorage.setItem("cloneai_access", access);
    localStorage.setItem("cloneai_refresh", refresh);
  }
}

export function loadTokens() {
  if (typeof window !== "undefined") {
    _accessToken = localStorage.getItem("cloneai_access");
    _refreshToken = localStorage.getItem("cloneai_refresh");
  }
}

export function clearTokens() {
  _accessToken = null;
  _refreshToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("cloneai_access");
    localStorage.removeItem("cloneai_refresh");
  }
}

export function getAccessToken(): string | null {
  return _accessToken;
}

// Auto-load on module init
loadTokens();

// ── Auth-aware fetch ──

async function authFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (_accessToken) {
    headers.set("Authorization", `Bearer ${_accessToken}`);
  }
  let res = await fetch(url, { ...init, headers });

  // Auto-refresh on 401
  if (res.status === 401 && _refreshToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${_accessToken}`);
      res = await fetch(url, { ...init, headers });
    }
  }
  return res;
}

async function refreshAccessToken(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: _refreshToken }),
    });
    if (!res.ok) {
      clearTokens();
      return false;
    }
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

// ── Interfaces ──

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
  download_url?: string;
}

export interface Language {
  code: string;
  name: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  script_text: string;
  language: string;
  emotion: string;
  background: string;
  tags: string[];
  is_builtin: boolean;
}

export interface AnalyticsSummary {
  total_jobs: number;
  completed: number;
  failed: number;
  avg_processing_time: number;
  total_duration_generated: number;
  active_today: number;
}

export interface MultiPersonSpec {
  face_path: string;
  voice_path: string;
  script: string;
  name?: string;
  language?: string;
  emotion?: string;
}

// ── Upload ──

export async function uploadPhoto(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await authFetch(`${API_BASE}/api/v1/upload/photo`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadVoice(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await authFetch(`${API_BASE}/api/v1/upload/voice`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Auth ──

export const auth = {
  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return data;
  },

  async logout() {
    if (_accessToken) {
      try {
        await authFetch(`${API_BASE}/api/v1/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: _refreshToken }),
        });
      } catch {
        // best-effort
      }
    }
    clearTokens();
  },

  async me() {
    const res = await authFetch(`${API_BASE}/api/v1/auth/me`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};

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
  const res = await authFetch(`${API_BASE}/api/v1/clone/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getCloneStatus(jobId: string): Promise<CloneStatusResponse> {
  const res = await authFetch(`${API_BASE}/api/v1/clone/${jobId}/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function cancelClone(jobId: string): Promise<void> {
  const res = await authFetch(`${API_BASE}/api/v1/clone/${jobId}`, { method: "DELETE" });
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
  const res = await authFetch(`${API_BASE}/api/v1/script/generate`, {
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
  const res = await authFetch(`${API_BASE}/api/v1/voice/profiles`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createVoiceProfile(data: FormData): Promise<VoiceProfile> {
  const res = await authFetch(`${API_BASE}/api/v1/voice/profiles`, {
    method: "POST",
    body: data,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteVoiceProfile(id: string): Promise<void> {
  const res = await authFetch(`${API_BASE}/api/v1/voice/profiles/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await res.text());
}

// ── Video Export ──

export async function exportVideo(
  jobId: string,
  format: string,
): Promise<{ download_url: string }> {
  const res = await authFetch(`${API_BASE}/api/v1/video/${jobId}/export`, {
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
  const res = await authFetch(`${API_BASE}/api/v1/admin/stats`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Analytics (Phase 12) ──

export const analytics = {
  async summary(): Promise<AnalyticsSummary> {
    const res = await authFetch(`${API_BASE}/api/v1/analytics/summary`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async dailyJobs(days = 30) {
    const res = await authFetch(`${API_BASE}/api/v1/analytics/daily-jobs?days=${days}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async languages() {
    const res = await authFetch(`${API_BASE}/api/v1/analytics/languages`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async engines() {
    const res = await authFetch(`${API_BASE}/api/v1/analytics/engines`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async processingTime(days = 30) {
    const res = await authFetch(`${API_BASE}/api/v1/analytics/processing-time?days=${days}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async qualityScores() {
    const res = await authFetch(`${API_BASE}/api/v1/analytics/quality-scores`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};

// ── Templates (Phase 12) ──

export const templates = {
  async list(category?: string): Promise<Template[]> {
    const params = category ? `?category=${encodeURIComponent(category)}` : "";
    const res = await fetch(`${API_BASE}/api/v1/templates${params}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async get(id: string): Promise<Template> {
    const res = await fetch(`${API_BASE}/api/v1/templates/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async create(data: Omit<Template, "id" | "is_builtin">): Promise<Template> {
    const res = await authFetch(`${API_BASE}/api/v1/templates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async delete(id: string): Promise<void> {
    const res = await authFetch(`${API_BASE}/api/v1/templates/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(await res.text());
  },
};

// ── Multi-Face (Phase 12) ──

export const multiFace = {
  async create(persons: MultiPersonSpec[], layout: string = "sequential") {
    const res = await authFetch(`${API_BASE}/api/v1/multi-face/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ persons, layout }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async status(id: string) {
    const res = await authFetch(`${API_BASE}/api/v1/multi-face/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};

// ── Project (Long-Form) ──

export interface ProjectScene {
  id: string;
  scene_index: number;
  script_text: string;
  duration_seconds: number;
  emotion: string;
  background: string;
  transition_type: string;
  status: string;
  identity_score: number | null;
  color_consistency_score: number | null;
  cross_scene_score: number | null;
  drift_frame_count: number;
}

export interface Project {
  id: string;
  name: string;
  status: string;
  total_scenes: number;
  completed_scenes: number;
  target_duration_minutes: number;
  overall_identity_score: number | null;
  overall_color_score: number | null;
  output_path: string | null;
  processing_time_seconds: number | null;
  scenes: ProjectScene[];
  created_at: string;
  updated_at: string | null;
}

export interface ProjectProgress {
  project_id: string;
  status: string;
  total_scenes: number;
  completed_scenes: number;
  current_scene_index: number | null;
  current_stage: string | null;
  overall_identity_score: number | null;
  progress_percent: number;
}

export const project = {
  async create(data: {
    name: string;
    script_text: string;
    target_duration_minutes: number;
    avatar_config: {
      photo_path: string;
      voice_path?: string;
      voice_id?: string;
    };
    consistency_settings?: {
      identity_threshold?: number;
      color_threshold?: number;
      auto_correct?: boolean;
      strict_mode?: boolean;
      max_retries?: number;
    };
    settings?: {
      scene_split_method?: string;
      transition_type?: string;
      default_emotion?: string;
      background?: string;
      enable_b_roll?: boolean;
    };
  }): Promise<Project> {
    const res = await authFetch(`${API_BASE}/api/v1/project/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async get(id: string): Promise<Project> {
    const res = await authFetch(`${API_BASE}/api/v1/project/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async list(status?: string): Promise<Project[]> {
    const params = status ? `?status=${status}` : "";
    const res = await authFetch(`${API_BASE}/api/v1/project/${params}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async generate(id: string): Promise<{ status: string; message: string }> {
    const res = await authFetch(`${API_BASE}/api/v1/project/${id}/generate`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async progress(id: string): Promise<ProjectProgress> {
    const res = await authFetch(`${API_BASE}/api/v1/project/${id}/progress`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async consistency(id: string): Promise<any> {
    const res = await authFetch(`${API_BASE}/api/v1/project/${id}/consistency`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async regenerateScene(projectId: string, sceneIndex: number): Promise<any> {
    const res = await authFetch(
      `${API_BASE}/api/v1/project/${projectId}/regenerate/${sceneIndex}`,
      { method: "POST" },
    );
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async delete(id: string): Promise<void> {
    const res = await authFetch(`${API_BASE}/api/v1/project/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(await res.text());
  },
};

// ── Persona (Self-Cloning Agent) ──

export interface PersonaData {
  id: string;
  name: string;
  videos_generated: number;
  avg_identity_score: number | null;
  is_active: boolean;
  created_at: string;
}

export const persona = {
  async create(data: {
    name: string;
    photo_path: string;
    voice_path?: string;
  }): Promise<PersonaData> {
    const res = await authFetch(`${API_BASE}/api/v1/persona/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async list(): Promise<PersonaData[]> {
    const res = await authFetch(`${API_BASE}/api/v1/persona/`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async get(id: string): Promise<PersonaData> {
    const res = await authFetch(`${API_BASE}/api/v1/persona/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async generate(
    personaId: string,
    data: {
      script_text?: string;
      prompt?: string;
      target_duration_minutes?: number;
      emotion?: string;
      background?: string;
    },
  ): Promise<{ status: string; project_id: string }> {
    const res = await authFetch(
      `${API_BASE}/api/v1/persona/${personaId}/generate`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async delete(id: string): Promise<void> {
    const res = await authFetch(`${API_BASE}/api/v1/persona/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(await res.text());
  },
};

// ── Project WebSocket ──

export function connectProjectWebSocket(
  projectId: string,
  onMessage: (data: any) => void,
  onError?: (error: Event) => void,
  onClose?: () => void,
): WebSocket {
  const wsBase = API_BASE.replace("http", "ws");
  const ws = new WebSocket(`${wsBase}/api/v1/project/${projectId}/ws`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.error("Failed to parse project WebSocket message");
    }
  };

  ws.onerror = (event) => {
    console.error("Project WebSocket error:", event);
    onError?.(event);
  };

  ws.onclose = () => {
    onClose?.();
  };

  return ws;
}

