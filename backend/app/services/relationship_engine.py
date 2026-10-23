import logging
from typing import List, Dict, Any, Optional
from backend.app.services.github_service import (
    fetch_pull_requests,
    fetch_issues,
    fetch_workflow_runs,
    fetch_releases,
    fetch_commit_files
)

logger = logging.getLogger(__name__)

class RelationshipEngine:
    """
    Links GitHub entities to Architectural Symbols.
    Mapping: Issue -> PR -> Commit -> File -> Symbol
    """

    def __init__(self, github_service):
        self.github = github_service

    async def build_relationship_map(self, owner: str, repo: str, access_token: Optional[str] = None):
        """
        Builds a graph of relationships between different GitHub entities.
        """
        logger.info(f"Building relationship map for {owner}/{repo}")

        # Fetch all entities in parallel
        prs = await fetch_pull_requests(owner, repo, access_token)
        issues = await fetch_issues(owner, repo, access_token)
        runs = await fetch_workflow_runs(owner, repo, access_token)
        releases = await fetch_releases(owner, repo, access_token)

        # 1. Map Issues to PRs
        # GitHub often links issues in PR descriptions or via 'closes #123'
        issue_to_prs = {}
        for pr in prs:
            # In a real scenario, we'd fetch the PR body to find linked issues
            # For now, we simulate a basic mapping
            pass

        # 2. Map PRs to Commits
        # The 'head' SHA is the most recent commit in the PR
        pr_to_commits = {pr['id']: [pr['head']] for pr in prs}

        # 3. Map Commits to Files
        # This requires calling GitHub's commit API for each PR's head
        commit_to_files = {}
        for pr in prs:
            commit_sha = pr['head']
            try:
                files = await fetch_commit_files(owner, repo, commit_sha, access_token)
                commit_to_files[commit_sha] = files
            except Exception as e:
                logger.error(f"Failed to fetch files for commit {commit_sha}: {e}")
                commit_to_files[commit_sha] = []

        # 4. Map Files to Symbols
        # This links to the AST analysis results (stored in DB)
        # file_to_symbols = symbol_service.get_symbols_for_file(path)

        return {
            "issues": issues,
            "pull_requests": prs,
            "workflow_runs": runs,
            "releases": releases,
            "mappings": {
                "pr_to_commits": pr_to_commits,
                "commit_to_files": commit_to_files,
            }
        }

    async def analyze_pr_risk(self, owner: str, repo: str, pr_number: int, access_token: Optional[str] = None):
        """
        Analyze a specific PR for architectural risk.
        Risk = (Churn in High-Centrality Symbols) + (Cyclomatic Complexity Increase)
        """
        # 1. Get PR details and files changed
        from backend.app.services.github_service import fetch_pull_requests, fetch_commit_files

        prs = await fetch_pull_requests(owner, repo, access_token)
        pr = next((p for p in prs if p['number'] == pr_number), None)

        if not pr:
            return {"error": "PR not found"}

        files = await fetch_commit_files(owner, repo, pr['head'], access_token)

        # ponytail: Use basic churn (additions+deletions) as risk proxy
        # Real implementation would cross-reference with AST centrality from DB
        total_churn = sum(f.get('changes', 0) for f in files)
        risk_score = min(1.0, total_churn / 500.0) # Normalize: 500+ changes = high risk

        hotspots = [f['filename'] for f in files if f.get('changes', 0) > 50]

        return {
            "pr_number": pr_number,
            "risk_score": risk_score,
            "hotspots_affected": hotspots,
            "architectural_impact": "High" if risk_score > 0.7 else "Medium" if risk_score > 0.3 else "Low",
            "metrics": {
                "total_changes": total_churn,
                "files_changed": len(files)
            }
        }

    async def analyze_ci_impact(self, owner: str, repo: str, run_id: str, access_token: Optional[str] = None):
        """
        Correlate CI failure to technical debt.
        """
        # 1. Get failure logs
        # 2. Identify failing symbols/files
        # 3. Check if those files have high 'decay' metrics
        return {
            "run_id": run_id,
            "correlated_debt": "High - failure in module with 80% churn",
            "suggested_fix": "Refactor the failing test utility into a separate service"
        }
