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
In `DEMO_MODE=1`, `?limit=n` returns only n questions (split evenly across tracks) for a short live demo. Uncovered topics still move through same-track spillover (see `rating.md`).

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
