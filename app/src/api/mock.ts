// In-memory mock of contracts/api.md, enabled with VITE_MOCK=1. Owned by Tim.
// Fixtures mirror contracts/examples/questions.json (copied because Vite won't
// serve files outside /app). Grading and Elo follow contracts/rating.md, simplified.
import type { Transport } from "./client";
import type { PublicQuestion, ResponseValue } from "./types";

type FullQuestion = PublicQuestion & { answer: ResponseValue; explanation: string; provenance?: object };

const QUESTIONS: FullQuestion[] = [
  {
    id: "sd-caching-001", version: 1, track: "system-design", topic: "caching", format: "mcq",
    scenario: "A product page is read 50,000 times per second and the price changes about once a day. Reads must be fast; a price that is a few seconds stale is acceptable.",
    prompt: "Which caching strategy fits best?",
    options: [
      { id: "a", text: "No cache; add read replicas" },
      { id: "b", text: "Cache-aside with a TTL and invalidate on price update" },
      { id: "c", text: "Write-through cache with no TTL" },
      { id: "d", text: "Client-side cache for 24 hours" },
    ],
    answer: "b",
    explanation: "Read-heavy, rarely written, small staleness allowed: cache-aside with TTL plus explicit invalidation keeps reads fast and bounds staleness. A 24h client cache would show stale prices after an update.",
    difficulty_rating: 1100,
  },
  {
    id: "sd-scaling-004", version: 1, track: "system-design", topic: "scaling", format: "tap_node",
    scenario: "Traffic doubled and p99 latency went from 80ms to 2s. The API tier autoscaled to 12 instances.",
    prompt: "Tap the bottleneck.",
    diagram: {
      nodes: [
        { id: "client", label: "Mobile clients", kind: "client" },
        { id: "lb", label: "Load balancer", kind: "lb" },
        { id: "api", label: "API x12", kind: "service", note: "autoscaled" },
        { id: "session", label: "Session store", kind: "db", note: "1 instance, 5k ops/s max" },
        { id: "db", label: "Postgres", kind: "db", note: "3 read replicas" },
      ],
      edges: [
        { from: "client", to: "lb" },
        { from: "lb", to: "api" },
        { from: "api", to: "session", label: "every request" },
        { from: "api", to: "db" },
      ],
    },
    options: [
      { id: "client", text: "Mobile clients" },
      { id: "lb", text: "Load balancer" },
      { id: "api", text: "API x12" },
      { id: "session", text: "Session store" },
      { id: "db", text: "Postgres" },
    ],
    answer: "session",
    explanation: "Every request hits a single session store capped at 5k ops/s. Scaling the API tier just sends more load to it.",
    difficulty_rating: 1300,
  },
  {
    id: "sd-async-002", version: 1, track: "system-design", topic: "async-messaging", format: "reorder",
    prompt: "Put the steps of processing an uploaded video in order.",
    options: [
      { id: "s1", text: "Client uploads file to object storage via signed URL" },
      { id: "s2", text: "API records upload and enqueues a transcode job" },
      { id: "s3", text: "Worker pulls the job and transcodes" },
      { id: "s4", text: "Worker writes outputs and marks job done" },
      { id: "s5", text: "Client is notified the video is ready" },
    ],
    answer: ["s1", "s2", "s3", "s4", "s5"],
    explanation: "Upload bypasses the API, the API enqueues work, workers process asynchronously, then completion is signaled.",
    difficulty_rating: 1000,
  },
  {
    id: "dbg-binary-search-flip-comparison-01", version: 1, track: "debugging", topic: "binary-search", format: "tap_line",
    prompt: "This function fails the test below. Tap the buggy line.",
    code: "def search(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo < hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1",
    language: "python",
    test_output: "search([1, 3, 5, 7], 7): expected 3, got -1\nsearch([4], 4): expected 0, got -1",
    answer: 3,
    explanation: "The loop uses < instead of <=, so when lo == hi the last candidate is never checked.",
    difficulty_rating: 1250,
    provenance: {
      source_function: "pipeline/corpus/binary_search.py::search",
      mutation_operator: "flip_comparison",
      original_line: "    while lo <= hi:",
      mutated_line: "    while lo < hi:",
      tests_failed: 2,
      tests_total: 6,
    },
  },
];

const TOPICS = [
  ["caching", "system-design", "Caching"],
  ["scaling", "system-design", "Scaling & Load Balancing"],
  ["databases", "system-design", "Databases & Storage"],
  ["async-messaging", "system-design", "Queues & Async"],
  ["reliability", "system-design", "Reliability & Consistency"],
  ["arrays-strings", "debugging", "Arrays & Strings"],
  ["binary-search", "debugging", "Binary Search"],
  ["recursion", "debugging", "Recursion"],
  ["sorting", "debugging", "Sorting"],
  ["hash-maps", "debugging", "Hash Maps"],
] as const;

// ---- state -----------------------------------------------------------------

interface MockUser {
  user_id: string;
  display_name: string;
  placed: boolean;
  ratings: Record<string, number>;
  history: Record<string, number[]>;
  answered: Record<string, { n: number; correct: number }>;
  streak: { current: number; best: number; last: string | null };
  lesson: { lesson_id: string; date: string; status: "in_progress" | "completed"; results: Record<string, boolean> } | null;
}

const users = new Map<string, MockUser>();
let seq = 1;

function newUser(display_name: string, id = `u_mock${seq++}`): MockUser {
  const u: MockUser = {
    user_id: id, display_name, placed: false,
    ratings: Object.fromEntries(TOPICS.map(([t]) => [t, 1200])),
    history: {}, answered: {},
    streak: { current: 0, best: 0, last: null },
    lesson: null,
  };
  users.set(id, u);
  return u;
}

function demoUser(today: string): MockUser {
  const u = newUser("Tim", "demo");
  u.placed = true;
  Object.assign(u.ratings, { caching: 1340, scaling: 1255, databases: 1180, "async-messaging": 1120, reliability: 1210, "arrays-strings": 1230, "binary-search": 1150, recursion: 1090, sorting: 1260, "hash-maps": 1300 });
  u.streak = { current: 6, best: 6, last: addDays(today, -1) };
  return u;
}

// ---- helpers ---------------------------------------------------------------

const level = (r: number) => (r < 1150 ? "beginner" : r < 1300 ? "intermediate" : "advanced");
const readiness = (r: number) => Math.max(0, Math.min(100, Math.round(((r - 900) / 700) * 100)));
const expected = (r: number, q: number) => 1 / (1 + 10 ** ((q - r) / 400));

function toPublic(q: FullQuestion): PublicQuestion {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { answer, explanation, provenance, ...pub } = q;
  if (pub.format === "reorder" && pub.options) pub.options = [...pub.options].reverse();
  return pub;
}

function score(q: FullQuestion, response: ResponseValue): number {
  if (q.format !== "reorder") return response === q.answer ? 1 : 0;
  const ans = q.answer as string[];
  const resp = response as string[];
  let ok = 0, total = 0;
  for (let i = 0; i < resp.length; i++)
    for (let j = i + 1; j < resp.length; j++) {
      total++;
      if (ans.indexOf(resp[i]) < ans.indexOf(resp[j])) ok++;
    }
  return total ? Math.round((ok / total) * 100) / 100 : 0;
}

function addDays(date: string, n: number): string {
  const d = new Date(date + "T12:00:00");
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

const ok = (json: unknown, status = 200) => ({ status, json });
const fail = (status: number, code: string, message: string) => ({ status, json: { error: { code, message } } });

// ---- transport -------------------------------------------------------------

export const mockTransport: Transport = async (method, path, body, headers) => {
  await new Promise((r) => setTimeout(r, 150)); // feel like a network
  const today = headers["X-Client-Date"];
  const route = `${method} ${path.split("?")[0]}`;
  const b = (body ?? {}) as Record<string, unknown>;

  if (route === "GET /health") return ok({ ok: true, questions: QUESTIONS.length });
  if (route === "GET /v1/topics")
    return ok({ version: 1, topics: TOPICS.map(([id, track, name]) => ({ id, track, name, description: "" })) });
  if (route === "POST /v1/users") {
    const u = newUser(String(b.display_name ?? "Student"));
    return ok({ user_id: u.user_id, display_name: u.display_name, placed: false }, 201);
  }
  if (route === "POST /v1/demo/switch" || route === "POST /v1/demo/reset") {
    const u = demoUser(today);
    return ok(route.endsWith("reset") ? { ok: true } : { user_id: u.user_id, display_name: u.display_name, placed: true, streak: { current: 6, best: 6, today_done: false } });
  }

  const u = users.get(headers["X-User-Id"] ?? "");
  if (!u) return fail(401, "unknown_user", "Missing or unknown X-User-Id");
  const streak = () => ({ current: u.streak.current, best: u.streak.best, today_done: u.streak.last === today });

  if (route === "GET /v1/me") return ok({ user_id: u.user_id, display_name: u.display_name, placed: u.placed, streak: streak() });

  if (route === "GET /v1/placement") return ok({ questions: QUESTIONS.map(toPublic) });
  if (route === "POST /v1/placement") {
    const responses = (b.responses ?? []) as { question_id: string; response: ResponseValue }[];
    const results = responses.map(({ question_id, response }) => {
      const q = QUESTIONS.find((x) => x.id === question_id)!;
      const s = score(q, response);
      const delta = 240 * (s - expected(u.ratings[q.topic], q.difficulty_rating));
      for (const [t, track] of TOPICS) {
        if (track !== q.track) continue;
        u.ratings[t] += t === q.topic ? delta : 0.3 * delta;
      }
      return { question_id, correct: s === 1 };
    });
    u.placed = true;
    return ok({
      results,
      topics: TOPICS.map(([t]) => ({ topic: t, rating: Math.round(u.ratings[t]), level: level(u.ratings[t]), readiness: readiness(u.ratings[t]) })),
    });
  }

  if (route === "GET /v1/lessons/today") {
    if (!u.placed) return fail(409, "not_placed", "Take the placement test first");
    if (!u.lesson || u.lesson.date !== today)
      u.lesson = { lesson_id: `l_${today}_${u.user_id}`, date: today, status: "in_progress", results: {} };
    const L = u.lesson;
    return ok({
      lesson_id: L.lesson_id, date: L.date, status: L.status,
      focus_topics: ["binary-search", "caching"],
      items: QUESTIONS.map((q, i) => ({
        position: i + 1, kind: i < 2 ? "focus" : "mix",
        answered: q.id in L.results, correct: L.results[q.id] ?? null, question: toPublic(q),
      })),
    });
  }

  if (route === "POST /v1/answers") {
    const q = QUESTIONS.find((x) => x.id === b.question_id);
    if (!q || !u.lesson || u.lesson.lesson_id !== b.lesson_id) return fail(404, "not_found", "Lesson or question not found");
    if (q.id in u.lesson.results) return fail(409, "already_answered", "Already answered in this lesson");
    const s = score(q, b.response as ResponseValue);
    const before = u.ratings[q.topic];
    const e = expected(before, q.difficulty_rating);
    const after = before + 48 * (s - e);
    const qBefore = q.difficulty_rating;
    q.difficulty_rating = Math.round(qBefore - 32 * (s - e));
    u.ratings[q.topic] = after;
    (u.history[q.topic] ??= []).push(Math.round(after));
    const a = (u.answered[q.topic] ??= { n: 0, correct: 0 });
    a.n++;
    a.correct += s === 1 ? 1 : 0;
    u.lesson.results[q.id] = s === 1;
    return ok({
      correct: s === 1, score: s, correct_answer: q.answer, explanation: q.explanation,
      rating: { topic: q.topic, before: Math.round(before), after: Math.round(after), delta: Math.round(after) - Math.round(before) },
      question_rating: { before: qBefore, after: q.difficulty_rating },
      ...(q.provenance ? { provenance: q.provenance } : {}),
      lesson_progress: { answered: Object.keys(u.lesson.results).length, total: QUESTIONS.length },
    });
  }

  const complete = route.match(/^POST \/v1\/lessons\/(.+)\/complete$/);
  if (complete) {
    if (!u.lesson || u.lesson.lesson_id !== decodeURIComponent(complete[1])) return fail(404, "not_found", "Lesson not found");
    let extended = false;
    if (u.streak.last !== today) {
      u.streak.current = u.streak.last === addDays(today, -1) ? u.streak.current + 1 : 1;
      u.streak.best = Math.max(u.streak.best, u.streak.current);
      u.streak.last = today;
      extended = true;
    }
    u.lesson.status = "completed";
    const vals = Object.values(u.lesson.results);
    return ok({ summary: { correct: vals.filter(Boolean).length, total: vals.length }, rating_changes: [], streak: { ...streak(), extended } });
  }

  if (route === "GET /v1/lessons/next/preview") {
    const missed = Object.entries(u.lesson?.results ?? {}).filter(([, c]) => !c).map(([id]) => QUESTIONS.find((q) => q.id === id)!.topic);
    const weakest = [...TOPICS].sort((x, y) => u.ratings[x[0]] - u.ratings[y[0]]).map(([t]) => t);
    const focus = [...new Set([...missed, ...weakest])].slice(0, 2);
    return ok({
      date: addDays(today, 1),
      focus_topics: focus.map((t) => ({ topic: t, reason: missed.includes(t) ? "missed_last_lesson" : "lowest_rating", rating: Math.round(u.ratings[t]) })),
      items: focus.map((t) => ({ topic: t, track: TOPICS.find(([x]) => x === t)![1], format: "mcq", difficulty_rating: Math.round(u.ratings[t] - 150), kind: "focus" })),
    });
  }

  if (route === "GET /v1/progress") {
    const topics = TOPICS.map(([t, track]) => {
      const r = u.ratings[t];
      const a = u.answered[t] ?? { n: 0, correct: 0 };
      return { topic: t, track, rating: Math.round(r), level: level(r), readiness: readiness(r), answered: a.n, accuracy: a.n ? a.correct / a.n : 0, history: u.history[t] ?? [Math.round(r)] };
    });
    return ok({ streak: streak(), overall_readiness: Math.round(topics.reduce((s, t) => s + t.readiness, 0) / topics.length), topics });
  }

  if (route === "POST /v1/demo/advance-day") return ok({ date: addDays(today, 1) });

  return fail(404, "not_found", `No mock for ${route}`);
};
