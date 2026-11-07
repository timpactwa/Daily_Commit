import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  api,
  ApiError,
  type AnswerResult,
  type Lesson as LessonData,
  type ResponseValue,
} from "../api";
import { ErrorNotice, Resource, useResource } from "../ui";
import { isComplete, Question } from "../questions/Question";
import { FeedbackSheet } from "../questions/FeedbackSheet";
export function Lesson() {
  const resource = useResource(api.getLessonToday);
  return (
    <Resource resource={resource}>
      {(lesson) => <Player key={lesson.lesson_id} initial={lesson} />}
    </Resource>
  );
}
function Player({ initial }: { initial: LessonData }) {
  const [lesson, setLesson] = useState(initial);
  const [value, setValue] = useState<ResponseValue>();
  const [feedback, setFeedback] = useState<AnswerResult>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>();
  const started = useRef(performance.now());
  const navigate = useNavigate();
  const item = lesson.items.find((i) => !i.answered);
  const count = lesson.items.filter((i) => i.answered).length;
  async function submit() {
    if (!item || value === undefined || busy) return;
    setBusy(true);
    setError(undefined);
    try {
      setFeedback(
        await api.submitAnswer({
          lesson_id: lesson.lesson_id,
          question_id: item.question.id,
          response: value,
          time_ms: Math.round(performance.now() - started.current),
        }),
      );
    } catch (err) {
      if (err instanceof ApiError && err.code === "already_answered") {
        // A response can be lost after the server commits. Recover its state
        // instead of retrying the same answer forever.
        try {
          setLesson(await api.getLessonToday());
          setValue(undefined);
          started.current = performance.now();
        } catch (refreshError) { setError(refreshError); }
      } else { setError(err); }
    } finally {
      setBusy(false);
    }
  }
  async function complete() {
    setBusy(true);
    setError(undefined);
    try {
      const result = await api.completeLesson(lesson.lesson_id);
      navigate("/lesson/done", { state: result, replace: true });
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  function next() {
    if (!item || !feedback) return;
    setLesson({
      ...lesson,
      items: lesson.items.map((i) =>
        i.position === item.position
          ? { ...i, answered: true, correct: feedback.correct }
          : i,
      ),
    });
    setFeedback(undefined);
    setValue(undefined);
    started.current = performance.now();
  }
  return (
    <section className="practice">
      <div className="split">
        <Link className="back" to="/">
          ← Today
        </Link>
        <span className="eyebrow">
          DAILY PRACTICE · {count}/{lesson.items.length}
        </span>
      </div>
      <progress
        aria-label="Lesson progress"
        value={count}
        max={lesson.items.length}
      />
      {item ? (
        <>
          <div className="card">
            <Question
              question={item.question}
              value={value}
              onChange={setValue}
              disabled={busy || !!feedback}
            />
            {!feedback && (
              <button
                className="primary full"
                disabled={!isComplete(item.question, value) || busy}
                onClick={submit}
              >
                {busy ? "Checking…" : "Check answer →"}
              </button>
            )}
          </div>
          {feedback && (
            <FeedbackSheet
              question={item.question}
              result={feedback}
              onContinue={next}
            />
          )}
        </>
      ) : (
        <div className="card">
          <p className="eyebrow">PRACTICE COMPLETE</p>
          <h1>
            Another commit.
            <br />A little stronger.
          </h1>
          <button className="primary full" disabled={busy} onClick={complete}>
            {busy ? "Saving…" : "Finish lesson →"}
          </button>
        </div>
      )}
      {!!error && (
        <ErrorNotice error={error} retry={item ? submit : complete} />
      )}
      <Link className="text-link" to="/tomorrow">
        See how tomorrow’s lesson is adapting ↗
      </Link>
    </section>
  );
}
