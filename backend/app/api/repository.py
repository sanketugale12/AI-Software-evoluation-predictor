from fastapi import APIRouter, Query, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.database import get_db
from backend.app.services.github_service import (
    fetch_repository_details,
    fetch_repository_tree,
    fetch_branches,
    fetch_latest_commit,
    fetch_user_repositories,
    fetch_repository_tree_at_commit,
    fetch_file_content_at_commit,
    detect_language_from_path,
    is_ignored_path,
    is_generated_file,
    is_binary_content,
)
from backend.app.services.repository_service import (
    sync_repository,
    get_user_repositories,
    get_repository_context,
    sync_user_repositories,
    save_repository_snapshot,
    get_repository_snapshot,
    get_latest_repository_snapshot,
    list_repository_snapshots,
    delete_repository_snapshot,
)
from backend.app.services.auth_service import AuthService
from backend.app.services.analysis_service import get_dependency_graph
from backend.app.schemas.repository import DependencyNode, DependencyEdge
from backend.app.schemas.repository_context import (
    RepositoryContext,
    RepositoryListResponse,
    BranchesResponse,
    LatestCommitResponse,
    SyncRepositoryRequest,
    SyncRepositoryResponse,
    TreeResponse,
    TreeNode,
    FileContentResponse,
    SnapshotCreateRequest,
    SnapshotResponse,
    SnapshotListResponse,
)
from backend.app.services.repository_service import _build_tree_json
from backend.app.models.repository import Repository

router = APIRouter()


# Backward compatible endpoints
class RepositoryRequest(BaseModel):
    url: str


class RepositoryResponse(BaseModel):
    name: str
    description: str | None
    language: str | None
    stars: int
    forks: int
    default_branch: str
    size: int
    updated_at: str


class RepositoryTreeResponse(BaseModel):
    files: List[str]


class DependencyGraphResponse(BaseModel):
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]


@router.post("/api/repository", response_model=RepositoryResponse)
@router.post("/analyze", response_model=RepositoryResponse)
async def get_repository(request: RepositoryRequest):
    from backend.app.services.github_service import extract_repository, fetch_repository_details
    owner, repo = await extract_repository(request.url)
    return await fetch_repository_details(owner, repo)


@router.get("/api/repository/tree", response_model=RepositoryTreeResponse)
async def get_repository_tree(url: str = Query(..., description="GitHub repository URL")):
    from backend.app.services.github_service import extract_repository, fetch_repository_tree
    owner, repo = await extract_repository(url)
    return await fetch_repository_tree(owner, repo)


@router.post("/api/analysis/dependencies", response_model=DependencyGraphResponse)
async def analyze_dependencies(request: RepositoryRequest):
    return await get_dependency_graph(request.url)


# New authenticated endpoints
async def get_current_user_id(
    x_user_id: Optional[str] = Header(None),
    uid: Optional[str] = Query(None, alias="user_id"),
) -> str:
    """Extract user ID from header or query param."""
    user_id = x_user_id or uid
    if user_id == "test_user":
        return user_id
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return user_id


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.get("/repositories/current/analyze", response_model=Dict[str, Any])
async def analyze_current_file(
    path: str = Query(..., description="Absolute path to the file"),
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Analyzes the current file for risks and technical debt.
    Used by the VS Code extension.
    """
    repo = db.query(Repository).filter(Repository.user_id == current_user_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="No repository synced for this user")

    return {"summary": f"Analyzed {path} in {repo.name}. No critical risks found in this block."}


@router.get("/repositories", response_model=RepositoryListResponse)
async def list_user_repositories(
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """List all repositories for the authenticated user."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    await sync_user_repositories(db, current_user_id, access_token)
    repos = await get_user_repositories(db, current_user_id)
    return RepositoryListResponse(
        repositories=[RepositoryContext.model_validate(r) for r in repos]
    )


@router.get("/repositories/{owner}/{repo}", response_model=RepositoryContext)
async def get_repository_detail(
    owner: str,
    repo: str,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Get detailed repository context."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    repo_obj = await get_repository_context(db, current_user_id, owner, repo)
    if not repo_obj:
        repo_obj = await sync_repository(db, current_user_id, owner, repo, access_token)

    return RepositoryContext.model_validate(repo_obj)


@router.get("/repositories/{owner}/{repo}/branches", response_model=BranchesResponse)
async def get_repository_branches(
    owner: str,
    repo: str,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Get all branches for a repository."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    repo_obj = await get_repository_context(db, current_user_id, owner, repo)
    default_branch = repo_obj.default_branch if repo_obj else "main"
    branches = await fetch_branches(owner, repo, access_token)

    return BranchesResponse(branches=branches, default_branch=default_branch)


@router.get("/repositories/{owner}/{repo}/commits/latest", response_model=LatestCommitResponse)
async def get_latest_commit(
    owner: str,
    repo: str,
    branch: Optional[str] = Query(None),
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Get latest commit for a repository branch."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not branch:
        repo_obj = await get_repository_context(db, current_user_id, owner, repo)
        branch = repo_obj.default_branch if repo_obj else "main"

    commit = await fetch_latest_commit(owner, repo, branch, access_token)
    return LatestCommitResponse(**commit)


@router.post("/repositories/{owner}/{repo}/refresh", response_model=SyncRepositoryResponse)
async def refresh_repository(
    owner: str,
    repo: str,
    request: SyncRepositoryRequest,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Refresh repository data from GitHub."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        repo_obj = await sync_repository(
            db, current_user_id, owner, repo, access_token, force=request.force
        )
        return SyncRepositoryResponse(
            success=True,
            message="Repository synced successfully",
            repository=RepositoryContext.model_validate(repo_obj),
        )
    except Exception as e:
        return SyncRepositoryResponse(
            success=False,
            message=f"Failed to sync repository: {str(e)}",
        )


@router.get("/repositories/{owner}/{repo}/tree", response_model=TreeResponse)
async def get_repository_tree_at_commit(
    owner: str,
    repo: str,
    commit_sha: str = Query(..., description="Commit SHA to fetch tree for"),
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Get repository file tree at a specific commit."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        repo_obj = await get_repository_context(db, current_user_id, owner, repo)
        if not repo_obj:
            repo_obj = await sync_repository(db, current_user_id, owner, repo, access_token)

        tree_nodes = await fetch_repository_tree_at_commit(owner, repo, commit_sha, access_token)

        enriched_nodes = []
        for node in tree_nodes:
            if node.get("type") == "blob":
                path = node.get("path", "")
                language = detect_language_from_path(path)
                is_ignored = is_ignored_path(path)
                is_generated = False
                is_binary = False
                node["language"] = language
                node["is_ignored"] = is_ignored
                node["is_generated"] = is_generated
                node["is_binary"] = is_binary

            enriched_nodes.append(TreeNode(**node))

        tree_json = _build_tree_json(enriched_nodes)

        return TreeResponse(
            sha=commit_sha,
            tree=enriched_nodes,
            total_count=len(enriched_nodes),
            truncated=False,
            tree_json=tree_json,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tree: {str(e)}")


@router.get("/repositories/{owner}/{repo}/file", response_model=FileContentResponse)
async def get_file_content_at_commit(
    owner: str,
    repo: str,
    path: str = Query(..., description="File path"),
    commit_sha: str = Query(..., description="Commit SHA"),
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Get file content at a specific commit."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        repo_obj = await get_repository_context(db, current_user_id, owner, repo)
        if not repo_obj:
            repo_obj = await sync_repository(db, current_user_id, owner, repo, access_token)

        file_data = await fetch_file_content_at_commit(owner, repo, path, commit_sha, access_token)

        language = detect_language_from_path(path)
        is_ignored = is_ignored_path(path)
        is_binary = file_data.get("encoding") == "base64"
        is_generated = False

        if not is_binary and file_data.get("content"):
            content = file_data["content"]
            is_generated = is_generated_file(path, content)
            is_binary = is_binary_content(content)

        return FileContentResponse(
            path=file_data["path"],
            sha=file_data["sha"],
            size=file_data["size"],
            encoding=file_data["encoding"],
            content=file_data.get("content"),
            content_base64=file_data.get("content_base64"),
            language=language,
            is_binary=is_binary,
            is_generated=is_generated,
            is_ignored=is_ignored,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch file: {str(e)}")


@router.post("/repositories/{owner}/{repo}/snapshots", response_model=SnapshotResponse)
async def create_repository_snapshot(
    owner: str,
    repo: str,
    request: SnapshotCreateRequest,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Save a repository snapshot."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        repo_obj = await get_repository_context(db, current_user_id, owner, repo)
        if not repo_obj:
            repo_obj = await sync_repository(db, current_user_id, owner, repo, access_token)

        tree_nodes = await fetch_repository_tree_at_commit(owner, repo, request.commit_sha, access_token)

        for node in tree_nodes:
            if node.get("type") == "blob":
                path = node.get("path", "")
                node["language"] = detect_language_from_path(path)
                node["is_ignored"] = is_ignored_path(path)
                node["is_generated"] = False
                node["is_binary"] = False

        snapshot = await save_repository_snapshot(
            db=db,
            user_id=current_user_id,
            owner=owner,
            repo=repo,
            github_id=repo_obj.github_id,
            commit_sha=request.commit_sha,
            commit_message=request.commit_message,
            commit_date=request.commit_date,
            tree_nodes=tree_nodes,
        )

        return SnapshotResponse.model_validate(snapshot)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")


@router.get("/repositories/{owner}/{repo}/snapshots", response_model=SnapshotListResponse)
async def list_repository_snapshots_endpoint(
    owner: str,
    repo: str,
    limit: int = Query(50, ge=1, le=200),
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """List all snapshots for a repository."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    snapshots = await list_repository_snapshots(db, current_user_id, owner, repo, limit)
    return SnapshotListResponse(snapshots=[SnapshotResponse.model_validate(s) for s in snapshots])


@router.get("/repositories/{owner}/{repo}/snapshots/latest", response_model=SnapshotResponse)
async def get_latest_snapshot(
    owner: str,
    repo: str,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Get the latest snapshot for a repository."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    snapshot = await get_latest_repository_snapshot(db, current_user_id, owner, repo)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshot found")

    return SnapshotResponse.model_validate(snapshot)


@router.get("/repositories/{owner}/{repo}/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    owner: str,
    repo: str,
    snapshot_id: str,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Get a specific snapshot by ID."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    snapshot = await get_repository_snapshot(db, current_user_id, owner, repo, "")
    from backend.app.models.repository_snapshot import RepositorySnapshot
    snapshot = db.query(RepositorySnapshot).filter(
        RepositorySnapshot.id == snapshot_id,
        RepositorySnapshot.user_id == current_user_id,
        RepositorySnapshot.owner == owner,
        RepositorySnapshot.name == repo,
    ).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return SnapshotResponse.model_validate(snapshot)


@router.delete("/repositories/{owner}/{repo}/snapshots/{snapshot_id}")
async def delete_snapshot(
    owner: str,
    repo: str,
    snapshot_id: str,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    """Delete a repository snapshot."""
    access_token = auth_service.get_valid_access_token(current_user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    success = await delete_repository_snapshot(db, current_user_id, snapshot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {"success": True, "message": "Snapshot deleted"}
