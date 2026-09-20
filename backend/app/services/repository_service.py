from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.services.github_service import (
    fetch_repository_details,
    fetch_branches,
    fetch_latest_commit,
    fetch_user_repositories,
)
from backend.app.models.repository import Repository
from backend.app.models.repository_snapshot import RepositorySnapshot
from backend.app.models.user import User
from backend.app.services.ingestion_service import (
    clone_repository_at_commit,
    IngestionConfig,
    IngestionResult,
    IngestionError,
    validate_repository_size,
    cleanup_workspace,
)


def clone_repository(repository_url: str, commit_sha: Optional[str] = None):
    """
    Clones a Git repository into a temporary directory.

    Args:
        repository_url: The URL of the repository to clone.
        commit_sha: Optional commit SHA to checkout. If provided, uses
            the new ingestion service with resource limits. If not provided,
            uses the legacy shallow clone for backward compatibility.

    Returns:
        The TemporaryDirectory object. The caller is responsible for
        keeping this object alive while the analysis is running.

    Raises:
        IngestionError: If using commit_sha and limits are exceeded or clone fails
    """
    from tempfile import TemporaryDirectory
    from git import Repo

    # If commit_sha is provided, use the new safe ingestion service
    if commit_sha:
        result: IngestionResult = clone_repository_at_commit(
            repository_url,
            commit_sha,
            IngestionConfig()
        )
        # Store the stats on the temp_dir for access by callers
        result.temp_dir.stats = result.stats
        return result.temp_dir

    # Legacy behavior for backward compatibility
    temp_dir = TemporaryDirectory()

    Repo.clone_from(
        repository_url,
        temp_dir.name,
        depth=1,
    )

    return temp_dir


def clone_repository_with_limits(
    repository_url: str,
    commit_sha: str,
    config: Optional[IngestionConfig] = None,
) -> IngestionResult:
    """
    Clone a repository at a specific commit with resource limits enforcement.

    Args:
        repository_url: GitHub repository URL
        commit_sha: Commit SHA to pin analysis to
        config: Optional ingestion configuration

    Returns:
        IngestionResult with repo path, stats, and temp directory handle

    Raises:
        IngestionError: If limits are exceeded or clone fails
    """
    if config is None:
        config = IngestionConfig()

    return clone_repository_at_commit(repository_url, commit_sha, config)


async def get_repository_files(db: Session, user_id: str, owner: str, repo: str) -> List[str]:
    """
    Retrieve a list of all file paths for a repository from the latest snapshot.
    """
    snapshot = await get_latest_repository_snapshot(db, user_id, owner, repo)
    if not snapshot:
        return []

    # Extract all blob paths from the tree_json
    files = []
    def extract_blobs(node):
        if node.get("type") == "tree" and "children" in node:
            for child in node["children"]:
                extract_blobs(child)
        elif node.get("type") == "blob":
            files.append(node.get("path", ""))

    extract_blobs(snapshot.tree_json)
    return files

async def sync_repository(
    db: Session,
    user_id: str,
    owner: str,
    repo: str,
    access_token: str,
    force: bool = False,
) -> Repository:
    """
    Sync repository data from GitHub to local database.
    """
    # Fetch latest data from GitHub
    github_repo = await fetch_repository_details(owner, repo, access_token)
    latest_commit = await fetch_latest_commit(owner, repo, github_repo.default_branch, access_token)

    # Check if repository exists
    existing = (
        db.query(Repository)
        .filter(Repository.user_id == user_id, Repository.owner == owner, Repository.name == repo)
        .first()
    )

    if existing and not force:
        # Update existing
        existing.github_id = github_repo["github_id"] if isinstance(github_repo, dict) else 0
        existing.full_name = github_repo.full_name
        existing.description = github_repo.description
        existing.default_branch = github_repo.default_branch
        existing.is_private = False  # We know it's accessible
        existing.language = github_repo.language
        existing.stars = github_repo.stars
        existing.forks = github_repo.forks
        existing.size = github_repo.size
        existing.latest_commit_sha = latest_commit.get("sha")
        existing.latest_commit_message = latest_commit.get("message")
        existing.latest_commit_date = (
            datetime.fromisoformat(latest_commit["date"].replace("Z", "+00:00"))
            if latest_commit.get("date")
            else None
        )
        existing.last_synced_at = datetime.now(timezone.utc)
        existing.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        new_repo = Repository(
            user_id=user_id,
            github_id=github_repo["github_id"] if isinstance(github_repo, dict) else 0,
            full_name=github_repo.full_name,
            owner=owner,
            name=repo,
            description=github_repo.description,
            default_branch=github_repo.default_branch,
            is_private=False,
            language=github_repo.language,
            stars=github_repo.stars,
            forks=github_repo.forks,
            size=github_repo.size,
            latest_commit_sha=latest_commit.get("sha"),
            latest_commit_message=latest_commit.get("message"),
            latest_commit_date=(
                datetime.fromisoformat(latest_commit["date"].replace("Z", "+00:00"))
                if latest_commit.get("date")
                else None
            ),
            last_synced_at=datetime.now(timezone.utc),
        )
        db.add(new_repo)
        db.commit()
        db.refresh(new_repo)
        return new_repo


async def get_user_repositories(db: Session, user_id: str) -> List[Repository]:
    """Get all repositories for a user."""
    return (
        db.query(Repository)
        .filter(Repository.user_id == user_id)
        .order_by(Repository.updated_at.desc())
        .all()
    )


async def get_repository_context(
    db: Session, user_id: str, owner: str, repo: str
) -> Optional[Repository]:
    """Get repository context for a user."""
    return (
        db.query(Repository)
        .filter(Repository.user_id == user_id, Repository.owner == owner, Repository.name == repo)
        .first()
    )


async def sync_user_repositories(
    db: Session, user_id: str, access_token: str
) -> List[Repository]:
    """Sync all user's repositories from GitHub."""
    github_repos = await fetch_user_repositories(access_token)
    synced = []

    for github_repo in github_repos:
        repo = await sync_repository(
            db,
            user_id,
            github_repo["owner"],
            github_repo["name"],
            access_token,
            force=False,
        )
        synced.append(repo)

    return synced


def _build_tree_json(tree_nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert flat tree list to nested JSON structure for storage."""
    # Build a nested tree structure from flat list
    root = {"type": "tree", "path": "", "children": []}
    path_to_node = {"": root}

    for node in tree_nodes:
        path = node.get("path", "")
        if not path:
            continue

        # Create node entry
        node_entry = {
            "path": path,
            "mode": node.get("mode", ""),
            "type": node.get("type", ""),
            "sha": node.get("sha", ""),
            "size": node.get("size"),
            "language": node.get("language"),
            "is_binary": node.get("is_binary", False),
            "is_generated": node.get("is_generated", False),
            "is_ignored": node.get("is_ignored", False),
            "children": [] if node.get("type") == "tree" else None,
        }

        path_to_node[path] = node_entry

        # Find parent
        parent_path = "/".join(path.split("/")[:-1])
        parent = path_to_node.get(parent_path, root)
        if "children" in parent and parent["children"] is not None:
            parent["children"].append(node_entry)

    return root


async def save_repository_snapshot(
    db: Session,
    user_id: str,
    owner: str,
    repo: str,
    github_id: int,
    commit_sha: str,
    commit_message: Optional[str],
    commit_date: Optional[datetime],
    tree_nodes: List[Dict[str, Any]],
) -> RepositorySnapshot:
    """
    Save repository tree snapshot to database.
    """
    # Calculate tree statistics
    total_files = sum(1 for n in tree_nodes if n.get("type") == "blob")
    total_directories = sum(1 for n in tree_nodes if n.get("type") == "tree")
    total_size = sum(n.get("size", 0) or 0 for n in tree_nodes if n.get("type") == "blob")

    # Build nested tree JSON
    tree_json = _build_tree_json(tree_nodes)

    # Create snapshot
    snapshot = RepositorySnapshot(
        user_id=user_id,
        github_id=github_id,
        owner=owner,
        name=repo,
        commit_sha=commit_sha,
        commit_message=commit_message,
        commit_date=commit_date,
        tree_json=tree_json,
        total_files=total_files,
        total_directories=total_directories,
        total_size=total_size,
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot


async def get_repository_snapshot(
    db: Session, user_id: str, owner: str, repo: str, commit_sha: str
) -> Optional[RepositorySnapshot]:
    """
    Retrieve a specific repository snapshot.
    """
    return (
        db.query(RepositorySnapshot)
        .filter(
            RepositorySnapshot.user_id == user_id,
            RepositorySnapshot.owner == owner,
            RepositorySnapshot.name == repo,
            RepositorySnapshot.commit_sha == commit_sha,
        )
        .first()
    )


async def get_latest_repository_snapshot(
    db: Session, user_id: str, owner: str, repo: str
) -> Optional[RepositorySnapshot]:
    """
    Retrieve the most recent snapshot for a repository.
    """
    return (
        db.query(RepositorySnapshot)
        .filter(
            RepositorySnapshot.user_id == user_id,
            RepositorySnapshot.owner == owner,
            RepositorySnapshot.name == repo,
        )
        .order_by(RepositorySnapshot.created_at.desc())
        .first()
    )


async def list_repository_snapshots(
    db: Session, user_id: str, owner: str, repo: str, limit: int = 50
) -> List[RepositorySnapshot]:
    """
    List all snapshots for a repository.
    """
    return (
        db.query(RepositorySnapshot)
        .filter(
            RepositorySnapshot.user_id == user_id,
            RepositorySnapshot.owner == owner,
            RepositorySnapshot.name == repo,
        )
        .order_by(RepositorySnapshot.created_at.desc())
        .limit(limit)
        .all()
    )


async def delete_repository_snapshot(
    db: Session, user_id: str, snapshot_id: str
) -> bool:
    """
    Delete a repository snapshot.
    """
    snapshot = (
        db.query(RepositorySnapshot)
        .filter(
            RepositorySnapshot.id == snapshot_id,
            RepositorySnapshot.user_id == user_id,
        )
        .first()
    )

    if snapshot:
        db.delete(snapshot)
        db.commit()
        return True

    return False