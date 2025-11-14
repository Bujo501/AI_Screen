// filepath: src/pages/Resumes.tsx
import React, { useRef, useState } from "react";
import { uploadResume, type UploadMode, type UploadResponse } from "@/services/http";

export default function Resumes() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<UploadMode>("upload");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);

  const onPick: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    setFile(e.target.files?.[0] ?? null);
    setResult(null);
    setError(null);
  };

  const onSubmit: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    if (!file) return setError("Please choose a file");
    setBusy(true); setError(null); setResult(null);
    try {
      const data = await uploadResume(file, mode);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", padding: 16 }}>
      <h2>Upload Resume</h2>
      <form onSubmit={onSubmit}>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp"
          onChange={onPick}
          disabled={busy}
        />
        <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
          <button type="button" disabled={busy} onClick={() => setMode("upload")}>
            Upload Only
          </button>
          <button type="button" disabled={busy} onClick={() => setMode("full")}>
            Upload &amp; Parse
          </button>
          <button type="submit" disabled={busy || !file}>
            {busy ? "Working..." : mode === "upload" ? "Send to /upload" : "Send to /full-pipeline"}
          </button>
        </div>
      </form>

      {error && <p style={{ color: "crimson", marginTop: 12 }}>{error}</p>}

      {result && (
        <pre
          style={{
            marginTop: 16,
            background: "#111",
            color: "#eee",
            padding: 12,
            borderRadius: 8,
            overflowX: "auto",
          }}
        >
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
