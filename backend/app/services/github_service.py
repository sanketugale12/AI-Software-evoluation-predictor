import re
import httpx
import base64
import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from backend.app.schemas.repository import RepositoryResponse, RepositoryTreeResponse
from backend.app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c'}

# File size limit for preview (1MB)
FILE_SIZE_LIMIT = 1_000_000

# Common ignore patterns (directories/files to mark as ignored)
IGNORE_PATTERNS = [
    "node_modules/",
    ".git/",
    "dist/",
    "build/",
    "__pycache__/",
    ".venv/",
    "venv/",
    "env/",
    ".next/",
    ".nuxt/",
    "target/",
    "bin/",
    "obj/",
    ".idea/",
    ".vscode/",
    "*.min.js",
    "*.min.css",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "*.log",
    "*.tsbuildinfo",
]


async def extract_repository(url: str):
    logger.info(f"Extracting repository from URL: {url}")
    match = re.search(
        r"github\.com/([^/]+)/([^/#?]+)",
        url
    )

    if not match:
        logger.error(f"Failed to match regex for URL: {url}")
        raise ValueError("Invalid GitHub repository URL")

    owner = match.group(1)
    repo = match.group(2).removesuffix(".git")
    logger.info(f"Extracted: owner={owner}, repo={repo}")

    return owner, repo


def get_github_headers(access_token: Optional[str] = None):
    """Get GitHub API headers with optional user access token."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = access_token or settings.github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def fetch_repository_details(
    owner: str, repo: str, access_token: Optional[str] = None
):
    """Fetch repository details from GitHub API."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    logger.info(f"Fetching details from: {api_url}")

    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers)

    if response.status_code != 200:
        logger.error(f"API Error {response.status_code}: {response.text}")
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(
            status_code=response.status_code,
            detail="Repository could not be found"
        )

    data = response.json()

    return RepositoryResponse(
        name=data["full_name"],
        description=data["description"],
        language=data["language"],
        stars=data["stargazers_count"],
        forks=data["forks_count"],
        default_branch=data["default_branch"],
        size=data["size"],
        updated_at=data["updated_at"],
    )


async def fetch_repository_details_by_url(
    url: str, access_token: Optional[str] = None
) -> RepositoryResponse:
    """Fetch repository details from URL (backward compatibility)."""
    owner, repo = await extract_repository(url)
    return await fetch_repository_details(owner, repo, access_token)


async def fetch_repository_tree(
    owner: str, repo: str, access_token: Optional[str] = None
) -> RepositoryTreeResponse:
    """Fetch repository file tree."""
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        # Get default branch
        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        repo_res = await client.get(repo_url, headers=headers)
        if repo_res.status_code != 200:
            if repo_res.status_code == 403:
                raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
            raise HTTPException(status_code=repo_res.status_code, detail="Repository not found")

        default_branch = repo_res.json().get("default_branch", "main")

        # Get recursive tree
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        tree_res = await client.get(tree_url, headers=headers)
        if tree_res.status_code != 200:
            if tree_res.status_code == 403:
                raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
            raise HTTPException(status_code=tree_res.status_code, detail="Could not retrieve file tree")

        tree_data = tree_res.json()
        all_files = tree_data.get("tree", [])

        # Filter supported source files
        filtered_files = []
        for item in all_files:
            if item["type"] == "blob":
                path = item["path"]
                if any(path.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    if item.get("size", 0) < 1_000_000:
                        filtered_files.append(path)

        return RepositoryTreeResponse(files=filtered_files)


async def fetch_repository_tree_by_url(
    url: str, access_token: Optional[str] = None
) -> RepositoryTreeResponse:
    """Fetch repository tree from URL (backward compatibility)."""
    owner, repo = await extract_repository(url)
    return await fetch_repository_tree(owner, repo, access_token)


async def fetch_branches(
    owner: str, repo: str, access_token: Optional[str] = None
) -> list:
    """Fetch all branches for a repository."""
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches",
            headers=headers,
        )

    if response.status_code != 200:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        raise HTTPException(status_code=response.status_code, detail="Could not fetch branches")

    branches = []
    for branch in response.json():
        branches.append({
            "name": branch["name"],
            "commit_sha": branch["commit"]["sha"],
            "protected": branch.get("protected", False),
        })

    return branches


async def fetch_latest_commit(
    owner: str, repo: str, branch: str = "main", access_token: Optional[str] = None
) -> dict:
    """Fetch latest commit for a branch."""
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}",
            headers=headers,
        )

    if response.status_code != 200:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        raise HTTPException(status_code=response.status_code, detail="Could not fetch latest commit")

    commit = response.json()
    return {
        "sha": commit["sha"],
        "message": commit["commit"]["message"],
        "author": commit["commit"]["author"]["name"],
        "date": commit["commit"]["author"]["date"],
        "url": commit["html_url"],
    }


async def fetch_user_repositories(
    access_token: str, per_page: int = 100
) -> list:
    """Fetch authenticated user's repositories."""
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/user/repos?per_page={per_page}&sort=updated&affiliation=owner,collaborator",
            headers=headers,
        )

    if response.status_code != 200:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        raise HTTPException(status_code=response.status_code, detail="Could not fetch repositories")

    repos = []
    for repo in response.json():
        repos.append({
            "github_id": repo["id"],
            "full_name": repo["full_name"],
            "owner": repo["owner"]["login"],
            "name": repo["name"],
            "description": repo["description"],
            "default_branch": repo["default_branch"],
            "is_private": repo["private"],
            "language": repo["language"],
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "size": repo["size"],
            "updated_at": repo["updated_at"],
        })

    return repos


async def fetch_file_content(
    owner: str, repo: str, path: str, branch: str = "main", access_token: Optional[str] = None
) -> str:
    """
    Fetches the content of a specific file from GitHub.
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"

    headers = get_github_headers(access_token)
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Could not fetch file {path}")

    data = response.json()
    content_base64 = data.get("content", "")
    content_base64 = content_base64.replace("\n", "")

    return base64.b64decode(content_base64).decode("utf-8", errors="replace")


async def fetch_repository_tree_at_commit(
    owner: str, repo: str, commit_sha: str, access_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch the full repository tree at a specific commit SHA.
    Returns all files and directories with metadata.
    """
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        # Get recursive tree at specific commit
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{commit_sha}?recursive=1"
        tree_res = await client.get(tree_url, headers=headers)

        if tree_res.status_code != 200:
            if tree_res.status_code == 403:
                raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
            if tree_res.status_code == 404:
                raise HTTPException(status_code=404, detail="Tree not found for commit")
            raise HTTPException(status_code=tree_res.status_code, detail="Could not retrieve file tree")

        tree_data = tree_res.json()
        return tree_data.get("tree", [])


async def fetch_file_content_at_commit(
    owner: str, repo: str, path: str, commit_sha: str, access_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch file content at a specific commit SHA.
    Returns decoded content and metadata.
    """
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        # Get file content via contents API with commit SHA as ref
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={commit_sha}"
        response = await client.get(api_url, headers=headers)

        if response.status_code != 200:
            if response.status_code == 403:
                raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"File not found: {path}")
            raise HTTPException(status_code=response.status_code, detail=f"Could not fetch file {path}")

        data = response.json()

        # Check if file is too large
        size = data.get("size", 0)
        if size > FILE_SIZE_LIMIT:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({size} bytes). Maximum size is {FILE_SIZE_LIMIT} bytes."
            )

        content_base64 = data.get("content", "")
        content_base64 = content_base64.replace("\n", "")

        # Decode content
        try:
            content = base64.b64decode(content_base64).decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            # Binary file - return base64
            content = content_base64
            encoding = "base64"

        return {
            "path": path,
            "sha": data.get("sha"),
            "size": size,
            "encoding": encoding,
            "content": content if encoding == "utf-8" else None,
            "content_base64": content if encoding == "base64" else None,
        }


def detect_language_from_path(path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext_to_lang = {
        # Python
        ".py": "python",
        ".pyi": "python",
        ".pyx": "python",
        ".pxd": "python",
        ".pxi": "python",
        # JavaScript/TypeScript
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        # Java
        ".java": "java",
        # C/C++
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".hxx": "cpp",
        # C#
        ".cs": "csharp",
        # Go
        ".go": "go",
        # Rust
        ".rs": "rust",
        # Ruby
        ".rb": "ruby",
        ".rake": "ruby",
        # PHP
        ".php": "php",
        # Swift
        ".swift": "swift",
        # Kotlin
        ".kt": "kotlin",
        ".kts": "kotlin",
        # Scala
        ".scala": "scala",
        # Shell
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "fish",
        # SQL
        ".sql": "sql",
        # HTML/CSS
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "scss",
        ".less": "less",
        # Config/Markup
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".md": "markdown",
        ".markdown": "markdown",
        ".rst": "rst",
        # Docker
        "Dockerfile": "dockerfile",
        ".dockerignore": "dockerfile",
        # Git
        ".gitignore": "gitignore",
        ".gitattributes": "gitignore",
        # Protobuf
        ".proto": "protobuf",
        # GraphQL
        ".graphql": "graphql",
        ".gql": "graphql",
        # Vue/Svelte
        ".vue": "vue",
        ".svelte": "svelte",
        # Terraform
        ".tf": "hcl",
        ".tfvars": "hcl",
    }

    # Check exact filename first (e.g., Dockerfile, Makefile)
    filename = path.split("/")[-1]
    if filename in ext_to_lang:
        return ext_to_lang[filename]

    # Check extension
    for ext, lang in ext_to_lang.items():
        if path.endswith(ext):
            return lang

    return None


async def fetch_commit_files(
    owner: str, repo: str, commit_sha: str, access_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch files changed in a specific commit.
    """
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
        response = await client.get(api_url, headers=headers)

    if response.status_code != 200:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        raise HTTPException(status_code=response.status_code, detail="Could not fetch commit files")

    data = response.json()
    files = []
    for file in data.get("files", []):
        files.append({
            "filename": file["filename"],
            "status": file["status"],
            "additions": file["additions"],
            "deletions": file["deletions"],
            "changes": file["changes"],
        })

    return files

def is_binary_content(content: Any) -> bool:
    """Check if content is binary. Returns True if content is not a string or cannot be decoded as UTF-8."""
    if not isinstance(content, str):
        return True
    try:
        content.encode('utf-8')
        return False
    except UnicodeEncodeError:
        return True

def is_ignored_path(path: str) -> bool:
    """Check if path matches common ignore patterns."""
    import fnmatch
    for pattern in IGNORE_PATTERNS:
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, f"*/{pattern}"):
            return True
        # Check if any parent directory matches
        parts = path.split("/")
        for i in range(len(parts)):
            parent = "/".join(parts[:i+1])
            if fnmatch.fnmatch(parent, pattern) or fnmatch.fnmatch(parent, f"*/{pattern}"):
                return True
    return False


def is_generated_file(path: str, content: Optional[str] = None) -> bool:
    """Heuristics to detect generated files."""
    generated_patterns = [
        # Minified files
        r"\.min\.(js|css)$",
        # Bundle files
        r"bundle\.(js|css)$",
        r"vendor\.(js|css)$",
        # Generated by build tools
        r"\.g\.py$",
        r"_pb2\.py$",
        r"_grpc\.py$",
        # TypeScript generated
        r"\.d\.ts$",
        # Protobuf generated
        r"_pb2\.py$",
        # Lock files (could be committed but often generated)
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Cargo.lock",
        "go.sum",
        "composer.lock",
        "poetry.lock",
        # IDE/OS
        ".DS_Store",
        "Thumbs.db",
    ]

    import re
    for pattern in generated_patterns:
        if re.search(pattern, path):
            return True

    # Check content for generated headers
    if content:
        generated_headers = [
            "// Generated by",
            "/* Generated by",
            "# Generated by",
            "# Auto-generated",
            "// Auto-generated",
            "/* Auto-generated",
            "<auto-generated>",
            "/// <auto-generated>",
            "DO NOT EDIT",
            "do not edit",
            "autogenerated",
            "auto-generated",
        ]
        content_lower = content.lower()
        for header in generated_headers:
            if header.lower() in content_lower[:500]:  # Check first 500 chars
                return True

    return False


async def fetch_pull_requests(
    owner: str, repo: str, access_token: Optional[str] = None
) -> list:
    """Fetch pull requests for a repository."""
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        # Use the pulls API
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=100"
        response = await client.get(api_url, headers=headers)

    if response.status_code != 200:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        raise HTTPException(status_code=response.status_code, detail="Could not fetch pull requests")

    prs = []
    for pr in response.json():
        prs.append({
            "id": pr["id"],
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "user": pr["user"]["login"],
            "created_at": pr["created_at"],
            "closed_at": pr["closed_at"],
            "merged_at": pr["merged_at"],
            "base": pr["base"]["ref"],
            "head": pr["head"]["sha"],
            "html_url": pr["html_url"],
        })

    return prs


async def fetch_issues(
    owner: str, repo: str, access_token: Optional[str] = None
) -> list:
    """Fetch issues for a repository."""
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        # GitHub Issues API also returns PRs unless filtered
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100"
        response = await client.get(api_url, headers=headers)

    if response.status_code != 200:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        raise HTTPException(status_code=response.status_code, detail="Could not fetch issues")

    issues = []
    for issue in response.json():
        # Skip pull requests (they have a 'pull_request' key)
        if "pull_request" in issue:
            continue

        issues.append({
            "id": issue["id"],
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "user": issue["user"]["login"],
            "created_at": issue["created_at"],
            "closed_at": issue["closed_at"],
            "labels": [label["name"] for label in issue["labels"]],
            "html_url": issue["html_url"],
        })

    return issues


async def fetch_workflow_runs(
    owner: str, repo: str, access_token: Optional[str] = None
) -> list:
    """Fetch CI/CD workflow runs."""
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=100"
        response = await client.get(api_url, headers=headers)

    if response.status_code != 200:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        raise HTTPException(status_code=response.status_code, detail="Could not fetch workflow runs")

    runs_data = response.json()
    runs = []
    for run in runs_data.get("workflow_runs", []):
        runs.append({
            "id": run["id"],
            "workflow_id": run["workflow_id"],
            "status": run["status"],
            "conclusion": run["conclusion"],
            "event": run["event"],
            "created_at": run["created_at"],
            "updated_at": run["updated_at"],
            "head_sha": run["head_sha"],
            "html_url": run["html_url"],
        })

    return runs


async def fetch_releases(
    owner: str, repo: str, access_token: Optional[str] = None
) -> list:
    """Fetch repository releases."""
    headers = get_github_headers(access_token)

    async with httpx.AsyncClient() as client:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        response = await client.get(api_url, headers=headers)

    if response.status_code != 200:
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded")
        raise HTTPException(status_code=response.status_code, detail="Could not fetch releases")

    releases = []
    for rel in response.json():
        releases.append({
            "id": rel["id"],
            "tag_name": rel["tag_name"],
            "name": rel["name"],
            "published_at": rel["published_at"],
            "author": rel["author"]["login"],
            "html_url": rel["html_url"],
        })

    return releases
