import { useRef, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import {
  api,
  type PlacementAnswer,
  type PlacementResult as Result,
  type PublicQuestion,
} from "../api";
import { Question, isComplete } from "../questions/Question";
import { ErrorNotice, Resource, topicName, useResource } from "../ui";
const RESULT_KEY = "dc.placement_result";
export function Placement() {
  const resource = useResource(() =>
    api.getPlacement(
      new URLSearchParams(location.search).get("demo") === "1" ? 4 : undefined,
    ),
  );
  return (
    <Resource resource={resource}>
      {(data) => <PlacementPlayer questions={data.questions} />}
    </Resource>
  );
}
function PlacementPlayer({ questions }: { questions: PublicQuestion[] }) {
  const [answers, setAnswers] = useState<PlacementAnswer[]>([]);
  const [values, setValues] = useState<
    Record<string, PlacementAnswer["response"]>
  >({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const started = useRef(performance.now());
  const navigate = useNavigate();
  const q = questions[answers.length];
  async function next() {
    if (!q || values[q.id] === undefined || busy) return;
    const responses = [
      ...answers,
      {
        question_id: q.id,
        response: values[q.id],
        time_ms: Math.round(performance.now() - started.current),
      },
    ];
    if (responses.length < questions.length) {
      setAnswers(responses);
      started.current = performance.now();
      return;
    }
    setBusy(true);
    setError(undefined);
    try {
      const result = await api.submitPlacement(responses);
      try {
        sessionStorage.setItem(RESULT_KEY, JSON.stringify(result));
      } catch {
        /* memory navigation works without storage */
      }
      navigate("/placement/result", { state: result, replace: true });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  if (!q)
    return (
      <div className="card">
        <h2>No placement questions yet.</h2>
        <p>The question bank is being prepared. Please try again shortly.</p>
        <Link to="/">Back to today</Link>
      </div>
    );
  return (
    <section className="practice">
      <div className="split">
        <p className="eyebrow">FIND YOUR STARTING POINT</p>
        <span className="eyebrow">
          {answers.length + 1} / {questions.length}
        </span>
      </div>
      <progress
        aria-label="Placement progress"
        max={questions.length}
        value={answers.length}
      />
      <div className="card">
        <Question
          key={q.id}
          question={q}
          value={values[q.id]}
          onChange={(value) => setValues({ ...values, [q.id]: value })}
          disabled={busy}
        />
        <button
          className="primary full"
          disabled={busy || !isComplete(q, values[q.id])}
          onClick={next}
        >
          {busy
            ? "Finding your level…"
            : answers.length === questions.length - 1
              ? "See my starting point →"
              : "Next question →"}
        </button>
      </div>
      <p className="small centered">
        No grades. No pressure. Just a starting point that fits you.
      </p>
      {!!error && <ErrorNotice error={error} retry={next} />}
    </section>
  );
}
export function PlacementResult() {
  const location = useLocation();
  let result = location.state as Result | null;
  if (!result) {
    try {
      result = JSON.parse(sessionStorage.getItem(RESULT_KEY) ?? "null");
    } catch {
      /* unavailable storage */
    }
  }
  if (!result?.topics) return <Navigate to="/" replace />;
  return (
    <section className="practice">
      <p className="eyebrow">YOUR STARTING POINT</p>
      <h1>
        A little clarity.
        <br />A path forward.
      </h1>
      <p>
        Your daily practice will adapt from here. Every answer helps us find the
        right challenge.
      </p>
      {(["system-design", "debugging"] as const).map((track) => (
        <div className="card track-card" key={track}>
          <h2>
            {track === "system-design" ? "◇ System design" : "⌘ Debugging"}
          </h2>
          {result!.topics
            .filter(
              (t) =>
                ([
                  "caching",
                  "scaling",
                  "databases",
                  "async-messaging",
                  "reliability",
                ].includes(t.topic)
                  ? "system-design"
                  : "debugging") === track,
            )
            .map((t) => (
              <div className="topic-row" key={t.topic}>
                <div>
                  <strong>{topicName(t.topic)}</strong>
                  <p>{Math.round(t.rating)} Elo</p>
                </div>
                <span className={`level ${t.level}`}>{topicName(t.level)}</span>
              </div>
            ))}
        </div>
      ))}
      <Link className="primary full" to="/">
        Let’s make a daily habit →
      </Link>
    </section>
  );
}
