import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from backend.app.services.github_service import (
    fetch_pull_requests,
    fetch_issues,
    fetch_workflow_runs,
    fetch_releases,
    fetch_commit_files
)
from backend.app.analyzers.ast_analyzer import MultiLanguageParser
from backend.app.analyzers.dependency_graph import DependencyGraphBuilder
from backend.app.analyzers.arch_intelligence import ArchIntelligence
from backend.app.analyzers.git_history import GitHistoryAnalyzer
from backend.app.analyzers.hotspot_analyzer import HotspotAnalyzer
from backend.app.analyzers.security_analyzer import SecurityAnalyzer
from backend.app.analyzers.secret_detector import SecretDetector

logger = logging.getLogger(__name__)

class IntelligenceService:
    """
    Orchestrates the ASEP Intelligence Pipeline.
    Pipeline: AST -> Graph -> Evolution -> Security -> Consolidation.
    """

    def __init__(self, owner: str, repo: str, access_token: Optional[str] = None):
        self.owner = owner
        self.repo = repo
        self.access_token = access_token

    async def run_full_intelligence_pipeline(self, commit_sha: str) -> Dict[str, Any]:
        """
        Executes the full suite of analyzers and consolidates them into a
        unified intelligence map bound to a specific commit SHA.
        """
        logger.info(f"Running full intelligence pipeline for {self.owner}/{self.repo} @ {commit_sha}")

        try:
            # 1. AST Phase: Extract Symbols and Structure
            # ponytail: In a real scenario, we'd fetch the repo content to disk first
            parser = MultiLanguageParser()
            # For the purpose of this service, we assume a method to get all files at SHA
            # and then parse them.
            symbols = await self._run_ast_phase(commit_sha, parser)

            # 2. Graph Phase: Build Architectural Map
            graph_builder = DependencyGraphBuilder()
            graph_data = await graph_builder.build_graph(self.owner, self.repo, commit_sha, self.access_token)

            intel = ArchIntelligence(graph_data['graph'])
            arch_metrics = {
                "centrality": intel.calculate_centrality(),
                "circular_dependencies": intel.find_circular_dependencies(),
                "connectivity": intel.calculate_connectivity()
            }

            # 3. Evolution Phase: Git Churn & Hotspots
            git_analyzer = GitHistoryAnalyzer(self.owner, self.repo)
            churn_data = await git_analyzer.analyze_churn(commit_sha)

            hotspot_analyzer = HotspotAnalyzer()
            hotspots = hotspot_analyzer.identify_hotspots(churn_data, arch_metrics['centrality'])

            # 4. Security Phase: Vulnerabilities & Secrets
            security_analyzer = SecurityAnalyzer()
            security_findings = await security_analyzer.scan(self.owner, self.repo, commit_sha, self.access_token)

            secret_detector = SecretDetector()
            secret_findings = await secret_detector.scan(self.owner, self.repo, commit_sha, self.access_token)

            # 5. Consolidation: Merge into Intelligence Map
            return {
                "commit_sha": commit_sha,
                "architecture": {
                    "nodes": graph_data['nodes'],
                    "edges": graph_data['edges'],
                    "metrics": arch_metrics
                },
                "evolution": {
                    "hotspots": hotspots,
                    "churn": churn_data
                },
                "security": {
                    "findings": security_findings + secret_findings
                },
                "symbols": symbols
            }

        except Exception as e:
            logger.error(f"Intelligence pipeline failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Intelligence pipeline error: {str(e)}")

    async def _run_ast_phase(self, commit_sha: str, parser: MultiLanguageParser) -> List[Dict[str, Any]]:
        """
        Helper to run AST extraction across the repository at a specific commit.
        """
        # This is a simplified placeholder. A full implementation would:
        # 1. Get the file tree at commit_sha.
        # 2. Fetch content for each supported file.
        # 3. Run parser.parse() on each.
        return [] # Implementation details would follow a similar pattern to fetch_repository_tree_at_commit
