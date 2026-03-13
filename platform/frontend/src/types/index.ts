/* ─── User & Auth ─── */
export interface User {
  id: number;
  email: string;
  full_name: string;
  avatar_url?: string;
  plan: "free" | "pro" | "team" | "enterprise";
  credits_remaining: number;
  is_verified: boolean;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/* ─── Voice Studio ─── */
export interface VoicePreset {
  id: string;
  name: string;
  gender: string;
  accent: string;
  style: string;
}

export interface TTSResult {
  file_id: string;
  file_url: string;
  voice: VoicePreset;
  duration_seconds: number;
  word_count: number;
  status: string;
}

/* ─── Design Studio ─── */
export interface ImageResult {
  file_id: string;
  file_url: string;
  prompt: string;
  style: string;
  width: number;
  height: number;
  status: string;
}

export interface TemplateCategory {
  [key: string]: {
    [key: string]: { width: number; height: number; name: string };
  };
}

/* ─── Code Studio ─── */
export interface CodeResult {
  file_id: string;
  language: string;
  code: string;
  explanation: string;
  tokens_used: number;
  status: string;
}

export interface ProjectTemplate {
  name: string;
  stack: string[];
}

/* ─── AI Writer ─── */
export interface ContentResult {
  file_id: string;
  content_type: string;
  content: string;
  topic: string;
  tone: string;
  word_count: number;
  seo_score: number;
  readability_score: number;
  status: string;
}

/* ─── Music Studio ─── */
export interface MusicResult {
  file_id: string;
  file_url: string;
  genre: string;
  mood: string;
  duration_seconds: number;
  bpm: number;
  status: string;
}

/* ─── Workflow ─── */
export interface WorkflowStep {
  id: string;
  type: string;
  config: Record<string, unknown>;
  depends_on?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  total_credits: number;
  status: string;
  created_at: string;
}

/* ─── Billing ─── */
export interface Plan {
  name: string;
  price_monthly: number;
  price_yearly: number;
  credits_monthly: number;
  features: string[];
  limits: { max_projects: number; max_storage_mb: number; max_team_members: number };
}

export interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: string;
  description: string;
}

/* ─── Common ─── */
export interface APIResponse<T = unknown> {
  success: boolean;
  credits_used?: number;
  data?: T;
  message?: string;
}

export type ModuleName = "voice" | "design" | "code" | "video" | "writer" | "music" | "workflow";
