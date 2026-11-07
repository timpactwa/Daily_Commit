import type { PublicQuestion, ResponseValue } from "../api";
import { buzz, topicName } from "../ui";
import { Reorder } from "./Reorder";
import { TapNode } from "./TapNode";
export function Question({
  question: q,
  value,
  onChange,
  disabled = false,
}: {
  question: PublicQuestion;
  value?: ResponseValue;
  onChange: (v: ResponseValue) => void;
  disabled?: boolean;
}) {
  const select = (v: ResponseValue) => {
    buzz();
    onChange(v);
  };
  return (
    <div className="question">
      <div className="question-meta">
        <span className="tag">
          {q.track === "debugging" ? "⌘ DEBUGGING" : "◇ SYSTEM DESIGN"}
        </span>
        <span>{topicName(q.topic)}</span>
      </div>
      {q.scenario && <p className="scenario">{q.scenario}</p>}
      <h2>{q.prompt}</h2>
      {q.code &&
        (q.format === "tap_line" ? (
          <div className="code" aria-label="Select the buggy line">
            {q.code.split("\n").map((line, i) => (
              <button
                disabled={disabled}
                aria-pressed={value === i + 1}
                className={value === i + 1 ? "code-line selected" : "code-line"}
                onClick={() => select(i + 1)}
                key={i}
                aria-label={`Line ${i + 1}: ${line}`}
              >
                <span>{i + 1}</span>
                <code>{line || " "}</code>
              </button>
            ))}
          </div>
        ) : (
          <pre className="code">{q.code}</pre>
        ))}
      {q.test_output && (
        <div className="test-output">
          <p className="eyebrow">FAILING TESTS</p>
          <pre>{q.test_output}</pre>
        </div>
      )}
      {q.format === "tap_node" && (
        <TapNode
          question={q}
          value={typeof value === "string" ? value : undefined}
          onChange={select}
          disabled={disabled}
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
            <button
              disabled={disabled}
              className={value === option.id ? "option selected" : "option"}
              aria-pressed={value === option.id}
              onClick={() => select(option.id)}
              key={option.id}
            >
              <span className="option-key">{String.fromCharCode(65 + i)}</span>
              {option.text}
            </button>
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
