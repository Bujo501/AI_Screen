# =========================================
# filepath: AI_Screen/app/api/hr.py
# =========================================
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import uuid4

from app.core.database import get_connection

router = APIRouter(prefix="/hr", tags=["hr"])

# ---------- DDL helpers (runs lazily on first use) ----------
DDL_ROLE = """
CREATE TABLE IF NOT EXISTS hr_role (
  id VARCHAR(36) PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  min_years_experience INT NOT NULL DEFAULT 0,
  required_education INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

DDL_SKILL = """
CREATE TABLE IF NOT EXISTS hr_skill (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

DDL_ROLE_SKILL = """
CREATE TABLE IF NOT EXISTS hr_role_skill (
  id INT AUTO_INCREMENT PRIMARY KEY,
  role_id VARCHAR(36) NOT NULL,
  skill_id INT NOT NULL,
  weight TINYINT NOT NULL DEFAULT 3,
  must_have BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT fk_rs_role FOREIGN KEY (role_id) REFERENCES hr_role(id) ON DELETE CASCADE,
  CONSTRAINT fk_rs_skill FOREIGN KEY (skill_id) REFERENCES hr_skill(id) ON DELETE CASCADE,
  INDEX idx_rs_role (role_id),
  INDEX idx_rs_skill (skill_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

def _ensure_schema() -> None:
    conn = get_connection()
    if conn is None:
        raise HTTPException(500, "DB connection failed")
    cur = conn.cursor()
    cur.execute(DDL_ROLE)
    cur.execute(DDL_SKILL)
    cur.execute(DDL_ROLE_SKILL)
    conn.commit()
    cur.close()
    conn.close()

def _get_or_create_skill_id(cur, name: str) -> int:
    cur.execute("SELECT id FROM hr_skill WHERE name=%s", (name,))
    row = cur.fetchone()
    if row: return int(row[0])
    cur.execute("INSERT INTO hr_skill(name) VALUES (%s)", (name,))
    return int(cur.lastrowid)

def _role_to_dict(role_row: Dict[str, Any], skills_rows: List[tuple]) -> Dict[str, Any]:
    must: List[str] = []
    nice: List[str] = []
    for name, must_have in skills_rows:
        (must if must_have else nice).append(name)
    return {
        "id": role_row["id"],
        "title": role_row["title"],
        "description": role_row.get("description") or "",
        "min_years_experience": int(role_row.get("min_years_experience") or 0),
        "required_education": int(role_row.get("required_education") or 0),
        "must_have_skills": must,
        "nice_to_have_skills": nice,
    }

# ---------- Schemas ----------
class RoleIn(BaseModel):
    title: str
    description: Optional[str] = ""
    min_years_experience: int = 0
    required_education: int = 0
    must_have_skills: List[str] = []
    nice_to_have_skills: List[str] = []

class RoleOut(RoleIn):
    id: str

# ---------- Endpoints ----------
@router.get("/roles", response_model=List[RoleOut])
def list_roles():
    _ensure_schema()
    conn = get_connection()
    if conn is None:
        raise HTTPException(500, "DB connection failed")

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title, description, min_years_experience, required_education FROM hr_role ORDER BY updated_at DESC")
    roles = cur.fetchall()
    out: List[Dict[str, Any]] = []

    for r in roles:
        cur2 = conn.cursor()
        cur2.execute(
            """SELECT s.name, rs.must_have
               FROM hr_role_skill rs
               JOIN hr_skill s ON s.id = rs.skill_id
               WHERE rs.role_id=%s
               ORDER BY s.name""",
            (r["id"],),
        )
        rows = cur2.fetchall()
        cur2.close()
        out.append(_role_to_dict(r, rows))

    cur.close()
    conn.close()
    return out

@router.get("/roles/{role_id}", response_model=RoleOut)
def get_role(role_id: str):
    _ensure_schema()
    conn = get_connection()
    if conn is None:
        raise HTTPException(500, "DB connection failed")

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title, description, min_years_experience, required_education FROM hr_role WHERE id=%s", (role_id,))
    r = cur.fetchone()
    if not r:
        cur.close(); conn.close()
        raise HTTPException(404, "Role not found")

    cur2 = conn.cursor()
    cur2.execute(
        """SELECT s.name, rs.must_have
           FROM hr_role_skill rs
           JOIN hr_skill s ON s.id = rs.skill_id
           WHERE rs.role_id=%s
           ORDER BY s.name""",
        (role_id,),
    )
    rows = cur2.fetchall()
    cur2.close(); cur.close(); conn.close()
    return _role_to_dict(r, rows)

@router.post("/roles", response_model=RoleOut)
def create_role(payload: RoleIn):
    _ensure_schema()
    conn = get_connection()
    if conn is None:
        raise HTTPException(500, "DB connection failed")

    rid = str(uuid4())
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO hr_role
           (id, title, description, min_years_experience, required_education)
           VALUES (%s, %s, %s, %s, %s)""",
        (
            rid,
            payload.title.strip(),
            (payload.description or "").strip(),
            int(payload.min_years_experience or 0),
            int(payload.required_education or 0),
        ),
    )

    # skills
    for name in (payload.must_have_skills or []):
        sid = _get_or_create_skill_id(cur, name.strip())
        cur.execute(
            "INSERT INTO hr_role_skill(role_id, skill_id, weight, must_have) VALUES (%s, %s, %s, %s)",
            (rid, sid, 3, True),
        )
    for name in (payload.nice_to_have_skills or []):
        sid = _get_or_create_skill_id(cur, name.strip())
        cur.execute(
            "INSERT INTO hr_role_skill(role_id, skill_id, weight, must_have) VALUES (%s, %s, %s, %s)",
            (rid, sid, 2, False),
        )

    conn.commit()
    cur.close(); conn.close()

    return RoleOut(
        id=rid,
        title=payload.title,
        description=payload.description or "",
        min_years_experience=int(payload.min_years_experience or 0),
        required_education=int(payload.required_education or 0),
        must_have_skills=list(payload.must_have_skills or []),
        nice_to_have_skills=list(payload.nice_to_have_skills or []),
    )
