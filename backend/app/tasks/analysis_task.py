from backend.app.celery_app import celery_app
from backend.app.services.analysis_pipeline import analyze_repository
from backend.app.database import SessionLocal
from backend.app.models.analysis_job import AnalysisJob
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def update_job_progress(job_id: str, progress: dict):
    """Update job progress in database"""
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.progress = progress
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update progress for job {job_id}: {e}")
    finally:
        db.close()


def check_job_cancelled(job_id: str) -> bool:
    """Check if job has been cancelled"""
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        return job.cancelled if job else False
    finally:
        db.close()


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status and other fields"""
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update status for job {job_id}: {e}")
    finally:
        db.close()


def get_job_repository_info(job_id: str) -> dict:
    """Get repository URL and commit SHA for a job"""
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            return {
                "repository_url": job.repository_url,
                "commit_sha": getattr(job, "commit_sha", None),
            }
        return {"repository_url": None, "commit_sha": None}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_analysis(self, job_id: str, repository_url: str, commit_sha: str = None):
    """
    Run the full analysis pipeline for a repository.
    Supports retries, cancellation, and progress tracking.

    Args:
        job_id: Analysis job ID
        repository_url: Repository URL
        commit_sha: Optional commit SHA to pin analysis to (Phase 6)
    """
    logger.info(f"Starting analysis: {job_id} for {repository_url} at commit {commit_sha[:8] if commit_sha else 'default'}")

    # Update status to running
    update_job_status(job_id, "running", started_at=datetime.now(timezone.utc))
    update_job_progress(job_id, {
        "current_step": "initializing",
        "total_steps": 6,
        "step_number": 0,
        "message": "Initializing analysis..."
    })

    try:
        # Check for cancellation
        if check_job_cancelled(job_id):
            update_job_status(job_id, "cancelled", completed_at=datetime.now(timezone.utc))
            return {"job_id": job_id, "status": "cancelled"}

        # Step 1: Cloning repository
        update_job_progress(job_id, {
            "current_step": "cloning",
            "total_steps": 6,
            "step_number": 1,
            "message": "Cloning repository..."
        })

        # Check for cancellation
        if check_job_cancelled(job_id):
            update_job_status(job_id, "cancelled", completed_at=datetime.now(timezone.utc))
            return {"job_id": job_id, "status": "cancelled"}

        # Run the analysis pipeline with progress updates
        result = analyze_repository(
            repository_url,
            job_id=job_id,
            progress_callback=lambda step, msg: update_job_progress(job_id, {
                "current_step": step,
                "total_steps": 6,
                "step_number": {"cloning": 1, "complexity": 2, "git_history": 3,
                               "security": 4, "hotspots": 5, "technical_debt": 6}.get(step, 0),
                "message": msg
            }),
            cancellation_check=lambda: check_job_cancelled(job_id),
            commit_sha=commit_sha,
        )

        # Check for cancellation after analysis
        if check_job_cancelled(job_id):
            update_job_status(job_id, "cancelled", completed_at=datetime.now(timezone.utc))
            return {"job_id": job_id, "status": "cancelled"}

        # Success
        update_job_status(
            job_id,
            "completed",
            completed_at=datetime.now(timezone.utc),
            result=result
        )
        update_job_progress(job_id, {
            "current_step": "completed",
            "total_steps": 6,
            "step_number": 6,
            "message": "Analysis completed successfully"
        })

        logger.info(f"Analysis completed: {job_id}")
        return {
            "job_id": job_id,
            "status": "completed",
            "results": result,
        }

    except Exception as e:
        logger.error(f"Analysis failed for {job_id}: {str(e)}", exc_info=True)

        # Check if we should retry
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying analysis {job_id} (attempt {self.request.retries + 1}/{self.max_retries})")
            update_job_status(job_id, "queued", retry_count=self.request.retries + 1)
            raise self.retry(exc=e)

        # Max retries exceeded - mark as failed
        update_job_status(
            job_id,
            "failed",
            completed_at=datetime.now(timezone.utc),
            error_message=str(e)
        )
        update_job_progress(job_id, {
            "current_step": "failed",
            "total_steps": 6,
            "step_number": 0,
            "message": f"Analysis failed: {str(e)}"
        })

        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task
def cancel_analysis(job_id: str):
    """Cancel a running analysis job"""
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job and job.status in ["queued", "running"]:
            job.cancelled = True
            db.commit()
            logger.info(f"Analysis job {job_id} marked for cancellation")
            return {"job_id": job_id, "status": "cancelling"}
        return {"job_id": job_id, "status": job.status if job else "not_found"}
    finally:
        db.close()