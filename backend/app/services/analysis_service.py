from typing import Dict
import httpx
from backend.app.services.github_service import (
    extract_repository,
    fetch_repository_tree,
    fetch_file_content,
    get_github_headers
)
from backend.app.analyzers.dependency_graph import build_dependency_graph
from backend.app.schemas.repository import DependencyGraphResponse, DependencyNode, DependencyEdge

async def get_dependency_graph(url: str) -> DependencyGraphResponse:
    """
    Orchestrates the process of fetching repository files and building a dependency graph.
    """
    # 1. Identify repository owner and name
    owner, repo = await extract_repository(url)

    # 2. Get the default branch
    # We can reuse fetch_repository_tree's logic or just call it.
    # To avoid redundant API calls, let's just get the tree first.
    tree_res = await fetch_repository_tree(owner, repo)
    files_list = tree_res.files

    # 3. Fetch content for all supported files
    files_content = {}
    async with httpx.AsyncClient() as client:
        for path in files_list:
            try:
                # We'll use a simple loop for now. In production, we'd use asyncio.gather.
                # Using the existing fetch_file_content logic but passing the client.
                api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                response = await client.get(api_url, headers=get_github_headers())
                if response.status_code == 200:
                    import base64
                    data = response.json()
                    content = base64.b64decode(data.get("content", "").replace("\n", "")).decode("utf-8", errors="replace")
                    files_content[path] = content
            except Exception:
                continue

    # 4. Build the graph using the analyzer
    graph = build_dependency_graph(files_content)

    # 5. Format for API response
    nodes = [DependencyNode(id=node) for node in graph.nodes]
    edges = [DependencyEdge(source=u, target=v) for u, v in graph.edges]

    return DependencyGraphResponse(nodes=nodes, edges=edges)
