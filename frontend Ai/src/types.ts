
// ===========================================
// filepath: src/types.ts
// ===========================================
export enum EducationLevel {
  none = 0,
  highschool = 1,
  associate = 2,
  bachelor = 3,
  master = 4,
  phd = 5,
}

export type ParsedResume = {
  name?: string;
  email?: string;
  phone?: string;
  skills: string[];
  years_experience: number;
  education: number; // use EducationLevel ordinal
  raw_text: string;
};

export type ResumeRecord = ParsedResume & {
  id: string;
  created_at: string;
  updated_at: string;
};

export type JobRequirements = {
  id?: string;
  title: string;
  must_have_skills: string[];
  nice_to_have_skills: string[];
  min_years_experience: number;
  required_education: number; // EducationLevel
  description: string;
};
