"""Unified findings aggregator that combines all analyzer outputs."""
from typing import Any
from .schemas.findings import (
    UnifiedFinding,
    UnifiedFindingsResponse,
    FindingCategory,
    Severity,
    FindingStatus,
    Evidence,
)


ANALYZER_VERSIONS = {
    "security": "1.0.0",
    "dependency": "1.0.0",
    "secret": "1.0.0",
    "complexity": "1.0.0",
    "maintainability": "1.0.0",
    "duplication": "1.0.0",
    "architecture": "1.0.0",
    "quality": "1.0.0",
    "hotspot": "1.0.0",
    "technical_debt": "1.0.0",
}

SCHEMA_VERSION = "1.0.0"


def _normalize_severity(severity: str) -> str:
    """Normalize various severity formats to standard levels."""
    severity_lower = str(severity).lower()
    mapping = {
        "critical": "critical",
        "high": "high",
        "error": "high",
        "warning": "medium",
        "medium": "medium",
        "warn": "medium",
        "low": "low",
        "info": "info",
        "informational": "info",
    }
    return mapping.get(severity_lower, "info")


def _normalize_confidence(confidence: Any) -> float:
    """Normalize confidence to 0.0-1.0 scale."""
    if confidence is None:
        return 0.5
    try:
        conf = float(confidence)
        if conf > 1.0:
            return conf / 100.0
        return max(0.0, min(1.0, conf))
    except (ValueError, TypeError):
        return 0.5


def _normalize_category(category: str) -> str:
    """Normalize category to standard values."""
    category_lower = str(category).lower()
    mapping = {
        "security": "security",
        "dependency": "dependency",
        "secret": "secret",
        "complexity": "complexity",
        "maintainability": "maintainability",
        "duplication": "duplication",
        "architecture": "architecture",
        "quality": "quality",
        "hotspot": "hotspot",
        "technical_debt": "technical_debt",
        "tech_debt": "technical_debt",
    }
    return mapping.get(category_lower, "quality")


def _create_evidence(finding: dict[str, Any]) -> Evidence:
    """Create an Evidence object from a finding dict."""
    return Evidence(
        file=finding.get("file", "unknown"),
        line=finding.get("line"),
        column=finding.get("column"),
        snippet=finding.get("snippet"),
        context=finding.get("metadata", {}).get("context"),
    )


def normalize_finding(finding: dict[str, Any], analyzer_version: str = None) -> UnifiedFinding:
    """Convert a raw finding dict into a UnifiedFinding."""
    category = _normalize_category(finding.get("category", "quality"))
    analyzer_ver = analyzer_version or ANALYZER_VERSIONS.get(category, "1.0.0")

    return UnifiedFinding(
        id=finding.get("id", f"finding-{hash(str(finding))}"),
        category=FindingCategory(category),
        subcategory=finding.get("subcategory"),
        severity=Severity(_normalize_severity(finding.get("severity", "info"))),
        confidence=_normalize_confidence(finding.get("confidence", 0.5)),
        title=finding.get("title", "Untitled Finding"),
        description=finding.get("description", finding.get("title", "")),
        evidence=_create_evidence(finding),
        recommendation=finding.get("recommendation", "Review and address this finding"),
        analyzer_version=analyzer_ver,
        rule_id=finding.get("rule_id"),
        cwe=finding.get("cwe"),
        owasp=finding.get("owasp"),
        status=FindingStatus.OPEN,
        metadata=finding.get("metadata", {}),
    )


def deduplicate_findings(findings: list[UnifiedFinding]) -> tuple[list[UnifiedFinding], int]:
    """
    Deduplicate findings based on file, line, rule_id, and category.
    Returns (deduplicated_findings, removed_count).
    """
    seen = set()
    deduplicated = []
    removed = 0

    for finding in findings:
        # Create a key based on file, line, rule_id, and category
        key = (
            finding.evidence.file,
            finding.evidence.line,
            finding.rule_id,
            finding.category.value,
        )

        if key in seen:
            removed += 1
            continue

        seen.add(key)
        deduplicated.append(finding)

    return deduplicated, removed


def aggregate_findings(all_findings: list[dict[str, Any]]) -> UnifiedFindingsResponse:
    """
    Aggregate all raw findings from all analyzers into a unified response.
    """
    normalized = []
    for finding in all_findings:
        try:
            nf = normalize_finding(finding)
            normalized.append(nf)
        except Exception:
            # Skip findings that fail normalization
            continue

    # Deduplicate
    deduplicated, removed = deduplicate_findings(normalized)

    # Calculate counts
    by_category = {}
    by_severity = {}
    analyzer_versions = {}

    for finding in deduplicated:
        cat = finding.category.value
        sev = finding.severity.value
        by_category[cat] = by_category.get(cat, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1
        analyzer_versions[cat] = finding.analyzer_version

    return UnifiedFindingsResponse(
        version=SCHEMA_VERSION,
        analyzer_versions=analyzer_versions,
        total_count=len(deduplicated),
        findings=deduplicated,
        by_category=by_category,
        by_severity=by_severity,
        deduplicated_count=removed if removed > 0 else None,
    )


def findings_to_dict(findings: list[UnifiedFinding]) -> list[dict[str, Any]]:
    """Convert UnifiedFinding objects to dicts for JSON serialization."""
    result = []
    for f in findings:
        result.append({
            "id": f.id,
            "category": f.category.value,
            "subcategory": f.subcategory,
            "severity": f.severity.value,
            "confidence": f.confidence,
            "title": f.title,
            "description": f.description,
            "evidence": {
                "file": f.evidence.file,
                "line": f.evidence.line,
                "column": f.evidence.column,
                "snippet": f.evidence.snippet,
                "context": f.evidence.context,
            },
            "recommendation": f.recommendation,
            "analyzer_version": f.analyzer_version,
            "rule_id": f.rule_id,
            "cwe": f.cwe,
            "owasp": f.owasp,
            "status": f.status.value,
            "metadata": f.metadata,
        })
    return result