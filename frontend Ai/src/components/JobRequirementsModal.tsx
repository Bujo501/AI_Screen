// ---------- File: src/components/JobRequirementsModal.tsx
import React, { useEffect, useState } from "react";
import { EducationLevel, JobRequirements } from "@/types";
import { JobsAPI } from "@/services/http";

type Props = {
  open: boolean;
  onClose: () => void;
  onSaved: (job: JobRequirements) => void;
  initial?: JobRequirements | null;
};

const emptyJob: JobRequirements = {
  title: "",
  must_have_skills: [],
  nice_to_have_skills: [],
  min_years_experience: 0,
  required_education: EducationLevel.none,
  description: "",
};

export default function JobRequirementsModal({ open, onClose, onSaved, initial }: Props) {
  const [job, setJob] = useState<JobRequirements>(initial ?? emptyJob);
  const [skillInput, setSkillInput] = useState("");
  const [niceInput, setNiceInput] = useState("");
  const [saving, setSaving] = useState(false);
  const isEdit = Boolean(initial?.id);

  useEffect(() => {
    setJob(initial ?? emptyJob);
  }, [initial]);

  if (!open) return null;

  const addTo = (key: "must_have_skills" | "nice_to_have_skills") => {
    const value = key === "must_have_skills" ? skillInput.trim() : niceInput.trim();
    if (!value) return;
    setJob({ ...job, [key]: [...job[key], value] });
    key === "must_have_skills" ? setSkillInput("") : setNiceInput("");
  };

  const removeAt = (key: "must_have_skills" | "nice_to_have_skills", idx: number) => {
    const arr = [...job[key]];
    arr.splice(idx, 1);
    setJob({ ...job, [key]: arr });
  };

  const save = async () => {
    setSaving(true);
    try {
      const payload = { ...job };
      const saved = isEdit
        ? await JobsAPI.update(initial!.id!, payload)
        : await JobsAPI.create(payload);
      onSaved(saved);
      onClose();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">{isEdit ? "Edit Job Requirements" : "New Job Requirements"}</h2>
          <button onClick={onClose} className="px-3 py-1 rounded-lg border">Close</button>
        </div>

        <div className="grid gap-4">
          <label className="grid gap-1">
            <span className="text-sm font-medium">Job Title</span>
            <input className="input" value={job.title} onChange={e => setJob({ ...job, title: e.target.value })} />
          </label>

          <div className="grid gap-2">
            <span className="text-sm font-medium">Must-have Skills</span>
            <div className="flex gap-2">
              <input className="input flex-1" placeholder="e.g. React" value={skillInput}
                     onChange={e => setSkillInput(e.target.value)} />
              <button className="btn" onClick={() => addTo("must_have_skills")}>Add</button>
            </div>
            <div className="flex flex-wrap gap-2">
              {job.must_have_skills.map((s, i) => (
                <span key={`${s}-${i}`} className="tag">{s}
                  <button className="ml-2 text-xs" onClick={() => removeAt("must_have_skills", i)}>✕</button>
                </span>
              ))}
            </div>
          </div>

          <div className="grid gap-2">
            <span className="text-sm font-medium">Nice-to-have Skills</span>
            <div className="flex gap-2">
              <input className="input flex-1" placeholder="e.g. GraphQL" value={niceInput}
                     onChange={e => setNiceInput(e.target.value)} />
              <button className="btn" onClick={() => addTo("nice_to_have_skills")}>Add</button>
            </div>
            <div className="flex flex-wrap gap-2">
              {job.nice_to_have_skills.map((s, i) => (
                <span key={`${s}-${i}`} className="tag">{s}
                  <button className="ml-2 text-xs" onClick={() => removeAt("nice_to_have_skills", i)}>✕</button>
                </span>
              ))}
            </div>
          </div>

          <label className="grid gap-1">
            <span className="text-sm font-medium">Minimum Years Experience</span>
            <input type="number" min={0} step={0.5} className="input"
                   value={job.min_years_experience}
                   onChange={e => setJob({ ...job, min_years_experience: Number(e.target.value) })} />
          </label>

          <label className="grid gap-1">
            <span className="text-sm font-medium">Required Education</span>
            <select className="input"
                    value={job.required_education}
                    onChange={e => setJob({ ...job, required_education: Number(e.target.value) as any })}>
              {Object.entries(EducationLevel).filter(([k]) => isNaN(Number(k))).map(([k, v]) => (
                <option key={k} value={v as any}>{k}</option>
              ))}
            </select>
          </label>

          <label className="grid gap-1">
            <span className="text-sm font-medium">Description / Requirements Text</span>
            <textarea className="input min-h-[100px]" value={job.description}
                      onChange={e => setJob({ ...job, description: e.target.value })} />
          </label>
        </div>

        <div className="flex justify-end gap-2 mt-5">
          <button className="px-4 py-2 rounded-lg border" onClick={onClose}>Cancel</button>
          <button className="btn" onClick={save} disabled={saving}>
            {saving ? "Saving..." : isEdit ? "Save" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}
