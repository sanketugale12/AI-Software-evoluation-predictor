import re
import networkx as nx
from pathlib import PurePosixPath
from .ast_analyzer import analyze_ast, SymbolType
from .arch_intelligence import analyze_architecture


def resolve_import(module: str, file_paths: set[str]):
    """Resolve a Python module path to an actual file path."""
    if not module:
        return None
    expected = module.replace(".", "/")

    candidates = [
        f"{expected}.py",
        f"{expected}/__init__.py",
    ]

    for path in candidates:
        if path in file_paths:
            return path

    return None


def _extract_python_imports(source_code: str) -> list[str]:
    """Extract imported module names from Python source code."""
    imports = []
    try:
        import ast
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Handle relative imports
                    if node.level and node.level > 0:
                        # Relative import - skip for now, too context-dependent
                        continue
                    imports.append(node.module)
    except SyntaxError:
        # Fallback to regex for non-Python or invalid Python
        imports.extend(_extract_imports_regex(source_code, "py"))
    return imports


def _extract_js_imports(source_code: str, ext: str) -> list[str]:
    """Extract imported module paths from JavaScript/TypeScript source code."""
    imports = []
    # ES6 import: import X from './path'
    for match in re.finditer(
        r'(?:import|export)\s+.*?\s+from\s+["\']([^"\']+)["\']',
        source_code,
    ):
        imports.append(match.group(1))
    # require: const X = require('./path')
    for match in re.finditer(
        r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
        source_code,
    ):
        imports.append(match.group(1))
    return imports


def _extract_imports_regex(source_code: str, ext: str) -> list[str]:
    """Regex-based import extraction as fallback."""
    imports = []
    if ext == "py":
        # import X
        for match in re.finditer(r'^\s*import\s+(\S+)', source_code, re.MULTILINE):
            imports.append(match.group(1).split(",")[0].strip())
        # from X import Y
        for match in re.finditer(r'^\s*from\s+(\S+)\s+import', source_code, re.MULTILINE):
            imports.append(match.group(1))
    elif ext in ("js", "ts", "tsx", "jsx"):
        imports.extend(_extract_js_imports(source_code, ext))
    return imports


def _resolve_import_path(import_path: str, current_file: str, file_paths: set[str]) -> str | None:
    """Resolve an import path to an actual file path."""
    # Skip external packages (not relative, not absolute)
    if import_path.startswith("."):
        # Relative import
        current_dir = str(PurePosixPath(current_file).parent)
        if current_dir == ".":
            current_dir = ""
        resolved = str(PurePosixPath(current_dir) / import_path)
        # Try various extensions
        candidates = [
            f"{resolved}.py",
            f"{resolved}.js",
            f"{resolved}.ts",
            f"{resolved}/__init__.py",
            f"{resolved}/index.js",
            f"{resolved}/index.ts",
        ]
        for cand in candidates:
            if cand in file_paths:
                return cand
        return None
    else:
        # Absolute module path - try Python-style resolution
        return resolve_import(import_path, file_paths)


def build_dependency_graph(files: dict[str, str]):
    """
    Builds a directed dependency graph from source code files.
    Parses imports from each file and resolves them to actual file paths.
    """
    graph = nx.DiGraph()
    file_paths = set(files.keys())

    # Add all files as nodes (simple file path IDs)
    for file_path in files:
        graph.add_node(file_path, label=file_path)

    # Extract imports from each file and resolve
    for file_path, source_code in files.items():
        ext = file_path.rsplit(".", 1)[-1] if "." in file_path else ""

        # Extract imports based on file type
        if ext == "py":
            imports = _extract_python_imports(source_code)
        elif ext in ("js", "ts", "tsx", "jsx"):
            imports = _extract_js_imports(source_code, ext)
        else:
            imports = []

        # Resolve each import to a file path
        for imp in imports:
            resolved = _resolve_import_path(imp, file_path, file_paths)
            if resolved and resolved != file_path:
                if graph.has_node(resolved):
                    graph.add_edge(file_path, resolved)

    # Also add symbol-level dependencies from AST analyzer
    all_symbols = []
    for file_path in files:
        try:
            symbols = analyze_ast(file_path)
            all_symbols.extend(symbols)
        except Exception:
            pass

    for symbol in all_symbols:
        for dep_id in symbol.dependencies:
            if graph.has_node(dep_id):
                graph.add_edge(symbol.id, dep_id)

    return graph


def get_architecture_intelligence(files: dict[str, str]):
    """
    Analyzes the project architecture using AST and NetworkX metrics.
    """
    all_symbols = []
    for file_path in files:
        try:
            symbols = analyze_ast(file_path)
            all_symbols.extend(symbols)
        except Exception:
            pass

    return analyze_architecture(all_symbols)