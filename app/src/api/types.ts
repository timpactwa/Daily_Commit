// Types for contracts/api.md and contracts/question.schema.json (public view).
// Owned by Tim. Screens import from "src/api", never from fetch directly.

export type Track = "system-design" | "debugging";
export type Format = "mcq" | "tap_line" | "reorder" | "tap_node" | "predict_output";
export type Level = "beginner" | "intermediate" | "advanced";
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
  streak?: Streak;
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
}

export interface Lesson {
  lesson_id: string;
  date: string;
  status: "in_progress" | "completed";
  focus_topics: string[];
  items: LessonItem[];
}

export interface AnswerRequest {
  lesson_id: string;
  question_id: string;
  response: ResponseValue;
  time_ms: number;
}

export interface AnswerResult {
  correct: boolean;
  score: number;
  correct_answer: ResponseValue;
  explanation: string;
  rating: { topic: string; before: number; after: number; delta: number };
  question_rating: { before: number; after: number };
  provenance?: Provenance;
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
  readiness: number;
  answered: number;
  accuracy: number;
  history: number[];
}

export interface Progress {
  streak: Streak;
  overall_readiness: number;
  topics: TopicProgress[];
}

export type ErrorCode =
  | "unknown_user"
  | "not_found"
  | "not_placed"
  | "already_answered"
  | "invalid_response"
  | "network"
  | "server";
