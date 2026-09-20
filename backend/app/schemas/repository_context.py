from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BranchInfo(BaseModel):
    name: str
    commit_sha: str
    protected: bool = False


class RepositoryContext(BaseModel):
    id: str
    github_id: int
    full_name: str
    owner: str
    name: str
    description: Optional[str] = None
    default_branch: str
    is_private: bool
    language: Optional[str] = None
    stars: int
    forks: int
    size: int
    latest_commit_sha: Optional[str] = None
    latest_commit_message: Optional[str] = None
    latest_commit_date: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RepositoryListResponse(BaseModel):
    repositories: List[RepositoryContext]


class BranchesResponse(BaseModel):
    branches: List[BranchInfo]
    default_branch: str


class LatestCommitResponse(BaseModel):
    sha: str
    message: str
    author: str
    date: datetime
    url: str


class SyncRepositoryRequest(BaseModel):
    force: bool = False


class SyncRepositoryResponse(BaseModel):
    success: bool
    message: str
    repository: Optional[RepositoryContext] = None


# Tree and file schemas
class TreeNode(BaseModel):
    path: str
    mode: str  # "100644" for file, "040000" for directory
    type: str  # "blob" for file, "tree" for directory
    sha: str
    size: Optional[int] = None  # bytes, only for files
    # Extended metadata
    language: Optional[str] = None
    is_binary: bool = False
    is_generated: bool = False
    is_ignored: bool = False


class TreeResponse(BaseModel):
    sha: str
    tree: List[TreeNode]
    total_count: int
    truncated: bool = False
    tree_json: Optional[Dict[str, Any]] = None


class FileContentResponse(BaseModel):
    path: str
    sha: str
    size: int
    encoding: str  # "base64" or "utf-8"
    content: Optional[str] = None  # Decoded content (for text files)
    content_base64: Optional[str] = None  # Base64 encoded (for binary files)
    # Metadata
    language: Optional[str] = None
    is_binary: bool = False
    is_generated: bool = False
    is_ignored: bool = False


class FileContentRequest(BaseModel):
    path: str
    commit_sha: str


# Snapshot schemas
class SnapshotCreateRequest(BaseModel):
    commit_sha: str
    commit_message: Optional[str] = None
    commit_date: Optional[datetime] = None
    tree_json: Dict[str, Any]


class SnapshotResponse(BaseModel):
    id: str
    github_id: int
    owner: str
    name: str
    commit_sha: str
    commit_message: Optional[str] = None
    commit_date: Optional[datetime] = None
    tree_json: Dict[str, Any]
    total_files: int
    total_directories: int
    total_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotListResponse(BaseModel):
    snapshots: List[SnapshotResponse]