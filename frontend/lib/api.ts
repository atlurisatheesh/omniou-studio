const API_BASE = "/api";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("agri_token") : null;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ── Auth ──
export const api = {
  auth: {
    register: (data: {
      phone: string;
      password: string;
      name: string;
      region?: string;
    }) => request("/auth/register", { method: "POST", body: JSON.stringify(data) }),

    login: (phone: string, password: string) =>
      request<{ access_token: string; user: Record<string, unknown> }>(
        "/auth/login",
        { method: "POST", body: JSON.stringify({ phone, password }) }
      ),

    me: () => request<Record<string, unknown>>("/auth/me"),
  },

  // ── Disease Detection ──
  disease: {
    scan: (file: File, crop: string) => {
      const form = new FormData();
      form.append("image", file);
      form.append("crop", crop);
      return request<{
        disease: string;
        confidence: number;
        severity: string;
        treatment: { chemical: string[]; organic: string[]; prevention: string[] };
        scan_id: string;
      }>("/disease/scan", { method: "POST", body: form });
    },

    history: () =>
      request<{ scans: Array<Record<string, unknown>> }>("/disease/history"),

    crops: () => request<{ crops: string[] }>("/disease/crops"),
  },

  // ── Soil Analysis ──
  soil: {
    analyze: (data: Record<string, number>) =>
      request<{
        overall_score: number;
        health_status: string;
        parameters: Array<Record<string, unknown>>;
        recommendations: Array<Record<string, unknown>>;
      }>("/soil/analyze", { method: "POST", body: JSON.stringify(data) }),

    ranges: () => request<{ ranges: Record<string, unknown> }>("/soil/ranges"),

    cropNeeds: () =>
      request<{ crops: Record<string, unknown> }>("/soil/crop-needs"),
  },

  // ── Weather ──
  weather: {
    forecast: (lat?: number, lon?: number) => {
      const params = new URLSearchParams();
      if (lat) params.set("lat", String(lat));
      if (lon) params.set("lon", String(lon));
      return request<{
        current: Record<string, unknown>;
        forecast: Array<Record<string, unknown>>;
        pest_risks: Array<Record<string, unknown>>;
      }>(`/weather/forecast?${params}`);
    },

    sprayWindow: (lat?: number, lon?: number) => {
      const params = new URLSearchParams();
      if (lat) params.set("lat", String(lat));
      if (lon) params.set("lon", String(lon));
      return request<{
        windows: Array<Record<string, unknown>>;
      }>(`/weather/spray-window?${params}`);
    },
  },

  // ── Crop Calendar ──
  calendar: {
    create: (crop: string, sowingDate: string) =>
      request("/calendar/create", {
        method: "POST",
        body: JSON.stringify({ crop, sowing_date: sowingDate }),
      }),

    crops: () =>
      request<{ crops: Array<{ name: string; duration_days: number }> }>(
        "/calendar/crops"
      ),

    activities: (crop: string) =>
      request<{
        crop: string;
        stages: Array<{
          stage: string;
          activities: Array<{
            activity: string;
            day: number;
            details: string;
            upcoming: boolean;
          }>;
        }>;
      }>(`/calendar/activities/${encodeURIComponent(crop)}`),
  },

  // ── Market ──
  market: {
    prices: (commodity: string) =>
      request<{
        commodity: string;
        msp: number;
        prices: Array<{ market: string; price: number; trend: string }>;
        best_market: { market: string; price: number };
      }>(`/market/prices/${encodeURIComponent(commodity)}`),

    commodities: () =>
      request<{ commodities: string[] }>("/market/commodities"),

    advisory: (commodity: string) =>
      request<{ commodity: string; advisory: string; details: Record<string, unknown> }>(
        `/market/advisory/${encodeURIComponent(commodity)}`
      ),
  },

  // ── Community ──
  community: {
    posts: (category?: string, crop?: string) => {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      if (crop) params.set("crop", crop);
      return request<{ posts: Array<Record<string, unknown>> }>(
        `/community/posts?${params}`
      );
    },

    getPost: (id: string) =>
      request<{
        post: Record<string, unknown>;
        replies: Array<Record<string, unknown>>;
      }>(`/community/posts/${id}`),

    createPost: (data: FormData) =>
      request("/community/posts", { method: "POST", body: data }),

    reply: (postId: string, body: string) => {
      const form = new FormData();
      form.append("body", body);
      return request(`/community/posts/${postId}/reply`, {
        method: "POST",
        body: form,
      });
    },

    upvote: (postId: string) =>
      request(`/community/posts/${postId}/upvote`, { method: "POST" }),
  },
};
