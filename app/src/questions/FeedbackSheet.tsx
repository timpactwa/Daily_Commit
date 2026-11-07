import { useEffect, useRef } from "react";
import type { AnswerResult, PublicQuestion, ResponseValue } from "../api";
import { learningFor } from "../learning/feedback";

function answerText(question: PublicQuestion, value: ResponseValue) {
  const label = (id: string) =>
    question.options?.find((o) => o.id === id)?.text ??
    question.diagram?.nodes.find((node) => node.id === id)?.label ??
    id;
  if (Array.isArray(value)) return value.map(label).join(" → ");
  return question.format === "tap_line"
    ? `Line ${value}`
    : label(String(value));
}
export function FeedbackSheet({
  result,
  question,
  response,
  onContinue,
}: {
  result: AnswerResult;
  question: PublicQuestion;
  response?: ResponseValue;
  onContinue: () => void;
}) {
  const ref = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);
  const guide = learningFor(question, result);
  const correction =
    question.track === "debugging" ? result.provenance : undefined;
  return (
    <section
      className={`feedback ${result.correct ? "correct" : "incorrect"}`}
      role="region"
      aria-label="Answer feedback"
      aria-live="polite"
    >
      <div className="feedback-heading">
        <h2 ref={ref} tabIndex={-1}>
          {result.correct
            ? "You got it. Here’s why."
            : result.score > 0
              ? "Partly there. Let’s connect the steps."
              : "Let’s work through it."}
        </h2>
      </div>
      {!result.correct && (
        <div className="answer-comparison">
          {response !== undefined && (
            <p>
              <strong>Your answer: </strong>
              {answerText(question, response)}
            </p>
          )}
          <p>
            <strong>Correct answer: </strong>
            {answerText(question, result.correct_answer)}
          </p>
        </div>
      )}
      <h3>Why this works</h3>
      <p>{result.explanation}</p>
      {guide && (
        <>
          <h3>{guide.concept}</h3>
          <p>{guide.principle}</p>
          <div className="worked-example">
            <h4>A smaller example</h4>
            <p>{guide.example}</p>
          </div>
        </>
      )}
      {correction && (
        <details className="feedback-details">
          <summary>Trace the failing case and the fix</summary>
          {question.test_output && (
            <>
              <h4>Observed failure</h4>
              <pre>{question.test_output}</pre>
            </>
          )}
          <h4>Faulty line</h4>
          <pre>
            <code>{correction.mutated_line.trim()}</code>
          </pre>
          <h4>Corrected line</h4>
          <pre>
            <code>{correction.original_line.trim()}</code>
          </pre>
          <p>
            Use one failing input to trace the variables with each version. Find
            the first point where the values or control flow differ.
          </p>
        </details>
      )}
      {guide && (
        <>
          <div className="understanding-check">
            <h3>Check your understanding</h3>
            <p>{guide.check}</p>
            <details className="feedback-details">
              <summary>Show the reasoning</summary>
              <p>{guide.reasoning}</p>
            </details>
          </div>
          <details className="feedback-details further-reading">
            <summary>Read more about this concept</summary>
            <p>
              Start with either resource. Links open in a new tab so you can
              keep your place.
            </p>
            <ul>
              {guide.resources.map((reading) => (
                <li key={reading.url}>
                  <a
                    href={reading.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {reading.title} ↗
                    <span className="sr-only"> (opens in a new tab)</span>
                  </a>
                  <span className="reading-publisher">{reading.publisher}</span>
                  <p>{reading.purpose}</p>
                </li>
              ))}
            </ul>
          </details>
        </>
      )}
      <p className="feedback-rating">
        <span className="delta">
          {result.rating.delta >= 0 ? "+" : ""}
          {result.rating.delta} Elo
        </span>{" "}
        · One answer helps tune your next lesson.
      </p>
      <button className="primary full" onClick={onContinue}>
        Continue →
      </button>
    </section>
  );
}
