# filepath: AI_Screen/app/core/match.py
from __future__ import annotations
import re
from typing import Iterable, Tuple, Optional

_WORD = re.compile(r"\w+", re.UNICODE)

# minimal synonym map used in candidate-vs-role matching
_SYNONYMS = {
    "reactjs": "react", "react.js": "react",
    "node": "node.js", "nodejs": "node.js", "express": "express.js",
    "ts": "typescript", "js": "javascript",
    "postgres": "postgresql", "postgre": "postgresql", "pgsql": "postgresql",
    "np": "numpy", "numy": "numpy", "deeplearing": "deep learning",
    "power bi": "powerbi", "power-bi": "powerbi",
    "github": "git", "gwthub": "git",
}

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def _syn(s: str) -> str:
    return _SYNONYMS.get(s, s)

def _tokset(s: str) -> set[str]:
    return set(_WORD.findall(_norm(s)))

def _canon_set(items: Iterable[str] | None) -> list[tuple[str, set[str]]]:
    out = []
    for it in items or []:
        cs = _syn(_norm(it))
        out.append((cs, _tokset(cs)))
    return out

def skill_score(
    candidate_skills: list[str] | None,
    must_have_skills: list[str] | None,
    nice_to_have_skills: list[str] | None,
) -> Tuple[float, int, int]:
    cand_pairs = _canon_set(candidate_skills or [])
    cand_strs = {s for s, _ in cand_pairs}

    def _has(skill: str) -> bool:
        cs = _syn(_norm(skill))
        if cs in cand_strs:
            return True
        req_tokens = _tokset(cs)
        for _, toks in cand_pairs:
            if req_tokens.issubset(toks):
                return True
        return False

    must = must_have_skills or []
    nice = nice_to_have_skills or []

    matched_must = sum(1 for s in must if _has(s))
    matched_nice = sum(1 for s in nice if _has(s))

    total_points = 2 * len(must) + 1 * len(nice)
    if total_points == 0:
        return 0.0, matched_must, matched_nice

    got_points = 2 * matched_must + matched_nice
    score = got_points / total_points
    if matched_must < len(must):
        score *= 0.8
    return score, matched_must, matched_nice

def experience_score(candidate_years: Optional[float | int], min_years: int) -> float:
    if candidate_years is None:
        return 0.5
    years = max(0.0, float(candidate_years))
    if min_years <= 0:
        return 1.0
    return min(1.0, years / float(min_years))

def education_score(candidate_edu: int, required_edu: int) -> float:
    candidate_edu = int(candidate_edu or 0)
    required_edu = int(required_edu or 0)
    if required_edu <= 0:
        return 1.0
    return min(1.0, max(0.0, candidate_edu / float(required_edu)))

def keywords_score(resume_text: str, source_text: str) -> float:
    a, b = _tokset(resume_text or ""), _tokset(source_text or "")
    if not a and not b:
        return 0.0
    return len(a & b) / float(len(a | b))

def overall_score(weights: dict | None, s_score: float, e_score: float, d_score: float, k_score: float) -> float:
    w = dict(weights or {})
    skills_w = float(w.get("skills", 0.70))
    exp_w    = float(w.get("experience", 0.25))
    edu_w    = float(w.get("education", 0.03))
    kw_w     = float(w.get("keywords", 0.02))
    total = skills_w + exp_w + edu_w + kw_w
    if total <= 0:
        skills_w, exp_w, edu_w, kw_w = 0.70, 0.25, 0.03, 0.02
        total = 1.0
    skills_w, exp_w, edu_w, kw_w = (skills_w/total, exp_w/total, edu_w/total, kw_w/total)
    final = (skills_w * s_score) + (exp_w * e_score) + (edu_w * d_score) + (kw_w * k_score)
    return round(final * 100.0, 1)
