import type { PublicQuestion, ResponseValue } from "../api";
import { buzz, Confetti, topicName } from "../ui";
import { Reorder } from "./Reorder";
import { TapNode } from "./TapNode";
export function Question({
  question: q,
  value,
  onChange,
  disabled = false,
  outcome,
  excludedResponses = [],
}: {
  question: PublicQuestion;
  value?: ResponseValue;
  onChange: (v: ResponseValue) => void;
  disabled?: boolean;
  /** Set after grading: animates the chosen answer (pop + confetti, or shake). Display only. */
  outcome?: "correct" | "incorrect";
  excludedResponses?: ResponseValue[];
}) {
  const mark = outcome === "correct" ? " ok" : outcome === "incorrect" ? " bad" : "";
  const select = (v: ResponseValue) => {
    buzz();
    onChange(v);
  };
  return (
    <div className="question">
      <div className="question-meta">
        <span className={`tag ${q.track === "debugging" ? "tag-debug" : "tag-sd"}`}>
          {q.track === "debugging" ? "⌘ DEBUGGING" : "◇ SYSTEM DESIGN"}
        </span>
        <span>{topicName(q.topic)}</span>
      </div>
      {q.scenario && <p className="scenario">{q.scenario}</p>}
      <h2>{q.prompt}</h2>
      {q.test_output && (
        <section className="test-output term" aria-label="Failing tests">
          <div className="term-bar">
            <span className="fail-dot" aria-hidden="true">●</span>
            <p className="eyebrow">FAILING TESTS</p>
          </div>
          <pre>{q.test_output}</pre>
        </section>
      )}
      {q.code &&
        (q.format === "tap_line" ? (
          <div className="term">
            <TermBar title={fileName(q.code)} />
            <div className="code" aria-label="Select the buggy line">
              {q.code.split("\n").map((line, i) => (
                <button
                  disabled={disabled || excludedResponses.includes(i + 1)}
                  aria-pressed={value === i + 1}
                  className={value === i + 1 ? `code-line selected${mark}` : "code-line"}
                  onClick={() => select(i + 1)}
                  key={i}
                  aria-label={`Line ${i + 1}: ${line}`}
                >
                  <span>{i + 1}</span>
                  <code>{line || " "}</code>
                </button>
              ))}
            </div>
            {outcome === "correct" && <Confetti />}
          </div>
        ) : (
          <div className="term">
            <TermBar title={fileName(q.code)} />
            <pre className="code">{q.code}</pre>
          </div>
        ))}
      {q.format === "tap_node" && (
        <TapNode
          question={q}
          value={typeof value === "string" ? value : undefined}
          onChange={select}
          disabled={disabled}
          excludedIds={excludedResponses.filter((r): r is string => typeof r === "string")}
        />
      )}{" "}
      {q.format === "reorder" && (
        <Reorder
          options={q.options ?? []}
          value={Array.isArray(value) ? value : []}
          onChange={select}
          disabled={disabled}
        />
      )}{" "}
      {q.format !== "tap_line" && q.format !== "reorder" && (
        <div className="options">
          {q.options?.map((option, i) => (
            <div className="option-wrap" key={option.id}>
              <button
                disabled={disabled || excludedResponses.includes(option.id)}
                className={value === option.id ? `option selected${mark}` : "option"}
                aria-pressed={value === option.id}
                onClick={() => select(option.id)}
              >
                <span className="option-key">{String.fromCharCode(65 + i)}</span>
                {option.text}
              </button>
              {value === option.id && outcome === "correct" && <Confetti />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
export function isComplete(q: PublicQuestion, value?: ResponseValue): boolean {
  return (
    value !== undefined &&
    (!Array.isArray(value) || value.length === q.options?.length)
  );
}
function fileName(code: string) {
  const m = code.match(/def\s+([A-Za-z_]\w*)/);
  return m ? `${m[1]}.py` : "snippet.py";
}
function TermBar({ title }: { title: string }) {
  return (
    <div className="term-bar" aria-hidden="true">
      <span className="term-title">{title}</span>
      <span className="term-lang">python</span>
    </div>
  );
}
