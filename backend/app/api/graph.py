from fastapi import APIRouter
from backend.app.analyzers.dependency_graph import build_dependency_graph

router = APIRouter()


@router.post("/dependencies")
def dependencies(files: dict[str, str]):
    graph = build_dependency_graph(files)

    return {
        "nodes": [
            {"id": node, "label": node, "type": "file"}
            for node in graph.nodes
        ],
        "edges": [
            {"source": source, "target": target, "type": "imports"}
            for source, target in graph.edges
        ],
    }
