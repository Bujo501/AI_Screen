# ============================
# backend/hrmatching/scoring.py
# ============================
from __future__ import annotations
import re
from typing import Iterable, List, Tuple, Dict, Set

DEFAULT_SKILLS = {
    "python","java","javascript","typescript","react","node","fastapi","django","flask",
    "sql","postgresql","mysql","mongodb","redis","aws","gcp","azure","docker","kubernetes",
    "ci/cd","git","linux","rest","graphql","microservices","pandas","numpy","spark","hadoop",
}

WORD_SPLIT = re.compile(r"[^\w\+#]+", re.UNICODE)

def normalize(text: str) -> str:
    return text.lower().strip()

def tokenize(text: str) -> List[str]:
    return [t for t in WORD_SPLIT.split(text.lower()) if t]

def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    return 0.0 if not sa and not sb else len(sa & sb) / len(sa | sb)

def extract_years(resume_text: str | None) -> int | None:
    if not resume_text:
        return None
    m = re.search(r"(\d+)\s*\+?\s*years?", resume_text.lower())
    return int(m.group(1)) if m else None

def extract_skills(text: str | None, known_skills: Set[str] | None = None) -> List[str]:
    if not text:
        return []
    known = set(known_skills or DEFAULT_SKILLS)
    tokens = set(tokenize(text))
    hits = []
    for skill in known:
        parts = set(tokenize(skill))
        if parts.issubset(tokens) or skill in text.lower():
            hits.append(skill)
    return sorted(hits)

def score_candidate_against_role(
    candidate_skills: Set[str],
    candidate_years: int | None,
    candidate_title: str | None,
    role_title: str,
    job_skills: List[Tuple[str, int, bool]],  # (skill, weight, must_have)
    min_years: int,
    max_years: int,
) -> Tuple[int, Dict]:
    total_weight = sum(w for _, w, _ in job_skills) or 1
    matched_weight = 0
    matched_names, missing_must, missing_nice = [], [], []

    for name, weight, must in job_skills:
        if normalize(name) in candidate_skills:
            matched_weight += weight
            matched_names.append(name)
        else:
            (missing_must if must else missing_nice).append(name)

    skill_score = matched_weight / total_weight
    if missing_must:
        skill_score *= 0.6  # why: hard penalty for missing mandatory skills

    if candidate_years is None:
        exp_score = 0.5
    else:
        if candidate_years < min_years:
            exp_score = max(0.0, candidate_years / max(1, min_years))
        elif candidate_years <= max_years:
            exp_score = 1.0
        else:
            over = candidate_years - max_years
            exp_score = max(0.8, 1.0 - min(0.2, over * 0.02))

    title_score = jaccard(tokenize(candidate_title or ""), tokenize(role_title))

    final = 0.70 * skill_score + 0.25 * exp_score + 0.05 * title_score
    percent = int(round(final * 100))

    details = {
        "skill_score": round(skill_score, 3),
        "experience_score": round(exp_score, 3),
        "title_score": round(title_score, 3),
        "matched_skills": sorted(matched_names),
        "missing_must_haves": sorted(missing_must),
        "missing_nice_to_haves": sorted(missing_nice),
    }
    return percent, details
