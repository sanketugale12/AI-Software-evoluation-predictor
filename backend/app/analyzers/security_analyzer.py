import json
import subprocess


def normalize_findings(raw_results: dict):
    normalized = []
    results = raw_results.get("results", [])

    for finding in results:
        normalized.append({
            "rule_id": finding.get("check_id"),
            "severity": finding.get("extra", {}).get("severity", "WARNING"),
            "file": finding.get("path"),
            "line": finding.get("start", {}).get("line"),
            "message": finding.get("extra", {}).get("message", "Review this finding"),
            "source": "semgrep"
        })

    return {"findings": normalized}


def run_security_scan(repo_path: str):
    result = subprocess.run(
        [
            "semgrep",
            "scan",
            "--config",
            "p/python",
            "--json",
            repo_path,
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr)

    raw_data = json.loads(result.stdout)
    return normalize_findings(raw_data)
