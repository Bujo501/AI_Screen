// ===========================================
// filepath: src/components/CandidateCard.tsx
// ===========================================
import React from "react";

type Person = {
  id?: string;
  name: string;
  role: string;
  initials: string;
  score: number;
  years: number;
  updated: string;
  badge: string;
  tags: string[];
};

export default function CandidateCard({ person }: { person: Person }) {
  return (
    <div className="card p-4 relative">
      <div className="absolute right-3 top-3">
        <span className="px-2 py-1 rounded-xl bg-blue-600 text-white text-xs font-semibold">
          {Math.max(0, Math.min(100, Math.round(person.score)))}% match
        </span>
      </div>
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-slate-200 flex items-center justify-center font-bold">
          {person.initials}
        </div>
        <div>
          <div className="font-semibold">{person.name}</div>
          <div className="text-xs text-[var(--muted)]">{person.role}</div>
        </div>
      </div>
      <div className="mt-2 text-xs text-[var(--muted)]">{person.years} years • {person.updated}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {person.tags.map((t) => <span key={t} className="tag">{t}</span>)}
      </div>
      <div className="mt-3 flex gap-2">
        <button className="btn">View Details</button>
        <button className="btn">Schedule Interview</button>
      </div>
    </div>
  );
}

