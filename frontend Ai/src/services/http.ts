// ============================================================================
// filepath: src/services/http.ts  (replace file)
// ============================================================================
export const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

export type UploadMode = "upload" | "full";
export type UploadResponse = Record<string, unknown>;

function json<T>(res: Response): Promise<T> {
  if (!res.ok) return res.text().then((t) => { throw new Error(`HTTP ${res.status} ${res.statusText}: ${t || "<empty>"}`); });
  return res.json();
}

// --- Upload helpers (no JSX here)
export async function uploadResume(file: File, mode: UploadMode): Promise<UploadResponse> {
  const form = new FormData(); form.append("file", file);
  const path = mode === "upload" ? "/api/v1/resume/upload" : "/api/v1/resume/full-pipeline";
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const j = await res.json(); msg = (j as any)?.detail || JSON.stringify(j); } catch { try { msg = await res.text(); } catch {} }
    throw new Error(msg);
  }
  return res.json();
}

export function uploadResumeXHR(file: File, mode: UploadMode, onProgress: (pct: number) => void): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const form = new FormData(); form.append("file", file);
    const path = mode === "upload" ? "/api/v1/resume/upload" : "/api/v1/resume/full-pipeline";
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}${path}`, true);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100)); };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText || "{}")); } catch { resolve({ message: "Uploaded", raw: xhr.responseText }); }
      } else reject(new Error(xhr.responseText || `HTTP ${xhr.status}`));
    };
    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send(form);
  });
}

// --- Types shared by UI
export enum EducationLevel { none=0, highschool=1, associate=2, bachelor=3, master=4, phd=5 }

export type ParsedResume = {
  name?: string; email?: string; phone?: string;
  skills: string[]; years_experience: number; education: number; raw_text: string;
};
export type ResumeRecord = ParsedResume & { id: string; created_at: string; updated_at: string; };

export type JobRequirements = {
  id?: string; title: string; must_have_skills: string[]; nice_to_have_skills: string[];
  min_years_experience: number; required_education: number; description: string;
};

// --- Jobs / Match / Resumes APIs
export const JobsAPI = {
  list: <T = any[]>() => fetch(`${API_BASE}/api/v1/jobs/`).then(json<T>),
};

export const MatchAPI = {
  scoreBatch: <T = any>(payload: any) =>
    fetch(`${API_BASE}/api/v1/match/score/batch`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    }).then(json<T>),
};

export const ResumesAPI = {
  list: async <T = ResumeRecord[]>() => {
    const r = await fetch(`${API_BASE}/api/v1/resume/resumes`);
    if (r.status === 404) {
      const r2 = await fetch(`${API_BASE}/api/v1/resume/resumes/`);
      if (!r2.ok) throw new Error(await r2.text());
      return r2.json() as Promise<T>;
    }
    if (!r.ok) throw new Error(await r.text());
    return r.json() as Promise<T>;
  },
  create: async <T = ResumeRecord>(resume: ParsedResume) => {
    const body = JSON.stringify(resume);
    const r = await fetch(`${API_BASE}/api/v1/resume/resumes`, { method: "POST", headers: { "Content-Type": "application/json" }, body });
    if (r.status === 404) {
      const r2 = await fetch(`${API_BASE}/api/v1/resume/resumes/`, { method: "POST", headers: { "Content-Type": "application/json" }, body });
      if (!r2.ok) throw new Error(await r2.text());
      return r2.json() as Promise<T>;
    }
    if (!r.ok) throw new Error(await r.text());
    return r.json() as Promise<T>;
  },
};

// --- Parse server payload (handles both /upload and /full-pipeline)
export function extractParsedFromPipeline(payload: any): ParsedResume {
  // shape A: { pipeline_results: { extracted_data, interview_questions, ... }, filename, ... }
  const pr = payload?.pipeline_results;
  const ex = pr?.extracted_data || payload?.extracted_data || {};
  const name = ex.full_name || payload?.name || "";
  const email = ex.email_id || payload?.email || "";
  const skills: string[] = Array.isArray(ex.skills) ? ex.skills : (ex.skills ? tryParseList(ex.skills) : []);
  const years = Number(ex.years_experience ?? payload?.years_experience ?? 0);
  const education = toEduOrdinal(ex.education ?? payload?.education);
  const raw_text = (pr?.resume_text || payload?.raw_text || "").toString();
  return { name, email, phone: "", skills, years_experience: years, education, raw_text };
}

function tryParseList(x: any): string[] {
  if (!x) return [];
  if (Array.isArray(x)) return x.map(String).filter(Boolean);
  if (typeof x === "string") {
    try { const j = JSON.parse(x); if (Array.isArray(j)) return j.map(String).filter(Boolean); } catch {}
    return x.split(",").map(s => s.trim()).filter(Boolean);
  }
  return [];
}

function toEduOrdinal(x: any): number {
  if (typeof x === "number") return x;
  const s = Array.isArray(x) && x.length ? String(x[0]) : String(x || "").toLowerCase();
  if (s.includes("phd") || s.includes("doctor")) return EducationLevel.phd;
  if (s.includes("master") || s.includes("m.sc") || s.includes("ms")) return EducationLevel.master;
  if (s.includes("bachelor") || s.includes("b.e") || s.includes("btech") || s.includes("b.sc")) return EducationLevel.bachelor;
  if (s.includes("associate")) return EducationLevel.associate;
  if (s.includes("high")) return EducationLevel.highschool;
  return EducationLevel.none;
}
