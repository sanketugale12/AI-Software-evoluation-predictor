import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..database import get_db
from ..models.analysis_job import AnalysisJob

router = APIRouter()

def calculate_debt_delta(job1_results: Dict[str, Any], job2_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate the difference in technical debt between two analysis jobs."""
    debt1 = job1_results.get("technical_debt", {}).get("debt_score", 0)
    debt2 = job2_results.get("technical_debt", {}).get("debt_score", 0)

    sec1 = len(job1_results.get("security", {}).get("findings", [])) if isinstance(job1_results.get("security"), dict) else 0
    sec2 = len(job2_results.get("security", {}).get("findings", [])) if isinstance(job2_results, dict) else 0

    return {
        "debt_delta": round(debt2 - debt1, 2),
        "security_delta": sec2 - sec1,
        "trend": "increasing" if debt2 > debt1 else "decreasing" if debt2 < debt1 else "stable"
    }

@router.get("/compare")
async def compare_analysis_jobs(
    id1: str,
    id2: str,
    db: Session = Depends(get_db)
):
    """Compare two analysis jobs to see how the repository has evolved."""
    job1 = db.query(AnalysisJob).filter(AnalysisJob.id == id1).first()
    job2 = db.query(AnalysisJob).filter(AnalysisJob.id == id2).first()

    if not job1 or not job2:
        raise HTTPException(status_code=404, detail="One or both analysis jobs not found")

    # Results are stored as JSON in the DB
    res1 = job1.result if isinstance(job1.result, dict) else {}
    res2 = job2.result if isinstance(job2.result, dict) else {}

    delta = calculate_debt_delta(res1, res2)

    return {
        "job_1": {"id": id1, "commit": job1.commit_sha},
        "job_2": {"id": id2, "commit": job2.commit_sha},
        "comparison": delta
    }
