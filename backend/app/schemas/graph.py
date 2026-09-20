from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    type: str = "file"


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str = "imports"


class DependencyGraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
