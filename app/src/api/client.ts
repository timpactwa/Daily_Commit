// Typed client for contracts/api.md. Owned by Tim.
//
// Config (Vite env):
//   VITE_API_BASE  base URL of the API ("" = same origin; dev server proxies /v1 and /health)
//   VITE_MOCK=1    use the in-memory mock (src/api/mock.ts) instead of the network
import type {
  AnswerRequest, AnswerResult, AuthResult, CompleteResult, ErrorCode, Features, Leaderboard,
  LearnCheckResult, LearnModule, LearnSummary, Lesson, PlacementAnswer, PlacementResult, Preview,
  Progress, PublicQuestion, RankedResult, RankedSession, RankedTier, ResponseValue, TierId, Topic, User,
} from "./types";
import { mockTransport } from "./mock";

export class ApiError extends Error {
  constructor(public status: number, public code: ErrorCode, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export interface Transport {
  (method: "GET" | "POST", path: string, body: unknown, headers: Record<string, string>): Promise<{
    status: number;
    json: unknown;
  }>;
}

const env = import.meta.env ?? {};
const BASE: string = env.VITE_API_BASE ?? "";
const USE_MOCK = env.VITE_MOCK === "1" || env.VITE_MOCK === "true";
const USER_KEY = "dc.user_id";
const TOKEN_KEY = "dc.token";

const fetchTransport: Transport = async (method, path, body, headers) => {
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      method,
      headers: { ...headers, ...(body !== undefined ? { "Content-Type": "application/json" } : {}) },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network", "Can't reach the server. Check your connection and try again.");
  }
  const json = await res.json().catch(() => null);
  return { status: res.status, json };
};

let transport: Transport = USE_MOCK ? mockTransport : fetchTransport;

/** Tests or storybook can swap the transport. */
export function setTransport(t: Transport) {
  transport = t;
}

// ---- identity + date -------------------------------------------------------

let memoryUserId: string | null = null;

export function getUserId(): string | null {
  try {
    return localStorage.getItem(USER_KEY) ?? memoryUserId;
  } catch {
    return memoryUserId;
  }
}

export function setUserId(id: string | null) {
  memoryUserId = id;
  try {
    if (id) localStorage.setItem(USER_KEY, id);
    else localStorage.removeItem(USER_KEY);
  } catch {
    /* private mode: memory only */
  }
}

let memoryToken: string | null = null;

/** Session token for accounts. Guests have none and are identified by X-User-Id only. */
export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY) ?? memoryToken;
  } catch {
    return memoryToken;
  }
}

export function setToken(token: string | null) {
  memoryToken = token;
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* private mode: memory only */
  }
}

/** The phone's local date as YYYY-MM-DD. */
export function localDate(d = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

async function call<T>(method: "GET" | "POST", path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "X-Client-Date": localDate() };
  const uid = getUserId();
  if (uid) headers["X-User-Id"] = uid;
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const { status, json } = await transport(method, path, body, headers);
  if (status >= 200 && status < 300) return json as T;
  const err = (json as { error?: { code?: ErrorCode; message?: string } } | null)?.error;
  throw new ApiError(status, err?.code ?? "server", err?.message ?? `Request failed (${status})`);
}

// ---- endpoints (one per contracts/api.md entry) -----------------------------

export const api = {
  health: () => call<{ ok: boolean; questions: number }>("GET", "/health"),
  getTopics: () => call<{ version: number; topics: Topic[] }>("GET", "/v1/topics"),

  /** Creates a user and stores its id for every later call. */
  async createUser(display_name: string): Promise<User> {
    const user = await call<User>("POST", "/v1/users", { display_name });
    setUserId(user.user_id);
    return user;
  },
  getMe: () => call<User>("GET", "/v1/me"),

  getPlacement: (limit?: number) =>
    call<{ questions: PublicQuestion[] }>("GET", `/v1/placement${limit ? `?limit=${limit}` : ""}`),
  submitPlacement: (responses: PlacementAnswer[]) =>
    call<PlacementResult>("POST", "/v1/placement", { responses }),

  getLessonToday: () => call<Lesson>("GET", "/v1/lessons/today"),
  submitAnswer: (req: AnswerRequest) => call<AnswerResult>("POST", "/v1/answers", req),
  completeLesson: (lesson_id: string) =>
    call<CompleteResult>("POST", `/v1/lessons/${encodeURIComponent(lesson_id)}/complete`),
  getNextPreview: () => call<Preview>("GET", "/v1/lessons/next/preview"),

  getProgress: () => call<Progress>("GET", "/v1/progress"),

  // Demo mode only (server returns 404 otherwise).
  demoReset: () => call<{ ok: boolean }>("POST", "/v1/demo/reset", { user_id: "demo" }),
  demoAdvanceDay: () => call<{ date: string }>("POST", "/v1/demo/advance-day"),
  /** Switches the app to the seeded demo user ("Tim on day 7"). */
  async demoSwitch(): Promise<User> {
    setToken(null);
    const user = await call<User>("POST", "/v1/demo/switch", { user_id: "demo" });
    setUserId(user.user_id);
    return user;
  },
  /** Feature flags. Missing endpoint (old server) means every new feature is off. */
  async getConfig(): Promise<Features> {
    try {
      return (await call<{ features: Features }>("GET", "/v1/config")).features;
    } catch {
      return { learn: false, ranked: false, accounts: false };
    }
  },

  // Accounts. Signup claims the current guest's progress (same user id).
  async signup(username: string, password: string): Promise<AuthResult> {
    const r = await call<AuthResult>("POST", "/v1/auth/signup", { username, password });
    setToken(r.token);
    setUserId(r.user.user_id);
    return r;
  },
  async login(username: string, password: string): Promise<AuthResult> {
    const r = await call<AuthResult>("POST", "/v1/auth/login", { username, password });
    setToken(r.token);
    setUserId(r.user.user_id);
    return r;
  },
  async logout(): Promise<void> {
    try {
      await call<{ ok: boolean }>("POST", "/v1/auth/logout");
    } finally {
      setToken(null);
      setUserId(null);
    }
  },

  // Learning modules
  getModules: () => call<{ modules: LearnSummary[] }>("GET", "/v1/learn"),
  getModule: (topic: string) => call<LearnModule>("GET", `/v1/learn/${encodeURIComponent(topic)}`),
  checkSection: (topic: string, section_id: string, response: string) =>
    call<LearnCheckResult>("POST", `/v1/learn/${encodeURIComponent(topic)}/check`, { section_id, response }),

  // Ranked tests
  getRanked: () => call<{ has_account: boolean; ranked_level: number; ranked_rating: number; tiers: RankedTier[] }>("GET", "/v1/ranked"),
  startRanked: (tier: TierId) => call<RankedSession>("POST", `/v1/ranked/${tier}/start`),
  resumeRanked: (tier: TierId) => call<RankedSession>("GET", `/v1/ranked/${tier}/attempt`),
  answerRanked: (tier: TierId, question_id: string, response: ResponseValue) =>
    call<{ saved: boolean; answered: number; total: number; remaining_ms: number }>(
      "POST", `/v1/ranked/${tier}/answer`, { question_id, response }),
  submitRanked: (tier: TierId) => call<RankedResult>("POST", `/v1/ranked/${tier}/submit`),
  getRankedResult: (tier: TierId) => call<RankedResult>("GET", `/v1/ranked/${tier}/result`),
  getLeaderboard: (tier: TierId) => call<Leaderboard>("GET", `/v1/ranked/${tier}/leaderboard`),

  signOut: () => {
    setToken(null);
    setUserId(null);
  },
};

export type Api = typeof api;
