from ..services.repository_service import clone_repository
from ..services.ingestion_service import (
    IngestionConfig,
    IngestionError,
    validate_repository_size,
    cleanup_workspace,
    monitor_disk_usage,
)
from ..analyzers.technical_debt import run_complexity_analysis
from ..analyzers.git_history import analyze_git_history
from ..analyzers.security_analyzer import run_security_scan
from ..analyzers.hotspot_analyzer import analyze_hotspots
from ..analyzers.evolution_analyzer import EvolutionAnalyzer
from ..analyzers.maintainability import run_maintainability_analysis
from ..analyzers.arch_intelligence import analyze_architecture
from ..analyzers.ast_analyzer import analyze_ast
from typing import Callable, Optional
import logging
import time
import signal
import threading
import os

logger = logging.getLogger(__name__)


class AnalysisTimeoutError(Exception):
    """Raised when analysis exceeds the maximum execution time."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise AnalysisTimeoutError("Analysis execution time exceeded")


def analyze_repository(
    repository_url: str,
    job_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str, str], None]] = None,
    cancellation_check: Optional[Callable[[], bool]] = None,
    commit_sha: Optional[str] = None,
    config: Optional[IngestionConfig] = None,
):
    """
    Orchestrates the full analysis pipeline for a given repository.

    Args:
        repository_url: URL of the repository to analyze
        job_id: Optional job ID for tracking
        progress_callback: Optional callback(step_name, message) for progress updates
        cancellation_check: Optional function that returns True if job should be cancelled
        commit_sha: Optional commit SHA to pin analysis to (Phase 6)
        config: Optional ingestion configuration for resource limits (Phase 6)
    """
    def report_progress(step: str, message: str):
        if progress_callback:
            progress_callback(step, message)

    def check_cancelled() -> bool:
        if cancellation_check:
            return cancellation_check()
        return False

    if config is None:
        config = IngestionConfig()

    # Set up timeout handler (Unix only)
    timeout_thread = None
    if hasattr(signal, 'SIGALRM'):
        def timeout_thread_func():
            time.sleep(config.max_execution_time_seconds)
            if not getattr(analyze_repository, '_completed', False):
                # We can't easily interrupt from another thread, so we'll check in cancellation_check
                pass
        timeout_thread = threading.Thread(target=timeout_thread_func, daemon=True)
        timeout_thread.start()

    try:
        # Clone repository with commit pinning
        report_progress("cloning", "Cloning repository...")
        temp_dir = clone_repository(repository_url, commit_sha)

        # If using new ingestion service, stats are attached to temp_dir
        stats = getattr(temp_dir, 'stats', None)

        report_progress("cloning", "Repository cloned successfully")

        try:
            repo_path = temp_dir.name

            # Validate repository size if stats available
            if stats:
                report_progress("validation", f"Validating repository: {stats.file_count} files, {stats.total_size_mb:.1f}MB")
            else:
                # Legacy validation
                stats = validate_repository_size(repo_path, config)
                report_progress("validation", f"Repository validated: {stats.file_count} files, {stats.total_size_mb:.1f}MB")

            # Check for cancellation
            if check_cancelled():
                raise Exception("Analysis cancelled by user")

            # Step 1: Complexity Analysis
            report_progress("complexity", "Running complexity analysis...")
            complexity = run_complexity_analysis(repo_path)

            if check_cancelled():
                raise Exception("Analysis cancelled by user")

            # Step 1b: Maintainability Analysis
            report_progress("maintainability", "Running maintainability analysis...")
            maintainability = run_maintainability_analysis(repo_path)

            if check_cancelled():
                raise Exception("Analysis cancelled by user")

            # Monitor disk usage
            if not monitor_disk_usage(repo_path, config.max_disk_usage_mb):
                raise Exception(f"Disk usage exceeded maximum: {config.max_disk_usage_mb}MB")

            # Step 2: Git History Analysis
            report_progress("git_history", "Analyzing git history...")
            try:
                history = analyze_git_history(repo_path)
            except Exception as e:
                logger.error(f"Git history analysis failed: {e}")
                history = None

            if check_cancelled():
                raise Exception("Analysis cancelled by user")

            # Step 3: Security Analysis
            report_progress("security", "Running security scan...")
            security = run_security_scan(repo_path)

            if check_cancelled():
                raise Exception("Analysis cancelled by user")

            # Step 3b: Architecture Analysis
            report_progress("architecture", "Analyzing architecture...")
            all_symbols = []
            for root, _, files in os.walk(repo_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    try:
                        all_symbols.extend(analyze_ast(full_path))
                    except Exception as e:
                        logger.debug(f"AST analysis failed for {file}: {e}")

            architecture = analyze_architecture(all_symbols)

            if check_cancelled():
                raise Exception("Analysis cancelled by user")

            # Step 4: Evolution & Hotspot Analysis
            report_progress("hotspots", "Identifying evolution hotspots...")

            # Initialize evolution analyzer
            evo_analyzer = EvolutionAnalyzer()

            # Correlate Git, Complexity, and Security data
            if history:
                centrality_map = {path: 0.1 for path in history["file_changes"]}
                hotspots = evo_analyzer.analyze(
                    git_data=history,
                    arch_data=centrality_map,
                    security_data=security
                )
            else:
                hotspots = None

            if check_cancelled():
                raise Exception("Analysis cancelled by user")

            # Step 5: Technical Debt Analysis
            report_progress("technical_debt", "Calculating technical debt...")
            technical_debt = calculate_technical_debt(complexity, history)

            report_progress("completed", "All analysis steps completed")

            # Mark as completed for timeout thread
            analyze_repository._completed = True

            return {
                "version": 1,
                "commit_sha": stats.commit_sha if stats else None,
                "branch": stats.branch if stats else None,
                "repository_stats": {
                    "file_count": stats.file_count if stats else 0,
                    "total_size_mb": stats.total_size_mb if stats else 0,
                    "largest_file_mb": stats.largest_file_bytes / (1024 * 1024) if stats else 0,
                    "excluded_size_mb": stats.excluded_size_bytes / (1024 * 1024) if stats else 0,
                    "clone_duration_seconds": stats.clone_duration_seconds if stats else 0,
                } if stats else None,
                "complexity": complexity,
                "maintainability": maintainability,
                "architecture": architecture,
                "history": history,
                "security": security,
                "hotspots": hotspots,
                "technical_debt": technical_debt,
            }

        finally:
            # Ensure the temporary directory is cleaned up regardless of success or failure
            cleanup_workspace(temp_dir)
            analyze_repository._completed = True

    except AnalysisTimeoutError:
        raise Exception(f"Analysis timed out after {config.max_execution_time_seconds} seconds")
    except IngestionError as e:
        raise Exception(f"Repository ingestion failed: {e.message}")


def calculate_technical_debt(complexity: dict, history: Optional[dict]) -> dict:
    """
    Calculate technical debt metrics from complexity and history data.
    """
    total_complexity = 0
    file_count = 0
    high_complexity_files = 0

    for file_path, blocks in complexity.items():
        file_count += 1
        for block in blocks:
            c = block.get("complexity", 0)
            total_complexity += c
            if c > 10:  # Threshold for high complexity
                high_complexity_files += 1

    avg_complexity = total_complexity / file_count if file_count > 0 else 0

    # Get churn from history
    total_churn = history.get("metrics", {}).get("total_churn", 0) if history else 0
    commit_frequency = history.get("metrics", {}).get("commit_frequency", 0) if history else 0

    # Simple technical debt score
    debt_score = (avg_complexity * 0.5) + (high_complexity_files * 2) + (total_churn * 0.01) + (commit_frequency * 0.1)

    return {
        "total_files": file_count,
        "total_complexity": total_complexity,
        "average_complexity": round(avg_complexity, 2),
        "high_complexity_files": high_complexity_files,
        "total_churn": total_churn,
        "commit_frequency": commit_frequency,
        "debt_score": round(debt_score, 2),
        "risk_level": "High" if debt_score > 50 else "Medium" if debt_score > 20 else "Low",
        "history_available": history is not None
    }