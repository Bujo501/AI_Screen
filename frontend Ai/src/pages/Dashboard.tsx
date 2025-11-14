// ============================================================================
// filepath: src/pages/Dashboard.tsx  (PATCH: keep education/raw_text; no hardcodes)
// ============================================================================
import React, { useEffect, useMemo, useState } from "react";
import CandidateCard from "@/components/CandidateCard";
import UploadModal from "@/components/UploadModal";
import ResumeUpload from "@/components/ResumeUpload";
import QuestionsPanel from "@/components/QuestionsPanel";
import { JobsAPI, MatchAPI, ResumesAPI } from "@/services/http";
import type { JobRequirements, ResumeRecord } from "@/services/http";

type Person = {
  id: string;
  name: string;
  role: string;
  initials: string;
  score: number;
  years: number;
  updated: string;
  badge: string;
  tags: string[];
  education: number;   // <-- keep from DB
  raw_text: string;    // <-- keep from DB
};

const initials = (n?: string) =>
  (n || "??").split(" ").filter(Boolean).map(s => s[0]).slice(0,2).join("").toUpperCase();

export default function Dashboard() {
  const [openUpload, setOpenUpload] = useState(false);
  const [jobs, setJobs] = useState<JobRequirements[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobRequirements | null>(null);
  const [people, setPeople] = useState<Person[]>([]);

  const mapResumes = (rows: ResumeRecord[]): Person[] =>
    rows.map(r => ({
      id: r.id,
      name: r.name || "Candidate",
      role: "—",
      initials: initials(r.name),
      score: 0,
      years: Number(r.years_experience || 0),
      updated: new Date(r.updated_at || r.created_at || Date.now()).toDateString(),
      badge: "New",
      tags: Array.isArray(r.skills) ? r.skills : [],
      education: Number(r.education ?? 0),
      raw_text: String(r.raw_text || ""),
    }));

  useEffect(() => {
    (async () => {
      try {
        const list = await JobsAPI.list<JobRequirements[]>();
        setJobs(list);
        setSelectedJob(prev => prev ?? (list[0] || null));
      } catch {
        setJobs([]); setSelectedJob(null);
      }
    })();
    (async () => {
      try {
        const list = await ResumesAPI.list<ResumeRecord[]>();
        const byId = new Map<string, ResumeRecord>();
        list.forEach(r => byId.set(r.id, r));
        setPeople(mapResumes(Array.from(byId.values())));
      } catch {
        setPeople([]);
      }
    })();
  }, []);

  useEffect(() => {
    const h = () => {
      (async () => {
        try {
          const list = await ResumesAPI.list<ResumeRecord[]>();
          const byId = new Map<string, ResumeRecord>();
          list.forEach(r => byId.set(r.id, r));
          setPeople(mapResumes(Array.from(byId.values())));
        } catch {
          setPeople([]);
        }
      })();
    };
    window.addEventListener("resumes:changed", h as EventListener);
    return () => window.removeEventListener("resumes:changed", h as EventListener);
  }, []);

  const resumesForAPI = useMemo(
    () => people.map(p => ({
      name: p.name,
      email: "",
      phone: "",
      skills: p.tags,
      years_experience: p.years,
      education: p.education,   // <-- use DB value, not hardcoded
      raw_text: p.raw_text,     // <-- use DB value, not tags
    })),
    [people]
  );

  useEffect(() => {
    (async () => {
      if (!selectedJob || people.length === 0) return;
      try {
        const results: Array<{ score: number }> = await MatchAPI.scoreBatch({ resumes: resumesForAPI, job: selectedJob });
        setPeople(prev => prev.map((p, i) => ({ ...p, score: Math.round(results?.[i]?.score ?? 0) })));
      } catch {
        // keep previous scores
      }
    })();
  }, [selectedJob, resumesForAPI, people.length]);

  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-[260px_1fr]">
      <aside className="hidden md:block border-r border-[var(--border)] bg-white">
        <div className="p-5 text-xl font-bold">Recruiter</div>
        <nav className="px-3 space-y-1">
          <a className="block rounded-xl px-3 py-2 bg-indigo-50 text-indigo-700">Dashboard</a>
          <a className="block rounded-xl px-3 py-2 hover:bg-slate-100">Resumes</a>
          <a className="block rounded-xl px-3 py-2 hover:bg-slate-100">Interviews</a>
          <a className="block rounded-xl px-3 py-2 hover:bg-slate-100">Recommendations</a>
          <a className="block rounded-xl px-3 py-2 hover:bg-slate-100">Settings</a>
        </nav>
      </aside>

      <main className="p-6">
        <header className="mb-5 flex items-start justify-between gap-3">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Dashboard</h1>
            <p className="text-sm text-[var(--muted)]">Welcome back! Here’s your recruitment overview.</p>
          </div>
          <div className="flex gap-2">
            <select
              className="input"
              value={selectedJob?.id ?? ""}
              onChange={(e) => setSelectedJob(jobs.find((j) => j.id === e.target.value) || null)}
            >
              <option value="">Select Job</option>
              {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
            </select>
            <button className="btn" onClick={() => setOpenUpload(true)}>⬆ Upload Resume</button>
          </div>
        </header>

        <section className="mb-6 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
          <div className="card p-4"><div className="text-xs text-[var(--muted)]">Total Applications</div><div className="text-2xl font-bold">{people.length}</div><div className="text-xs text-[var(--muted)]">in system</div></div>
          <div className="card p-4"><div className="text-xs text-[var(--muted)]">Pending Reviews</div><div className="text-2xl font-bold">—</div><div className="text-xs text-[var(--muted)]">auto</div></div>
          <div className="card p-4"><div className="text-xs text-[var(--muted)]">Scheduled Interviews</div><div className="text-2xl font-bold">—</div><div className="text-xs text-[var(--muted)]">this week</div></div>
          <div className="card p-4"><div className="text-xs text-[var(--muted)]">Top Matches</div><div className="text-2xl font-bold">{people.filter(p => p.score >= 90).length}</div><div className="text-xs text-[var(--muted)]">90%+ match</div></div>
        </section>

        <div className="mb-4 grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
          <div>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <input className="input w-full max-w-xs" placeholder="Search candidates..." />
              <div className="flex gap-2">
                <select className="input"><option>All Roles</option></select>
                <select className="input"><option>Experience</option></select>
                <select className="input"><option>Status</option></select>
              </div>
            </div>
            <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {people.map((p) => <CandidateCard key={p.id} person={p} />)}
            </section>
          </div>
          <div>
            <div className="text-sm font-semibold mb-2">Generated Questions</div>
            <QuestionsPanel />
          </div>
        </div>
      </main>

      <UploadModal open={openUpload} onClose={() => setOpenUpload(false)}>
        <ResumeUpload />
      </UploadModal>
    </div>
  );
}
