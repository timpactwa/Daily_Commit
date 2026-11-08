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
  const correct = lesson.items.filter((i) => i.answered && i.correct).length;
  const required = lesson.mastery?.required ?? 0;
  const passed = !lesson.mastery || correct >= required || lesson.status === "completed";
  async function submit() {
    if (!item || value === undefined || busy) return;
    setBusy(true);
    setError(undefined);
    try {
      const result = await api.submitAnswer({
          lesson_id: lesson.lesson_id,
          question_id: item.question.id,
          response: value,
          time_ms: Math.round(performance.now() - started.current),
        });
      if (result.retry_available) {
        setLesson({ ...lesson, items: lesson.items.map(i => i.position === item.position
          ? { ...i, attempts_used: result.attempts_used, attempt_limit: result.attempt_limit,
              tried_responses: [...(i.tried_responses ?? []), value] } : i) });
        setValue(undefined);
      } else setFeedback(result);
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
  async function retry() {
    setBusy(true);
    setError(undefined);
    try {
      setLesson(await api.retryLesson(lesson.lesson_id));
      setValue(undefined);
      setFeedback(undefined);
      started.current = performance.now();
    } catch (err) { setError(err); }
    finally { setBusy(false); }
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
      {lesson.mastery && <p className="small practice-requirement">Pass this practice: {required} of {lesson.items.length} correct. {correct} earned so far.</p>}
      {item ? (
        <>
          <div className="card">
            {item.attempt_limit && <p className="eyebrow">TRY {(item.attempts_used ?? 0) + 1} OF {item.attempt_limit}</p>}
            {!!item.attempts_used && !feedback && <p className="retry-note" role="status">Not quite. You have one try left. Choose a different answer.</p>}
            <Question
              question={item.question}
              value={value}
              onChange={setValue}
              disabled={busy || !!feedback}
              outcome={feedback ? (feedback.correct ? "correct" : "incorrect") : undefined}
              excludedResponses={item.tried_responses}
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
              response={value}
              result={feedback}
              onContinue={next}
            />
          )}
        </>
      ) : (
        <div className="card">
          <p className="eyebrow">{passed ? "PRACTICE COMPLETE" : "KEEP PRACTICING"}</p>
          <h1>
            {passed ? <>Another commit.<br />A little stronger.</> : <>You’re learning.<br />Give it another try.</>}
          </h1>
          {lesson.mastery && <p>{correct} of {lesson.items.length} correct within the allowed tries. {passed ? "You can finish this lesson." : `Get at least ${required} correct to move on. Review the explanations, then retry the practice.`}</p>}
          {passed ? <button className="primary full" disabled={busy} onClick={complete}>
            {busy ? "Saving…" : "Finish lesson →"}
          </button> : <button className="primary full" disabled={busy} onClick={retry}>{busy ? "Preparing…" : "Retry practice →"}</button>}
        </div>
      )}
      {!!error && (
        <ErrorNotice error={error} retry={item ? submit : passed ? complete : retry} />
      )}
      <Link className="text-link" to="/tomorrow">
        See how tomorrow’s lesson is adapting ↗
      </Link>
    </section>
  );
}
