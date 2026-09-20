from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from backend.app.database import SessionLocal
from backend.app.models.analysis_job import AnalysisJob
from backend.app.schemas.analysis import (
    AnalysisJobCreate,
    AnalysisJobResponse,
    AnalysisResultsResponse,
    AnalysisJobListResponse,
    CancelAnalysisRequest,
    RetryAnalysisRequest,
    AnalysisJobRequest,
)
from backend.app.tasks.analysis_task import run_analysis, cancel_analysis
from backend.app.services.auth_service import AuthService
from backend.app.services.repository_service import get_repository_context

router = APIRouter(tags=["Analysis"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_id(
    x_user_id: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None),
) -> str:
    """Extract user ID from header or query param."""
    uid = x_user_id or user_id
    if uid == "test_user":
        return uid
    if not uid:
        raise HTTPException(status_code=401, detail="User ID required")
    return uid


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


# Legacy endpoint (backward compatibility)
@router.post("/legacy")
def create_analysis_legacy(
    repository_url: str,
    db: Session = Depends(get_db),
):
    job = AnalysisJob(repository_url=repository_url)

    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch background analysis task
    run_analysis.delay(
        job.id,
        job.repository_url,
    )

    return {
        "job_id": job.id,
        "status": job.status,
    }


# New authenticated endpoint
@router.post("/repositories/{owner}/{repo}/analyze", response_model=AnalysisJobResponse)
async def create_analysis(
    owner: str,
    repo: str,
    request: AnalysisJobRequest,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Start a new analysis for a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        request: Optional commit_sha to pin analysis to a specific commit
    """
    access_token = auth_service.get_valid_access_token(user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Get repository context
    repo_obj = await get_repository_context(db, user_id, owner, repo)
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Create analysis job
    job = AnalysisJob(
        repository_url=f"https://github.com/{owner}/{repo}",
        repository_id=str(repo_obj.id),
        commit_sha=request.commit_sha,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch background analysis task
    run_analysis.delay(
        job.id,
        job.repository_url,
        job.commit_sha,
    )

    return AnalysisJobResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        commit_sha=job.commit_sha
    )


@router.get("/{job_id}", response_model=AnalysisJobResponse)
def get_analysis_job_status(job_id: str, db: Session = Depends(get_db)):
    db_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    return AnalysisJobResponse(
        job_id=db_job.id,
        status=db_job.status,
        created_at=db_job.created_at,
        progress=db_job.progress,
        started_at=db_job.started_at,
        completed_at=db_job.completed_at,
        version=db_job.version,
        retry_count=db_job.retry_count,
        cancelled=db_job.cancelled,
        commit_sha=db_job.commit_sha
    )


@router.get("/{job_id}/results", response_model=AnalysisResultsResponse)
def get_analysis_results(job_id: str, db: Session = Depends(get_db)):
    db_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    return AnalysisResultsResponse(
        job_id=db_job.id,
        status=db_job.status,
        results=getattr(db_job, "result", None),
        error_message=getattr(db_job, "error_message", None)
    )


@router.post("/{job_id}/cancel")
def cancel_analysis_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel a running analysis job."""
    db_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    if db_job.status not in ["queued", "running"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job in status: {db_job.status}")

    # Mark as cancelled
    db_job.cancelled = True
    db.commit()

    # Also send cancel task to Celery
    cancel_analysis.delay(job_id)

    return {"job_id": job_id, "status": "cancelling"}


@router.post("/{job_id}/retry", response_model=AnalysisJobResponse)
def retry_analysis_job(job_id: str, db: Session = Depends(get_db)):
    """Retry a failed analysis job."""
    db_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    if db_job.status not in ["failed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Can only retry failed or cancelled jobs, current status: {db_job.status}")

    # Reset job for retry
    db_job.status = "queued"
    db_job.retry_count += 1
    db_job.error_message = None
    db_job.cancelled = False
    db_job.progress = None
    db_job.started_at = None
    db_job.completed_at = None
    db.commit()
    db.refresh(db_job)

    # Dispatch background analysis task (use original commit_sha if any)
    run_analysis.delay(
        db_job.id,
        db_job.repository_url,
        db_job.commit_sha,
    )

    return AnalysisJobResponse(
        job_id=db_job.id,
        status=db_job.status,
        created_at=db_job.created_at,
        commit_sha=db_job.commit_sha
    )


@router.get("/repositories/{owner}/{repo}/jobs", response_model=AnalysisJobListResponse)
async def list_analysis_jobs(
    owner: str,
    repo: str,
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """List analysis jobs for a repository."""
    access_token = auth_service.get_valid_access_token(user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Get repository context
    repo_obj = await get_repository_context(db, user_id, owner, repo)
    if not repo_obj:
        raise HTTPException(status_code=404, detail="Repository not found")

    jobs = db.query(AnalysisJob).filter(
        AnalysisJob.repository_id == str(repo_obj.id)
    ).order_by(AnalysisJob.created_at.desc()).limit(limit).all()

    return AnalysisJobListResponse(
        jobs=[
            AnalysisJobResponse(
                job_id=j.id,
                status=j.status,
                created_at=j.created_at,
                progress=j.progress,
                started_at=j.started_at,
                completed_at=j.completed_at,
                version=j.version,
                retry_count=j.retry_count,
                cancelled=j.cancelled,
                commit_sha=j.commit_sha
            )
            for j in jobs
        ]
    )