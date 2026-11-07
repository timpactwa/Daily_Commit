import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "./api";
export const topicName = (id: string) =>
  id
    .split("-")
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(" ");
export function buzz() {
  navigator.vibrate?.(12);
}
export function ErrorNotice({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  return (
    <div className="error" role="alert">
      <strong>Let’s try that again.</strong>
      <p>{error instanceof Error ? error.message : "Something went wrong."}</p>
      {error instanceof ApiError && error.status === 404 && (
        <p>This feature is still being connected on the server.</p>
      )}
      {error instanceof ApiError && error.code === "session_expired" ? (
        <Link className="primary" to="/account">
          Sign in →
        </Link>
      ) : error instanceof ApiError && error.code === "unknown_user" ? (
        <Link
          className="primary"
          to="/onboarding"
          onClick={() => api.signOut()}
        >
          Start a new session →
        </Link>
      ) : (
        <button onClick={retry}>Retry</button>
      )}
    </div>
  );
}
export function Loading() {
  return (
    <div className="loading" role="status">
      <span className="spinner" /> Getting your practice ready…
    </div>
  );
}
export function useResource<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<unknown>();
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let active = true;
    setError(undefined);
    setData(undefined);
    load()
      .then((value) => {
        if (active) setData(value);
      })
      .catch((err) => {
        if (active) setError(err);
      });
    return () => {
      active = false;
    };
  }, [version]);
  return { data, error, retry: () => setVersion((v) => v + 1) };
}
export function Resource<T>({
  resource,
  children,
}: {
  resource: ReturnType<typeof useResource<T>>;
  children: (data: T) => ReactNode;
}) {
  if (resource.error)
    return <ErrorNotice error={resource.error} retry={resource.retry} />;
  if (resource.data === undefined) return <Loading />;
  return children(resource.data);
}
/** Inline markup used by content: `code` and **bold**. Everything else is plain text. */
export function Rich({ text }: { text: string }) {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith("`") && p.endsWith("`") && p.length > 1 ? (
          <code className="inline-code" key={i}>{p.slice(1, -1)}</code>
        ) : p.startsWith("**") && p.endsWith("**") && p.length > 3 ? (
          <strong key={i}>{p.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  );
}
/** mm:ss */
export function clockText(ms: number) {
  const s = Math.max(0, Math.round(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}
