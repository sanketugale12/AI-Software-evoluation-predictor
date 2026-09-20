"""Maintainability metrics using Radon Maintainability Index (MI)."""
import json
import subprocess
import os
from typing import Any


ANALYZER_VERSION = "1.0.0"


def run_maintainability_analysis(repo_path: str) -> dict[str, Any]:
    """
    Run Radon Maintainability Index (MI) analysis.
    MI scores range from 0-100, with higher being more maintainable.
    """
    try:
        result = subprocess.run(
            ["radon", "mi", repo_path, "-s", "-j"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            return {"metrics": {}, "error": result.stderr[:500]}

        raw_data = json.loads(result.stdout)
        return normalize_maintainability(raw_data)

    except FileNotFoundError:
        return {"metrics": {}, "error": "radon not installed"}
    except subprocess.TimeoutExpired:
        return {"metrics": {}, "error": "Maintainability analysis timed out"}
    except json.JSONDecodeError:
        return {"metrics": {}, "error": "Failed to parse radon MI output"}


def normalize_maintainability(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize radon MI output into a standard format."""
    metrics = {}
    low_maintainability = []

    for file_path, data in raw_data.items():
        if isinstance(data, dict):
            mi_score = data.get("mi", 0)
            rank = data.get("rank", "A")

            metrics[file_path] = {
                "mi_score": mi_score,
                "rank": rank,
                "is_low_maintainability": mi_score < 20 or rank in ("C", "D"),
            }

            if mi_score < 20 or rank in ("C", "D"):
                low_maintainability.append({
                    "file": file_path,
                    "mi_score": mi_score,
                    "rank": rank,
                    "severity": "high" if rank == "D" else "medium",
                    "title": f"Low maintainability: {file_path}",
                    "description": f"Maintainability Index score is {mi_score:.1f} (rank {rank}). This file may be difficult to maintain.",
                    "recommendation": "Refactor to reduce complexity, improve naming, and add documentation.",
                })

    return {
        "metrics": metrics,
        "low_maintainability_files": low_maintainability,
        "total_files": len(metrics),
        "average_mi": sum(m["mi_score"] for m in metrics.values()) / len(metrics) if metrics else 0,
    }


def get_maintainability_findings(maintainability_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert maintainability data into unified findings."""
    findings = []
    for item in maintainability_data.get("low_maintainability_files", []):
        findings.append({
            "id": f"maintainability-{item['file']}",
            "rule_id": "low-maintainability",
            "category": "maintainability",
            "subcategory": "low_mi",
            "severity": item["severity"],
            "confidence": 0.85,
            "title": item["title"],
            "description": item["description"],
            "file": item["file"],
            "line": None,
            "recommendation": item["recommendation"],
            "analyzer_version": ANALYZER_VERSION,
            "cwe": "CWE-1066",
            "owasp": None,
            "metadata": {
                "mi_score": item["mi_score"],
                "rank": item["rank"],
                "source": "radon-mi",
            },
        })
    return findings