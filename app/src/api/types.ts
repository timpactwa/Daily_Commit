// Types for contracts/api.md and contracts/question.schema.json (public view).
// Owned by Tim. Screens import from "src/api", never from fetch directly.

export type Track = "system-design" | "debugging";
export type Format = "mcq" | "tap_line" | "reorder" | "tap_node" | "predict_output";
export type Level = "level-1" | "level-2" | "level-3" | "level-4" | "level-5" | "level-6" | "level-7";
export type LessonItemKind = "focus" | "mix" | "review";

export interface Option {
  id: string;
  text: string;
}

export interface DiagramNode {
  id: string;
  label: string;
  kind?: "client" | "service" | "lb" | "cache" | "db" | "queue" | "cdn" | "external";
  note?: string;
}

export interface DiagramEdge {
  from: string;
  to: string;
  label?: string;
}

/** A question as the app receives it: no answer, explanation or provenance. */
export interface PublicQuestion {
  id: string;
  version: 1;
  track: Track;
  topic: string;
  format: Format;
  prompt: string;
  scenario?: string;
  code?: string;
  language?: "python";
  test_output?: string;
  options?: Option[]; // reorder: already shuffled by the server
  diagram?: { nodes: DiagramNode[]; edges: DiagramEdge[] };
  difficulty_rating: number;
  tags?: string[];
}

/**
 * mcq / predict_output: option id. tap_line: 1-indexed line number.
 * tap_node: node id. reorder: option ids in the order the student chose.
 */
export type ResponseValue = string | number | string[];

export interface Provenance {
  source_function: string;
  mutation_operator: string;
  original_line: string;
  mutated_line: string;
  tests_failed: number;
  tests_total: number;
  generated_at?: string;
}

export interface Topic {
  id: string;
  track: Track;
  name: string;
  description: string;
}

export interface Streak {
  current: number;
  best: number;
  today_done: boolean;
  extended?: boolean;
}

export interface User {
  user_id: string;
  display_name: string;
  placed: boolean;
  /** null for guests (no account). */
  username?: string | null;
  has_account?: boolean;
  streak?: Streak;
}

export interface AuthResult {
  token: string;
  claimed_guest?: boolean;
  user: User;
}

export interface Features {
  learn: boolean;
  ranked: boolean;
  accounts: boolean;
}

// ---- learning modules (contracts/learn.schema.json) --------------------------

export interface LearnSummary {
  topic: string;
  track: Track;
  title: string;
  summary: string;
  minutes: number;
  sections: number;
  passed: number;
  completed: boolean;
}

export interface LearnSection {
  id: string;
  heading: string;
  body: string[];
  example: { title: string; code?: string; text?: string };
  /** answer + explanation are withheld until checked. */
  check: { prompt: string; options: Option[] };
}

export interface LearnModule {
  topic: string;
  track: Track;
  title: string;
  summary: string;
  minutes: number;
  sections: LearnSection[];
  sources: { title: string; url: string; publisher: string }[];
  progress: { passed: string[]; sections: number; completed: boolean };
}

export interface LearnCheckResult {
  correct: boolean;
  explanation?: string;
  passed: string[];
  sections: number;
  completed: boolean;
}

// ---- ranked tests --------------------------------------------------------------

export type TierId = "beginner" | "intermediate" | "advanced";

export interface Standing {
  rank: number;
  takers: number;
  top_percent: number;
}

export type AttemptSummary =
  | { status: "in_progress"; answered: number; total: number; remaining_ms: number }
  | ({ status: "finished"; score: number; total: number; time_ms: number } & Standing);

export interface RankedTier {
  id: TierId;
  title: string;
  description: string;
  time_limit_s: number;
  question_count: number;
  suggested: boolean;
  min_level: number;
  max_level: number;
  takers: number;
  attempt: AttemptSummary | null;
}

export interface RankedSession {
  tier: TierId;
  title: string;
  status: "in_progress";
  time_limit_s: number;
  remaining_ms: number;
  total: number;
  questions: PublicQuestion[];
  answered: Record<string, ResponseValue>;
}

export interface RankedResult extends Standing {
  tier: TierId;
  title: string;
  status: "finished";
  score: number;
  total: number;
  time_ms: number;
  review: {
    question: PublicQuestion;
    response: ResponseValue | null;
    correct: boolean;
    correct_answer: ResponseValue;
    explanation: string;
  }[];
}

export interface LeaderboardEntry {
  rank: number;
  username: string;
  score: number;
  total: number;
  time_ms: number;
  sample: boolean;
  you: boolean;
  top_percent?: number;
}

export interface Leaderboard {
  tier: TierId;
  title: string;
  takers: number;
  top: LeaderboardEntry[];
  you: LeaderboardEntry | null;
}

export interface TopicLevel {
  topic: string;
  rating: number;
  level: Level;
  readiness: number;
}

export interface PlacementAnswer {
  question_id: string;
  response: ResponseValue;
  time_ms: number;
}

export interface PlacementResult {
  results: { question_id: string; correct: boolean }[];
  topics: TopicLevel[];
}

export interface LessonItem {
  position: number;
  kind: LessonItemKind;
  answered: boolean;
  correct: boolean | null;
  question: PublicQuestion;
  attempts_used?: number;
  attempt_limit?: number;
  tried_responses?: ResponseValue[];
}

export interface Lesson {
  lesson_id: string;
  date: string;
  status: "in_progress" | "completed";
  focus_topics: string[];
  items: LessonItem[];
  mastery?: { required: number; correct: number; answered: number; total: number; can_complete: boolean; round: number };
}

export interface AnswerRequest {
  lesson_id: string;
  question_id: string;
  response: ResponseValue;
  time_ms: number;
}

export interface AnswerResult {
  practice_retry?: boolean;
  retry_available?: false;
  attempts_used?: number;
  attempt_limit?: number;
  correct: boolean;
  score: number;
  correct_answer: ResponseValue;
  explanation: string;
  rating: { topic: string; before: number; after: number; delta: number };
  question_rating: { before: number; after: number };
  provenance?: Provenance;
  lesson_progress: { answered: number; total: number };
}

export interface RetryAnswerResult {
  correct: false;
  retry_available: true;
  attempts_used: number;
  attempt_limit: number;
  lesson_progress: { answered: number; total: number };
}

export interface CompleteResult {
  summary: { correct: number; total: number };
  rating_changes: { topic: string; before: number; after: number }[];
  streak: Streak;
}

export interface Preview {
  date: string;
  focus_topics: { topic: string; reason: "missed_last_lesson" | "lowest_rating" | string; rating: number }[];
  items: { topic: string; track: Track; format: Format; difficulty_rating: number; kind: LessonItemKind }[];
}

export interface TopicProgress {
  topic: string;
  track: Track;
  rating: number;
  level: Level;
  next_level?: Level | null;
  next_level_rating?: number | null;
  level_progress?: number;
  readiness: number;
  answered: number;
  accuracy: number;
  history: number[];
}

export interface Progress {
  streak: Streak;
  overall_readiness: number;
  topics: TopicProgress[];
  skill_levels?: { id: Level; min_rating: number; max_rating: number }[];
}

export type ErrorCode =
  | "unknown_user"
  | "not_found"
  | "not_placed"
  | "already_answered"
  | "not_passed"
  | "practice_busy"
  | "invalid_response"
  | "session_expired"
  | "username_taken"
  | "bad_credentials"
  | "too_many_attempts"
  | "locked"
  | "account_required"
  | "already_taken"
  | "time_up"
  | "not_finished"
  | "network"
  | "server";
