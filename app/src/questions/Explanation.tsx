import type { ReactNode } from "react";

/** Render only HTTPS citation links. Other content remains escaped plain text. */
export function Explanation({ text }: { text: string }) {
  const parts: ReactNode[] = [];
  const citations = /\[([^\]\n]+)\]\((https:\/\/[^\s)]+)\)/g;
  let cursor = 0;
  for (const match of text.matchAll(citations)) {
    const index = match.index!;
    let url: URL;
    try { url = new URL(match[2]); } catch { continue; }
    if (url.username || url.password) continue;
    parts.push(text.slice(cursor, index));
    parts.push(
      <a className="source-link" href={url.href} target="_blank" rel="noopener noreferrer" key={index}>
        {match[1]}
      </a>,
    );
    cursor = index + match[0].length;
  }
  parts.push(text.slice(cursor));
  return <p className="explanation">{parts}</p>;
}
