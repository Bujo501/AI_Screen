# filepath: AI_Screen/app/api/jobs.py
from fastapi import APIRouter, HTTPException
from typing import List, Any
from pathlib import Path
import json
import uuid
import re

from ..schemas.match import JobRequirements

# NOTE: prefix is ONLY '/jobs' (versioning is added in main.py)
router = APIRouter(prefix="/jobs", tags=["jobs"])

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
JOBS_FILE = DATA_DIR / "jobs.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
if not JOBS_FILE.exists():
    JOBS_FILE.write_text("[]", encoding="utf-8")

# --------- normalization helpers ----------
_WORD = re.compile(r"\w+", re.UNICODE)

_SYNONYMS = {
    # frameworks / runtimes
    "reactjs": "react", "react.js": "react",
    "node": "node.js", "nodejs": "node.js", "express": "express.js",
    "ts": "typescript", "js": "javascript",
    # data/analytics
    "np": "numpy", "numy": "numpy", "numy.machine learing": "numpy",
    "pandas ": "pandas", "deeplearing": "deep learning",
    "power bi": "powerbi", "power-bi": "powerbi",
    "powerbi.matlab": "powerbi",  # bad source formatting
    # dbs
    "postgres": "postgresql", "postgre": "postgresql", "pgsql": "postgresql",
    # clouds / misc
    "aws cloud": "aws", "github": "git", "gwthub": "git",
}

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def _canon(skill: str) -> str:
    s = _norm(skill)
    # keep .js for libs; otherwise collapse punctuation to spaces
    s = _SYNONYMS.get(s, s)
    return s

def _explode_mixed(value: Any) -> List[str]:
    """
    Accepts list/str; splits on comma, newline, semicolon, and 'and'.
    Also splits 'React.js, Node.js, Express.js, Bootstrap, Redux' correctly.
    """
    if value is None:
        return []
    base: List[str] = []
    if isinstance(value, list):
        for it in value:
            base.append(str(it))
    else:
        base.append(str(value))

    out: List[str] = []
    for raw in base:
        # Fix common bad inputs like "JavaScript, SQL" in one token
        parts = re.split(r"(?:\s*\band\b\s*)|[,;\n]+", raw, flags=re.I)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            # break obvious dotted concatenations but keep *.js
            if (".") in p and not p.endswith(".js"):
                sub = [q for q in re.split(r"[.]", p) if q.strip()]
                if len(sub) > 1:
                    out.extend(sub)
                    continue
            out.append(p)
    # canonicalize + dedupe while keeping order
    seen, cleaned = set(), []
    for item in out:
        c = _canon(item)
        if not c:
            continue
        if c not in seen:
            seen.add(c)
            cleaned.append(c)
    return cleaned

def _clean_payload(j: dict) -> dict:
    """Normalize a JobRequirements-like dict in-place."""
    j = dict(j or {})
    j["title"] = (j.get("title") or "").strip()
    j["description"] = (j.get("description") or "").strip()
    j["min_years_experience"] = float(j.get("min_years_experience") or 0)
    j["required_education"] = int(j.get("required_education") or 0)

    j["must_have_skills"] = _explode_mixed(j.get("must_have_skills"))
    j["nice_to_have_skills"] = _explode_mixed(j.get("nice_to_have_skills"))
    return j

# --------- file io ----------
def _load() -> List[dict]:
    try:
        data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
        # ensure every row is normalized on read (repairs old rows)
        return [_clean_payload(x) for x in (data if isinstance(data, list) else [])]
    except Exception:
        return []

def _save(items: List[dict]) -> None:
    JOBS_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

# --------- endpoints ----------
@router.get("", response_model=List[JobRequirements])
def list_jobs():
    return _load()

@router.get("/{job_id}", response_model=JobRequirements)
def get_job(job_id: str):
    for item in _load():
        if item.get("id") == job_id:
            return item
    raise HTTPException(404, "Job not found")

@router.post("", response_model=JobRequirements)
def create_job(job: JobRequirements):
    data = _load()
    j = _clean_payload(job.dict())
    j["id"] = j.get("id") or str(uuid.uuid4())
    data.append(j)
    _save(data)
    return j

@router.put("/{job_id}", response_model=JobRequirements)
def update_job(job_id: str, job: JobRequirements):
    data = _load()
    for i, item in enumerate(data):
        if item.get("id") == job_id:
            new_item = _clean_payload(job.dict())
            new_item["id"] = job_id
            data[i] = new_item
            _save(data)
            return new_item
    raise HTTPException(404, "Job not found")

@router.delete("/{job_id}")
def delete_job(job_id: str):
    data = _load()
    new_data = [x for x in data if x.get("id") != job_id]
    if len(new_data) == len(data):
        raise HTTPException(404, "Job not found")
    _save(new_data)
    return {"ok": True}
# filepath: AI_Screen/app/api/jobs.py
@router.get("/", response_model=List[JobRequirements])
def list_jobs_slash():
    # mirror of list_jobs() to handle trailing slash
    return _load()
"""
Job description API routes
"""
from fastapi import APIRouter, HTTPException
from app.services.job_service import JobService
from app.schemas.resume import JobDescriptionCreate
from typing import Dict, Any

router = APIRouter(tags=["Jobs"])
job_service = JobService()


@router.post("/add", response_model=Dict[str, Any])
async def add_job_description(request: JobDescriptionCreate):
    """
    Add a new job description to the database.
    """
    return job_service.add_job_description(request.title, request.description)


@router.get("/all", response_model=Dict[str, Any])
async def get_all_jobs():
    """
    Fetch all job descriptions stored in the database.
    """
    return job_service.get_all_jobs()


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_by_id(job_id: str):
    """
    Fetch a specific job by its ID.
    """
    return job_service.get_job_by_id(job_id)


@router.delete("/{job_id}", response_model=Dict[str, Any])
async def delete_job(job_id: str):
    """
    Delete a job by its ID.
    """
    return job_service.delete_job(job_id)
