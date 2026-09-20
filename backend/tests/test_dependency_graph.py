from backend.app.analyzers.dependency_graph import build_dependency_graph


def test_dependency_graph():
    files = {
        "main.py": "import utils",
        "utils.py": "def calculate(): pass",
    }

    graph = build_dependency_graph(files)

    assert "main.py" in graph.nodes
    assert "utils.py" in graph.nodes
    # The graph analyzer now resolves module names to actual file paths
    assert graph.has_edge("main.py", "utils.py")
