import { useEffect, useRef } from "react";
import type { AnswerResult, PublicQuestion } from "../api";
import { Explanation } from "./Explanation";
export function FeedbackSheet({
  result,
  question,
  onContinue,
}: {
  result: AnswerResult;
  question: PublicQuestion;
  onContinue: () => void;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);
  const answer = Array.isArray(result.correct_answer)
    ? result.correct_answer
        .map((id) => question.options?.find((o) => o.id === id)?.text ?? id)
        .join(" → ")
    : question.format === "tap_line"
      ? `Line ${result.correct_answer}`
      : (question.options?.find((o) => o.id === result.correct_answer)?.text ??
        String(result.correct_answer));
  return (
    <section
      className={`feedback ${result.correct ? "correct" : "incorrect"}`}
      role="region"
      aria-label="Answer feedback"
      aria-live="polite"
    >
      <div className="split">
        <h2>
          {result.correct
            ? "✓ Nicely done."
            : result.score > 0
              ? "Almost there."
              : "A useful lesson."}
        </h2>
        <span className="delta">
          {result.rating.delta >= 0 ? "+" : ""}
          {result.rating.delta} Elo
        </span>
      </div>
      {!result.correct && (
        <p>
          <strong>Correct answer: </strong>
          {answer}
        </p>
      )}
      <Explanation text={result.explanation} />
      <button ref={ref} className="primary full" onClick={onContinue}>
        Continue →
      </button>
    </section>
  );
}
