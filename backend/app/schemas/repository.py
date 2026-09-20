from pydantic import BaseModel
from typing import List

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

class DependencyRequest(BaseModel):
    url: str

class DependencyNode(BaseModel):
    id: str

class DependencyEdge(BaseModel):
    source: str
    target: str

class DependencyGraphResponse(BaseModel):
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
