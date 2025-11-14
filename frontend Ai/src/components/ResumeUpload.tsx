// ============================================================================
// filepath: src/components/ResumeUpload.tsx  (replace file)
// ============================================================================
import React, { useState } from "react";
import { uploadResumeXHR, extractParsedFromPipeline, ResumesAPI } from "@/services/http";

export default function ResumeUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [pct, setPct] = useState(0);
  const [mode, setMode] = useState<"upload" | "full">("full");
  const [busy, setBusy] = useState(false);

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => setFile(e.target.files?.[0] || null);

  const start = async () => {
    if (!file) return;
    setBusy(true); setPct(0);
    try {
      const resp = await uploadResumeXHR(file, mode, setPct);

      // If we used the full pipeline, save a normalized record to DB and publish questions.
      if (mode === "full") {
        const parsed = extractParsedFromPipeline(resp);
        try { await ResumesAPI.create(parsed); } catch (e) { console.warn("DB save failed:", e); }
        const questions = resp?.pipeline_results?.interview_questions || null;
        if (questions) window.dispatchEvent(new CustomEvent("questions:update", { detail: questions }));
      }

      // Update the grid
      window.dispatchEvent(new CustomEvent("resumes:changed"));
      alert("Uploaded successfully");
    } catch (e: any) {
      alert(e.message || "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-4">
      <div className="mb-2"><input type="file" onChange={onFile} /></div>
      <div className="mb-3 flex items-center gap-6">
        <label className="flex items-center gap-2">
          <input type="radio" checked={mode === "full"} onChange={() => setMode("full")} />
          <span>Upload & Parse</span>
        </label>
        <label className="flex items-center gap-2">
          <input type="radio" checked={mode === "upload"} onChange={() => setMode("upload")} />
          <span>Upload Only</span>
        </label>
      </div>
      <button className="btn" disabled={!file || busy} onClick={start}>Start Upload</button>
      {busy && (
        <div className="mt-3 w-full bg-slate-200 rounded h-2 overflow-hidden">
          <div className="h-2 rounded" style={{ width: `${pct}%` }} />
        </div>
      )}
    </div>
  );
}
