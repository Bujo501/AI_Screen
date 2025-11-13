"""
Business logic for managing job descriptions.
"""

import json
from uuid import uuid4
from fastapi import HTTPException
from typing import Dict, Any
from app.core.database import get_connection


class JobService:
    """Handles database operations for job descriptions."""

    def add_job_description(self, title: str, description: str) -> Dict[str, Any]:
        """
        Add a new job description to the database.
        """
        try:
            job_id = str(uuid4())
            conn = get_connection()
            if conn is None:
                raise HTTPException(status_code=500, detail="Database connection failed")

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO job_descriptions (job_id, title, company_branch, description, required_skills)
                VALUES (%s, %s, %s,%s, %s)
            """, (job_id, title, description))
            conn.commit()
            cursor.close()
            conn.close()

            return {
                "status": "success",
                "job_id": job_id,
                "message": "Job description added successfully"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving job description: {str(e)}")

    def get_all_jobs(self) -> Dict[str, Any]:
        """
        Retrieve all job descriptions from the database.
        """
        try:
            conn = get_connection()
            if conn is None:
                raise HTTPException(status_code=500, detail="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT job_id, title, description, created_at
                FROM job_descriptions
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            return {
                "status": "success",
                "total_jobs": len(rows),
                "jobs": rows
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

    def get_job_by_id(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific job by ID.
        """
        try:
            conn = get_connection()
            if conn is None:
                raise HTTPException(status_code=500, detail="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT job_id, title, description, created_at FROM job_descriptions WHERE job_id = %s", (job_id,))
            job = cursor.fetchone()
            cursor.close()
            conn.close()

            if not job:
                raise HTTPException(status_code=404, detail="Job description not found")

            return {"status": "success", "job": job}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving job: {str(e)}")

    def delete_job(self, job_id: str) -> Dict[str, Any]:
        """
        Delete a job description by ID.
        """
        try:
            conn = get_connection()
            if conn is None:
                raise HTTPException(status_code=500, detail="Database connection failed")

            cursor = conn.cursor()
            cursor.execute("DELETE FROM job_descriptions WHERE job_id = %s", (job_id,))
            conn.commit()
            cursor.close()
            conn.close()

            return {
                "status": "success",
                "message": f"Job with ID {job_id} deleted successfully"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")
