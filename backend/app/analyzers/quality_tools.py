"""Language-specific quality tools: ESLint for JS/TS, Bandit for Python."""
import json
import subprocess
import os
from typing import Any


ANALYZER_VERSION = "1.0.0"


def run_eslint(repo_path: str, config_path: str = None) -> dict[str, Any]:
    """
    Run ESLint on JavaScript/TypeScript files.
    """
    cmd = ["npx", "eslint", "--format", "json"]
    if config_path:
        cmd.extend(["--config", config_path])
    cmd.append(repo_path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # ESLint returns exit code 1 when linting issues are found
        if result.returncode not in (0, 1):
            return {"findings": [], "error": result.stderr[:500]}

        raw_data = json.loads(result.stdout) if result.stdout else []
        return normalize_eslint_findings(raw_data)

    except FileNotFoundError:
        return {"findings": [], "error": "eslint not installed"}
    except subprocess.TimeoutExpired:
        return {"findings": [], "error": "ESLint scan timed out"}
    except json.JSONDecodeError:
        return {"findings": [], "error": "Failed to parse ESLint output"}


def normalize_eslint_findings(raw_data: list) -> dict[str, Any]:
    """Normalize ESLint output into standard findings format."""
    findings = []
    for file_result in raw_data:
        file_path = file_result.get("filePath", "unknown")
        messages = file_result.get("messages", [])

        for msg in messages:
            severity = "error" if msg.get("severity") == 2 else "warning"
            findings.append({
                "id": f"eslint-{file_path}-{msg.get('line', 0)}-{msg.get('ruleId', 'unknown')}",
                "rule_id": msg.get("ruleId"),
                "category": "quality",
                "subcategory": "lint",
                "severity": severity,
                "confidence": 0.95,
                "title": msg.get("message", "ESLint issue"),
                "description": msg.get("message", "ESLint issue detected"),
                "file": file_path,
                "line": msg.get("line"),
                "recommendation": msg.get("message", "Fix the linting issue"),
                "analyzer_version": ANALYZER_VERSION,
                "cwe": None,
                "owasp": None,
                "metadata": {
                    "node_type": msg.get("nodeType"),
                    "source": "eslint",
                },
            })

    return {"findings": findings}


def run_bandit(repo_path: str) -> dict[str, Any]:
    """
    Run Bandit security linter on Python files.
    """
    try:
        result = subprocess.run(
            [
                "bandit",
                "-r",
                repo_path,
                "-f",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Bandit returns exit code 1 when issues are found
        if result.returncode not in (0, 1):
            return {"findings": [], "error": result.stderr[:500]}

        raw_data = json.loads(result.stdout) if result.stdout else {}
        return normalize_bandit_findings(raw_data)

    except FileNotFoundError:
        return {"findings": [], "error": "bandit not installed"}
    except subprocess.TimeoutExpired:
        return {"findings": [], "error": "Bandit scan timed out"}
    except json.JSONDecodeError:
        return {"findings": [], "error": "Failed to parse Bandit output"}


def normalize_bandit_findings(raw_data: dict) -> dict[str, Any]:
    """Normalize Bandit output into standard findings format."""
    findings = []
    results = raw_data.get("results", [])

    for item in results:
        severity = item.get("issue_severity", "LOW").lower()
        findings.append({
            "id": f"bandit-{item.get('filename', 'unknown')}-{item.get('line_number', 0)}-{item.get('test_id', 'unknown')}",
            "rule_id": item.get("test_id"),
            "category": "security",
            "subcategory": "bandit",
            "severity": severity,
            "confidence": item.get("issue_confidence", "LOW").lower(),
            "title": item.get("issue_text", "Bandit security issue"),
            "description": item.get("issue_text", "Bandit security issue detected"),
            "file": item.get("filename", "unknown"),
            "line": item.get("line_number"),
            "recommendation": item.get("issue_text", "Fix the security issue"),
            "analyzer_version": ANALYZER_VERSION,
            "cwe": f"CWE-{item['test_id'].split('-')[0]}" if item.get("test_id") else None,
            "owasp": None,
            "metadata": {
                "more_info": item.get("more_info_url"),
                "source": "bandit",
            },
        })

    return {"findings": findings}