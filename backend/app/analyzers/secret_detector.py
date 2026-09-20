"""Secret detection analyzer using regex patterns."""
import re
import os
from typing import Any


ANALYZER_VERSION = "1.0.0"

# Common secret patterns with their severity and description
SECRET_PATTERNS = [
    {
        "id": "aws-access-key",
        "pattern": r"(?:aws_access_key_id|AWS_ACCESS_KEY_ID|aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{20,40})['\"]?",
        "severity": "critical",
        "description": "AWS Access Key ID or Secret Access Key detected",
        "recommendation": "Remove the key and rotate it immediately. Use IAM roles or environment variables instead.",
    },
    {
        "id": "github-token",
        "pattern": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}",
        "severity": "critical",
        "description": "GitHub personal access token detected",
        "recommendation": "Remove the token and revoke it in GitHub settings. Use GitHub Apps for fine-grained permissions.",
    },
    {
        "id": "private-key",
        "pattern": r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "severity": "critical",
        "description": "Private key detected in source code",
        "recommendation": "Remove the private key. Store secrets in a secure vault, never in source code.",
    },
    {
        "id": "api-key-generic",
        "pattern": r"(?:api[_-]?key|apikey|API[_-]?KEY)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{16,})['\"]?",
        "severity": "high",
        "description": "Generic API key detected",
        "recommendation": "Remove the API key and rotate it. Use environment variables or a secrets manager.",
    },
    {
        "id": "password",
        "pattern": r"(?:password|passwd|pwd)\s*[=:]\s*['\"]?([^'\"\s]{8,})['\"]?",
        "severity": "high",
        "description": "Password detected in source code",
        "recommendation": "Remove the hardcoded password. Use environment variables or a secrets manager.",
    },
    {
        "id": "jwt-token",
        "pattern": r"eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+",
        "severity": "high",
        "description": "JWT token detected in source code",
        "recommendation": "Remove the JWT token. Use secure token storage and rotation.",
    },
    {
        "id": "slack-token",
        "pattern": r"xox[baprs]-[A-Za-z0-9\-]+",
        "severity": "high",
        "description": "Slack token detected",
        "recommendation": "Remove the token and revoke it in Slack settings.",
    },
    {
        "id": "stripe-key",
        "pattern": r"(?:sk|pk)_(?:test|live)_[A-Za-z0-9]{24,}",
        "severity": "high",
        "description": "Stripe API key detected",
        "recommendation": "Remove the key and rotate it in the Stripe dashboard.",
    },
    {
        "id": "google-api-key",
        "pattern": r"AIza[0-9A-Za-z\-_]{35}",
        "severity": "high",
        "description": "Google API key detected",
        "recommendation": "Remove the key and restrict it in the Google Cloud Console.",
    },
    {
        "id": "sendgrid-key",
        "pattern": r"SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}",
        "severity": "high",
        "description": "SendGrid API key detected",
        "recommendation": "Remove the key and rotate it in the SendGrid dashboard.",
    },
    {
        "id": "slack-webhook",
        "pattern": r"https://hooks\.slack\.com/services/T[A-Za-z0-9_\-]+/B[A-Za-z0-9_\-]+/[A-Za-z0-9_\-]+",
        "severity": "medium",
        "description": "Slack webhook URL detected",
        "recommendation": "Remove the webhook URL and regenerate it in Slack.",
    },
    {
        "id": "generic-secret",
        "pattern": r"(?:secret|token|key)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{16,})['\"]?",
        "severity": "medium",
        "description": "Potential secret detected",
        "recommendation": "Review this value. If it's a secret, remove it and use environment variables.",
    },
]


def detect_secrets(file_path: str, source_code: str) -> list[dict[str, Any]]:
    """Scan source code for secrets using regex patterns."""
    findings = []
    lines = source_code.split("\n")

    for pattern_def in SECRET_PATTERNS:
        pattern = pattern_def["pattern"]
        try:
            for match in re.finditer(pattern, source_code, re.MULTILINE):
                line_num = source_code[:match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                # Redact the actual secret value
                redacted = _redact_match(match.group(0))

                findings.append({
                    "id": f"secret-{pattern_def['id']}-{file_path}-{line_num}",
                    "rule_id": pattern_def["id"],
                    "category": "secret",
                    "subcategory": "hardcoded_secret",
                    "severity": pattern_def["severity"],
                    "confidence": 0.7,
                    "title": pattern_def["description"],
                    "description": f"Found in {file_path} at line {line_num}",
                    "file": file_path,
                    "line": line_num,
                    "recommendation": pattern_def["recommendation"],
                    "analyzer_version": ANALYZER_VERSION,
                    "cwe": "CWE-798" if "password" in pattern_def["id"] else "CWE-526",
                    "owasp": "A07:2021 - Identification and Authentication Failures" if "password" in pattern_def["id"] else "A05:2021 - Security Misconfiguration",
                    "metadata": {
                        "pattern_id": pattern_def["id"],
                        "redacted_value": redacted,
                        "line_content": line_content[:200],
                        "source": "secret-detector",
                    },
                })
        except re.error:
            continue

    return findings


def _redact_match(value: str) -> str:
    """Redact a sensitive value, showing only the first/last few characters."""
    if len(value) <= 8:
        return "***"
    return value[:4] + "***" + value[-4:]


def scan_secrets(files: dict[str, str]) -> list[dict[str, Any]]:
    """Scan multiple files for secrets."""
    all_findings = []
    for file_path, source_code in files.items():
        findings = detect_secrets(file_path, source_code)
        all_findings.extend(findings)
    return all_findings