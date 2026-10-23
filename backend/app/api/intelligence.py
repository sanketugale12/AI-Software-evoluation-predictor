from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.app.database import SessionLocal
from backend.app.services.auth_service import AuthService
from backend.app.services.relationship_engine import RelationshipEngine
from backend.app.services.github_service import get_github_headers

router = APIRouter(tags=["Intelligence"])

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
    uid = x_user_id or user_id
    if uid == "test_user":
        return uid
    if not uid:
        raise HTTPException(status_code=401, detail="User ID required")
    return uid

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

@router.get("/repositories/{owner}/{repo}/intelligence", response_model=None)
async def get_repo_intelligence(
    owner: str,
    repo: str,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """
    Fetch the full relationship map for a repository.
    Links Issues -> PRs -> Commits -> Files -> Symbols.
    """
    access_token = auth_service.get_valid_access_token(user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # RelationshipEngine needs a github_service reference or just use the functions directly
    # Since the service functions are standalone async functions, we can wrap them
    # in a simple class or just use them. I'll use a dummy wrapper for the engine.
    class GithubServiceWrapper:
        async def fetch_pull_requests(self, o, r, t):
            from backend.app.services.github_service import fetch_pull_requests
            return await fetch_pull_requests(o, r, t)
        async def fetch_issues(self, o, r, t):
            from backend.app.services.github_service import fetch_issues
            return await fetch_issues(o, r, t)
        async def fetch_workflow_runs(self, o, r, t):
            from backend.app.services.github_service import fetch_workflow_runs
            return await fetch_workflow_runs(o, r, t)
        async def fetch_releases(self, o, r, t):
            from backend.app.services.github_service import fetch_releases
            return await fetch_releases(o, r, t)

    engine = RelationshipEngine(GithubServiceWrapper())
    return await engine.build_relationship_map(owner, repo, access_token)

@router.get("/repositories/{owner}/{repo}/prs/{pr_number}/risk", response_model=None)
async def get_pr_risk(
    owner: str,
    repo: str,
    pr_number: int,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """
    Analyze a specific PR for architectural risk.
    """
    access_token = auth_service.get_valid_access_token(user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    class GithubServiceWrapper:
        async def fetch_pull_requests(self, o, r, t):
            from backend.app.services.github_service import fetch_pull_requests
            return await fetch_pull_requests(o, r, t)
        # ... other methods as needed

    engine = RelationshipEngine(GithubServiceWrapper())
    return await engine.analyze_pr_risk(owner, repo, pr_number, access_token)

@router.get("/repositories/{owner}/{repo}/runs/{run_id}/impact", response_model=None)
async def get_ci_impact(
    owner: str,
    repo: str,
    run_id: str,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """
    Correlate CI failure to technical debt.
    """
    access_token = auth_service.get_valid_access_token(user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    class GithubServiceWrapper:
        async def fetch_pull_requests(self, o, r, t):
            from backend.app.services.github_service import fetch_pull_requests
            return await fetch_pull_requests(o, r, t)

    engine = RelationshipEngine(GithubServiceWrapper())
    return await engine.analyze_ci_impact(owner, repo, run_id, access_token)
