import type { Option } from "../api";
export function Reorder({
  options,
  value,
  onChange,
  disabled,
}: {
  options: Option[];
  value: string[];
  onChange: (ids: string[]) => void;
  disabled: boolean;
}) {
  return (
    <div className="reorder">
      <p className="small">
        Tap steps in order. Tap a chosen step to put it back.
      </p>
      <ol className="ordered" aria-label="Your step order">
        {value.length === 0 && (
          <li className="empty-slot">Your first step goes here</li>
        )}
        {value.map((id, i) => (
          <li key={id}>
            <button
              className="option selected"
              disabled={disabled}
              onClick={() => onChange(value.filter((v) => v !== id))}
              aria-label={`Remove step ${i + 1}: ${options.find((o) => o.id === id)?.text}`}
            >
              <span className="option-key">{i + 1}</span>
              {options.find((o) => o.id === id)?.text}
              <span className="remove">×</span>
            </button>
          </li>
        ))}
      </ol>
      <div className="options" aria-label="Available steps">
        {options
          .filter((o) => !value.includes(o.id))
          .map((o) => (
            <button
              className="option"
              disabled={disabled}
              key={o.id}
              onClick={() => onChange([...value, o.id])}
            >
              <span className="option-key">+</span>
              {o.text}
            </button>
          ))}
      </div>
      <p className="small" aria-live="polite">
        {value.length} of {options.length} steps ordered
      </p>
      {value.length > 0 && (
        <button
          className="quiet"
          disabled={disabled}
          onClick={() => onChange([])}
        >
          Start over
        </button>
      )}
    </div>
  );
}
