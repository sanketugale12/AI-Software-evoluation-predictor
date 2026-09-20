"""Unified findings schema for all analysis results."""
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class FindingCategory(str, Enum):
    """Categories of findings across all analyzers."""
    SECURITY = "security"
    DEPENDENCY = "dependency"
    SECRET = "secret"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    DUPLICATION = "duplication"
    ARCHITECTURE = "architecture"
    HOTSPOT = "hotspot"
    QUALITY = "quality"
    TECHNICAL_DEBT = "technical_debt"


class Severity(str, Enum):
    """Standard severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, Enum):
    """Status of a finding."""
    OPEN = "open"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED_RISK = "accepted_risk"


class Evidence(BaseModel):
    """Evidence supporting a finding."""
    file: str = Field(..., description="File path where evidence was found")
    line: Optional[int] = Field(None, description="Line number (1-indexed)")
    column: Optional[int] = Field(None, description="Column number")
    snippet: Optional[str] = Field(None, description="Code snippet from the location")
    context: Optional[dict[str, Any]] = Field(None, description="Additional context data")


class UnifiedFinding(BaseModel):
    """A unified finding from any analyzer."""
    id: str = Field(..., description="Unique finding ID")
    category: FindingCategory = Field(..., description="Category of the finding")
    subcategory: Optional[str] = Field(None, description="Sub-category or rule type")
    severity: Severity = Field(..., description="Severity level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    title: str = Field(..., description="Short title")
    description: str = Field(..., description="Detailed description")
    evidence: Evidence = Field(..., description="Supporting evidence")
    recommendation: str = Field(..., description="Remediation guidance")
    analyzer_version: str = Field(..., description="Version of the analyzer that produced this finding")
    rule_id: Optional[str] = Field(None, description="Rule or check identifier")
    cwe: Optional[str] = Field(None, description="CWE identifier if applicable")
    owasp: Optional[str] = Field(None, description="OWASP category if applicable")
    status: FindingStatus = Field(FindingStatus.OPEN, description="Current status")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UnifiedFindingsResponse(BaseModel):
    """Response containing all unified findings."""
    version: str = Field(..., description="Schema version")
    analyzer_versions: dict[str, str] = Field(default_factory=dict, description="Versions of all analyzers")
    total_count: int = Field(..., description="Total number of findings")
    findings: list[UnifiedFinding] = Field(default_factory=list, description="All findings")
    by_category: dict[str, int] = Field(default_factory=dict, description="Count by category")
    by_severity: dict[str, int] = Field(default_factory=dict, description="Count by severity")
    deduplicated_count: Optional[int] = Field(None, description="Number of findings removed by deduplication")