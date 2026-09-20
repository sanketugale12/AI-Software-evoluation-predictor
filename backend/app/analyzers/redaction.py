"""Sensitive value redaction utilities."""
import re
from typing import Any


# Patterns for values that should be redacted
SENSITIVE_PATTERNS = [
    # Keys and tokens
    (r'(?:api[_-]?key|apikey|API[_-]?KEY)\s*[=:]\s*[\'"]([^\'"]+)[\'"]', "API_KEY"),
    (r'(?:secret|SECRET)\s*[=:]\s*[\'"]([^\'"]+)[\'"]', "SECRET"),
    (r'(?:password|passwd|pwd|PASSWORD)\s*[=:]\s*[\'"]([^\'"]+)[\'"]', "PASSWORD"),
    (r'(?:token|TOKEN)\s*[=:]\s*[\'"]([^\'"]+)[\'"]', "TOKEN"),
    # AWS
    (r'AKIA[0-9A-Z]{16}', "AWS_ACCESS_KEY"),
    (r'(?i)aws_secret_access_key\s*[=:]\s*[\'"]([^\'"]+)[\'"]', "AWS_SECRET_KEY"),
    # GitHub
    (r'ghp_[A-Za-z0-9]{36}', "GITHUB_TOKEN"),
    (r'gho_[A-Za-z0-9]{36}', "GITHUB_OATH_TOKEN"),
    # Private keys
    (r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', "PRIVATE_KEY"),
    # JWT
    (r'eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+', "JWT_TOKEN"),
    # Connection strings
    (r'(?:postgres|postgresql|mysql|mongodb|redis)://[^:\s]+:[^@\s]+@[^\s]+', "CONNECTION_STRING"),
    # Generic high-entropy strings
    (r'[\'"]([A-Za-z0-9_\-]{32,})[\'"]', "HIGH_ENTROPY_STRING"),
]


def redact_sensitive_value(value: str) -> str:
    """Redact a sensitive value, showing only partial characters."""
    if not value or len(value) <= 4:
        return "***"
    # Show first 2 and last 2 characters
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def redact_text(text: str) -> str:
    """Redact all sensitive values found in a text string."""
    redacted = text
    for pattern, _ in SENSITIVE_PATTERNS:
        redacted = re.sub(
            pattern,
            lambda m: redact_sensitive_value(m.group(0)) if m.lastindex is None else f"{m.group(1) if m.lastindex >= 1 else ''}",
            redacted,
        )
    return redacted


def redact_dict(data: Any) -> Any:
    """Recursively redact sensitive values in a dictionary or list."""
    if isinstance(data, dict):
        return {k: redact_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_dict(item) for item in data]
    elif isinstance(data, str):
        return redact_text(data)
    return data


def redact_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive values in a finding dict."""
    return redact_dict(finding)