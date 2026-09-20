from pydantic import BaseModel, HttpUrl
from typing import Optional, Any, List
from datetime import datetime


class AnalysisJobCreate(BaseModel):
    repository_url: HttpUrl


class AnalysisJobRequest(BaseModel):
    """Request to start a new analysis (Phase 6: with optional commit_sha)"""
    commit_sha: Optional[str] = None


class AnalysisJobResponse(BaseModel):
    job_id: str
    status: str
    created_at: Optional[datetime] = None
    progress: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    version: Optional[int] = None
    retry_count: Optional[int] = None
    cancelled: Optional[bool] = None
    commit_sha: Optional[str] = None

    class Config:
        from_attributes = True


class AnalysisResultsResponse(BaseModel):
    job_id: str
    status: str
    results: Optional[Any] = None
    error_message: Optional[str] = None


class AnalysisJobListResponse(BaseModel):
    jobs: List[AnalysisJobResponse]


class CancelAnalysisRequest(BaseModel):
    pass


class RetryAnalysisRequest(BaseModel):
    pass