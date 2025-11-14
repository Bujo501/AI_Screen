// filepath: src/components/QuestionsPanel.tsx
import React, { useEffect, useState } from "react";

type QAData = Record<string, string[] | string>;

function toList(v: string[] | string | undefined | null): string[] {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

export default function QuestionsPanel() {
  const [data, setData] = useState<QAData | null>(null);

  useEffect(() => {
    const handler = (e: Event) => setData((e as CustomEvent).detail as QAData);
    window.addEventListener("questions:update", handler as EventListener);
    return () => window.removeEventListener("questions:update", handler as EventListener);
  }, []);

  if (!data) {
    return (
      <div className="card p-3 text-sm text-[var(--muted)]">
        Upload a resume with <b>Upload &amp; Parse</b> to generate questions.
      </div>
    );
  }

  const entries = Object.entries(data);
  if (entries.length === 0) {
    return <div className="card p-3 text-sm text-[var(--muted)]">No questions generated.</div>;
  }

  return (
    <div className="space-y-3">
      {entries.map(([topic, qs]) => (
        <div key={topic} className="card p-3">
          <div className="font-semibold mb-2">{topic}</div>
          <ul className="list-disc pl-5 text-sm space-y-1">
            {toList(qs).map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
