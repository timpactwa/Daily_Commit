# API Contract (v1)

FastAPI on port 8000. The app dev server (Vite, 5173) proxies `/v1` and `/health` to it. In production the API also serves the built app at `/`.

## Conventions

- JSON in and out. `Content-Type: application/json`.
- Identity: header `X-User-Id: <user_id>` on every `/v1` call except `POST /v1/users` and `GET /v1/topics`. No passwords. The app keeps `user_id` in localStorage.
- "Today": header `X-Client-Date: YYYY-MM-DD` (the phone's local date). Missing header means server UTC date. In `DEMO_MODE=1`, the server adds the user's demo day offset.
- Errors: `{"error": {"code": "<code>", "message": "<human text>"}}`

| HTTP | code | When |
|---|---|---|
| 401 | `unknown_user` | Missing or unknown `X-User-Id` |
| 404 | `not_found` | Unknown lesson or question |
| 409 | `not_placed` | Lesson requested before placement is done |
| 409 | `already_answered` | Same question answered twice in one lesson |
| 422 | `invalid_response` | Response shape does not match the question format |

### Public question

Questions sent to the app are the schema in `question.schema.json` **minus** `answer`, `explanation`, `provenance`, `placement`. For `reorder`, `options` are shuffled. `difficulty_rating` is included (current live value, int).

### Response shapes by format

| format | `response` |
|---|---|
| `mcq`, `predict_output` | `"b"` (option id) |
| `tap_line` | `4` (1-indexed line) |
| `tap_node` | `"session"` (node id) |
| `reorder` | `["s1","s2","s3","s4","s5"]` |

---

## Endpoints

### `GET /health`
`200 {"ok": true, "questions": 112}`

### `GET /v1/topics`
Returns `contracts/topics.json` verbatim.

### `POST /v1/users`
```json
// request
{ "display_name": "Tim" }
// 201
{ "user_id": "u_7f3a9c", "display_name": "Tim", "placed": false }
```

### `GET /v1/me`
```json
{ "user_id": "u_7f3a9c", "display_name": "Tim", "placed": true,
  "streak": { "current": 3, "best": 5, "today_done": false } }
```

### `GET /v1/placement`
```json
{ "questions": [ /* 10 public questions, one per topic */ ] }
```
In `DEMO_MODE=1`, `?limit=n` returns only n questions (split evenly across tracks) for a short live demo. Without `?limit`, demo mode defaults to `DEMO_PLACEMENT_LIMIT` questions (env var, default 4; `0` = full test), so the app needs no demo-specific code. Uncovered topics still move through same-track spillover (see `rating.md`).

### `POST /v1/placement`
No per-question feedback during placement; submit all at once.
```json
// request
{ "responses": [
    { "question_id": "sd-caching-001", "response": "b", "time_ms": 8200 },
    { "question_id": "dbg-binary-search-flip-comparison-01", "response": 3, "time_ms": 15400 }
] }
// 200
{ "results": [
    { "question_id": "sd-caching-001", "correct": true },
    { "question_id": "dbg-binary-search-flip-comparison-01", "correct": false }
  ],
  "topics": [
    { "topic": "caching", "rating": 1382, "level": "advanced", "readiness": 69 },
    { "topic": "scaling", "rating": 1255, "level": "intermediate", "readiness": 51 },
    { "topic": "binary-search", "rating": 1064, "level": "beginner", "readiness": 23 }
  ] }
```

### `GET /v1/lessons/today`
Idempotent: creates today's lesson on first call, returns the same one after.
```json
{ "lesson_id": "l_2026-11-08_u_7f3a9c",
  "date": "2026-11-08",
  "status": "in_progress",
  "focus_topics": ["binary-search", "async-messaging"],
  "items": [
    { "position": 1, "kind": "focus", "answered": false, "correct": null,
      "question": { /* public question */ } },
    { "position": 6, "kind": "review", "answered": true, "correct": true,
      "question": { /* public question */ } }
  ] }
```
`kind` is `focus | mix | review`. `status` is `in_progress | completed`.

### `POST /v1/answers`
```json
// request
{ "lesson_id": "l_2026-11-08_u_7f3a9c", "question_id": "dbg-binary-search-flip-comparison-01",
  "response": 3, "time_ms": 11800 }
// 200
{ "correct": true,
  "score": 1.0,
  "correct_answer": 3,
  "explanation": "The loop uses < instead of <=, so when lo == hi the last candidate is never checked.",
  "rating": { "topic": "binary-search", "before": 1080, "after": 1107, "delta": 27 },
  "question_rating": { "before": 1250, "after": 1232 },
  "provenance": { /* debugging only: same object as the schema */ },
  "lesson_progress": { "answered": 4, "total": 6 } }
```

### `POST /v1/lessons/{lesson_id}/complete`
Call after the last answer. Marks today done and updates the streak. Idempotent.
```json
// 200
{ "summary": { "correct": 4, "total": 6 },
  "rating_changes": [ { "topic": "binary-search", "before": 1080, "after": 1131 } ],
  "streak": { "current": 4, "best": 5, "today_done": true, "extended": true } }
```
Streak rule: completing a lesson on date D sets `current = current + 1` if the last completed date was D-1, keeps it if it was D, else sets it to 1.

### `GET /v1/lessons/next/preview`
What tomorrow's lesson would contain with current ratings. Used for the "lesson shifted" demo beat.
```json
{ "date": "2026-11-09",
  "focus_topics": [
    { "topic": "recursion", "reason": "missed_last_lesson", "rating": 1062 },
    { "topic": "databases", "reason": "lowest_rating", "rating": 1080 }
  ],
  "items": [ { "topic": "recursion", "track": "debugging", "format": "tap_line", "difficulty_rating": 925, "kind": "focus" } ] }
```

### `GET /v1/progress`
```json
{ "streak": { "current": 4, "best": 5, "today_done": true },
  "overall_readiness": 47,
  "topics": [
    { "topic": "caching", "track": "system-design", "rating": 1334, "level": "advanced",
      "readiness": 62, "answered": 9, "accuracy": 0.78,
      "history": [1200, 1320, 1311, 1334] }
  ] }
```
`history` = rating after each of the last 10 rated answers in that topic (sparkline).

### Demo only (`DEMO_MODE=1`, otherwise 404)

- `POST /v1/demo/reset` `{ "user_id": "demo" }` restores the seeded demo user (6-day streak, placed, some history).
- `POST /v1/demo/advance-day` (uses `X-User-Id`) shifts that user's "today" by +1 day. `200 {"date": "2026-11-09"}`
- `POST /v1/demo/switch` `{ "user_id": "demo" }` returns `200 { "user_id": "demo", "display_name": "Tim", "placed": true, "streak": { "current": 6, "best": 6, "today_done": false } }`. The app stores the returned `user_id` and reloads Home. Triggered by a hidden control (long-press the logo for 1 s).

In `DEMO_MODE=1`, lessons for the `demo` user have 3 items (1 SD focus, 1 debugging focus, 1 mix) so the whole lesson fits the live demo.

The server rebuilds starting data on every boot: all `/content` questions are upserted (seed `difficulty_rating` only applies to new questions; learned live ratings are kept) and the demo user is reset from `content/demo/demo-user.json`. Other users' data is never touched.

---

## Accounts, learning modules, ranked tests

Feature flags: `GET /v1/config` returns `{"features": {"learn": true, "ranked": true, "accounts": true}}`. Each feature's routes return 404 when its env flag (`FEATURE_LEARN`, `FEATURE_RANKED`, `FEATURE_ACCOUNTS`) is `0`; the app hides it.

### Identity with accounts
- Guests (no password) keep using `X-User-Id`.
- Accounts send `Authorization: Bearer <token>`. An account's `X-User-Id` alone is rejected with `401 session_expired`, which also covers an expired or unknown token.
- `GET /v1/me` adds `"username": "alice" | null, "has_account": bool`.

| HTTP | code | When |
|---|---|---|
| 401 | `session_expired` | Bad or expired token, or an account used without a token |
| 401 | `bad_credentials` | Wrong username or password |
| 409 | `username_taken` | Signup with a taken username |
| 429 | `too_many_attempts` | 10 failed sign-ins for one username in 15 minutes |
| 403 | `account_required` | Ranked test started by a guest |
| 409 | `locked` | Learning checkpoint answered before earlier sections pass |
| 409 | `already_taken` | Ranked tier already attempted (one attempt per account per tier, ever) |
| 409 | `time_up` | Ranked answer after the deadline |
| 409 | `not_finished` | Ranked result requested while the attempt is still running |

### `POST /v1/auth/signup`
`{ "username": "alice_1", "password": "at least 8 chars" }` returns `201 { "token": "...", "claimed_guest": true, "user": { /* /v1/me shape */ } }`. Usernames are 3 to 20 characters from `[a-z0-9_]`, stored lowercase. Prefixes `sample_` and `demo` are reserved. If `X-User-Id` names a guest, that guest becomes the account: same id, with all progress kept. The shared demo user is never claimed.

### `POST /v1/auth/login`, `POST /v1/auth/logout`
Login: `{ "username", "password" }` returns `{ "token", "user" }`. Sessions last 30 days. Logout deletes the bearer session.

### Learning modules (`contracts/learn.schema.json`, `content/learn/<topic>.json`)
- `GET /v1/learn` returns `{ "modules": [ { "topic", "track", "title", "summary", "minutes", "sections": 4, "passed": 1, "completed": false } ] }`, in topics.json order.
- `GET /v1/learn/{topic}` returns the module with each `check` stripped of `answer` and `explanation`, plus `"progress": { "passed": ["s1"], "sections": 4, "completed": false }`.
- `POST /v1/learn/{topic}/check` takes `{ "section_id", "response": "b" }` and returns `{ "correct", "explanation"? , "passed", "sections", "completed" }`. The explanation is returned only when the answer is correct, and wrong answers can retry. Checkpoints never change Elo.

### Ranked tests (`contracts/ranked.schema.json`, `content/ranked/tests.json`)
Three tiers (`beginner`, `intermediate`, `advanced`). Each has 10 fixed questions (5 system design, 5 debugging), in the same order for everyone. These questions live only in `content/ranked/` and are never used in placement or lessons. The server clock is the only clock.
- `GET /v1/ranked` returns `{ "has_account", "tiers": [ { "id", "title", "description", "time_limit_s", "question_count", "suggested", "takers", "attempt": null | {"status": "in_progress", "answered", "total", "remaining_ms"} | {"status": "finished", "score", "total", "time_ms", "rank", "takers", "top_percent"} } ] }`.
- `POST /v1/ranked/{tier}/start` creates the single attempt, or resumes it if it is still running. It returns `{ "tier", "title", "status": "in_progress", "time_limit_s", "remaining_ms", "total", "questions": [public questions], "answered": {"<qid>": response} }`.
- `GET /v1/ranked/{tier}/attempt` returns the same shape (resume only).
- `POST /v1/ranked/{tier}/answer` takes `{ "question_id", "response" }` and returns `{ "saved": true, "answered", "total", "remaining_ms" }`. There is no correctness feedback, and answers are final. It updates the student's topic Elo; question ratings are frozen.
- `POST /v1/ranked/{tier}/submit` finishes the attempt and returns the result below.
- `GET /v1/ranked/{tier}/result` returns `{ "tier", "title", "status": "finished", "score", "total", "time_ms", "rank", "takers", "top_percent", "review": [ { "question", "response" | null, "correct", "correct_answer", "explanation" } ] }`. Unanswered questions count as wrong. `time_ms` is `min(finish, deadline) - start`.
- `GET /v1/ranked/{tier}/leaderboard` returns `{ "tier", "title", "takers", "top": [ { "rank", "username", "score", "total", "time_ms", "sample", "you" } ] (top 50), "you": entry + "top_percent" | null }`. Ordering is score descending, then time ascending, then earliest finish.

In `DEMO_MODE=1`, the server seeds 24 labeled sample players (`sample_user_NN`, `"sample": true`, unable to sign in) on every boot. The demo user (`demo_tim`, no password) has one seeded Beginner result; the Intermediate and Advanced tiers stay open to take live.
