/**
 * Ominou Studio — Unified API Client
 * All service calls go through the gateway at /api/v1/{service}/{path}
 */

const API_BASE = "/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("ominou_token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Network error" }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

// ─── Auth ─────────────────────────────────
export const auth = {
  register: (email: string, password: string, full_name: string) =>
    request("/auth/auth/register", { method: "POST", body: JSON.stringify({ email, password, full_name }) }),

  login: (email: string, password: string) =>
    request("/auth/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  me: () => request("/auth/auth/me"),

  updateProfile: (data: Record<string, string>) =>
    request("/auth/users/profile", { method: "PUT", body: JSON.stringify(data) }),

  getCredits: () => request("/auth/users/credits"),

  createApiKey: (name: string) =>
    request("/auth/users/api-keys", { method: "POST", body: JSON.stringify({ name }) }),

  listApiKeys: () => request("/auth/users/api-keys"),

  deleteApiKey: (id: number) =>
    request(`/auth/users/api-keys/${id}`, { method: "DELETE" }),
};

// ─── Voice Studio ─────────────────────────
export const voice = {
  tts: (text: string, voice_id: string = "aria", speed: number = 1.0, pitch: number = 1.0) =>
    request("/voice/tts", { method: "POST", body: JSON.stringify({ text, voice_id, speed, pitch }) }),

  clone: (voice_name: string, audio_urls: string[]) =>
    request("/voice/clone", { method: "POST", body: JSON.stringify({ voice_name, audio_urls }) }),

  dub: (text: string, target_language: string, voice_id: string = "aria") =>
    request("/voice/dub", { method: "POST", body: JSON.stringify({ text, target_language, voice_id }) }),

  getVoices: () => request("/voice/voices"),
  getStyles: () => request("/voice/styles"),
  getLanguages: () => request("/voice/languages"),
};

// ─── Design Studio ────────────────────────
export const design = {
  generate: (prompt: string, style: string = "photorealistic", width: number = 1024, height: number = 1024) =>
    request("/design/generate", { method: "POST", body: JSON.stringify({ prompt, style, width, height }) }),

  removeBackground: (image_url: string) =>
    request("/design/remove-background", { method: "POST", body: JSON.stringify({ image_url }) }),

  upscale: (image_url: string, scale: number = 2) =>
    request("/design/upscale", { method: "POST", body: JSON.stringify({ image_url, scale }) }),

  fromTemplate: (template_id: string, category: string, customizations: Record<string, unknown> = {}) =>
    request("/design/from-template", { method: "POST", body: JSON.stringify({ template_id, category, customizations }) }),

  getTemplates: () => request("/design/templates"),
  getStyles: () => request("/design/styles"),
  getFilters: () => request("/design/filters"),
};

// ─── Code Studio ──────────────────────────
export const code = {
  generate: (prompt: string, language: string = "python", context: string = "") =>
    request("/code/generate", { method: "POST", body: JSON.stringify({ prompt, language, context }) }),

  explain: (codeStr: string, language: string = "python") =>
    request("/code/explain", { method: "POST", body: JSON.stringify({ code: codeStr, language }) }),

  refactor: (codeStr: string, language: string = "python", instructions: string = "") =>
    request("/code/refactor", { method: "POST", body: JSON.stringify({ code: codeStr, language, instructions }) }),

  createProject: (template: string, name: string) =>
    request("/code/project", { method: "POST", body: JSON.stringify({ template, name }) }),

  deploy: (project_id: string) =>
    request("/code/deploy", { method: "POST", body: JSON.stringify({ project_id }) }),

  getLanguages: () => request("/code/languages"),
  getTemplates: () => request("/code/templates"),
};

// ─── AI Writer ────────────────────────────
export const writer = {
  generate: (content_type: string, topic: string, tone: string = "professional", keywords: string[] = []) =>
    request("/writer/generate", { method: "POST", body: JSON.stringify({ content_type, topic, tone, keywords }) }),

  rewrite: (content: string, tone: string = "professional", instructions: string = "") =>
    request("/writer/rewrite", { method: "POST", body: JSON.stringify({ content, tone, instructions }) }),

  seo: (topic: string, keywords: string[] = []) =>
    request("/writer/seo", { method: "POST", body: JSON.stringify({ topic, keywords }) }),

  getContentTypes: () => request("/writer/content-types"),
  getTones: () => request("/writer/tones"),
};

// ─── Music Studio ─────────────────────────
export const music = {
  generate: (prompt: string, genre: string = "ambient", mood: string = "calm", duration_seconds: number = 30) =>
    request("/music/generate", { method: "POST", body: JSON.stringify({ prompt, genre, mood, duration_seconds }) }),

  jingle: (brand_name: string, style: string = "corporate", duration_seconds: number = 15) =>
    request("/music/jingle", { method: "POST", body: JSON.stringify({ brand_name, style, duration_seconds }) }),

  sfx: (category: string, effect: string) =>
    request("/music/sfx", { method: "POST", body: JSON.stringify({ category, effect }) }),

  remix: (audio_url: string, genre: string = "lo_fi") =>
    request("/music/remix", { method: "POST", body: JSON.stringify({ audio_url, genre }) }),

  getGenres: () => request("/music/genres"),
  getMoods: () => request("/music/moods"),
  getSfxCategories: () => request("/music/sfx-categories"),
};

// ─── Workflow ─────────────────────────────
export const workflow = {
  create: (name: string, steps: Array<{ id: string; type: string; config: Record<string, unknown>; depends_on?: string }>) =>
    request("/workflow/create", { method: "POST", body: JSON.stringify({ name, steps }) }),

  fromTemplate: (template: string, name?: string) =>
    request("/workflow/from-template", { method: "POST", body: JSON.stringify({ template, name }) }),

  run: (workflow_id: string) =>
    request(`/workflow/run/${workflow_id}`, { method: "POST" }),

  list: () => request("/workflow/list"),
  get: (id: string) => request(`/workflow/${id}`),
  delete: (id: string) => request(`/workflow/${id}`, { method: "DELETE" }),
  getTemplates: () => request("/workflow/templates"),
  getSteps: () => request("/workflow/steps"),
};

// ─── Billing ──────────────────────────────
export const billing = {
  getPlans: () => request("/billing/plans"),
  getCurrent: () => request("/billing/current"),
  subscribe: (plan: string, billing_cycle: string = "monthly") =>
    request("/billing/subscribe", { method: "POST", body: JSON.stringify({ plan, billing_cycle }) }),
  buyCredits: (amount: number) =>
    request("/billing/buy-credits", { method: "POST", body: JSON.stringify({ amount }) }),
  getUsage: () => request("/billing/usage"),
  getInvoices: () => request("/billing/invoices"),
  cancel: () => request("/billing/cancel", { method: "POST" }),
};

const api = { auth, voice, design, code, writer, music, workflow, billing };
export default api;
