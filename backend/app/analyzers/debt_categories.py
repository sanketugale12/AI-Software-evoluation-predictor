"""Debt categories and remediation guidance."""
from typing import Any


class DebtCategory:
    """Categories of technical debt with remediation guidance."""

    CATEGORIES = {
        "security": {
            "name": "Security Debt",
            "description": "Debt related to security vulnerabilities, misconfigurations, or insecure practices",
            "severity_weight": 1.5,
            "remediation_priority": 1,
        },
        "dependency": {
            "name": "Dependency Debt",
            "description": "Debt from outdated or vulnerable third-party dependencies",
            "severity_weight": 1.3,
            "remediation_priority": 2,
        },
        "secret": {
            "name": "Secret Exposure Debt",
            "description": "Debt from hardcoded secrets, keys, or credentials in source code",
            "severity_weight": 1.5,
            "remediation_priority": 1,
        },
        "complexity": {
            "name": "Complexity Debt",
            "description": "Debt from overly complex functions or classes that are hard to maintain",
            "severity_weight": 1.0,
            "remediation_priority": 4,
        },
        "maintainability": {
            "name": "Maintainability Debt",
            "description": "Debt from code that is difficult to read, understand, or modify",
            "severity_weight": 0.9,
            "remediation_priority": 5,
        },
        "duplication": {
            "name": "Duplication Debt",
            "description": "Debt from repeated code that violates the DRY principle",
            "severity_weight": 0.8,
            "remediation_priority": 6,
        },
        "architecture": {
            "name": "Architecture Debt",
            "description": "Debt from poor architectural design, coupling, or circular dependencies",
            "severity_weight": 1.1,
            "remediation_priority": 3,
        },
        "quality": {
            "name": "Quality Debt",
            "description": "Debt from code style violations, missing tests, or poor practices",
            "severity_weight": 0.7,
            "remediation_priority": 7,
        },
        "hotspot": {
            "name": "Hotspot Debt",
            "description": "Debt from frequently changed, complex code that is prone to bugs",
            "severity_weight": 1.2,
            "remediation_priority": 3,
        },
    }

    REMEDIATION_GUIDANCE = {
        "security": [
            "Run a security audit and fix all identified vulnerabilities",
            "Apply security patches and updates",
            "Implement security best practices (OWASP guidelines)",
            "Add input validation and output encoding",
        ],
        "dependency": [
            "Update vulnerable packages to the latest secure versions",
            "Use dependency scanning in CI/CD pipeline",
            "Consider replacing deprecated packages",
            "Pin dependency versions to prevent unexpected updates",
        ],
        "secret": [
            "Remove all hardcoded secrets from source code",
            "Rotate any exposed credentials immediately",
            "Use environment variables or a secrets manager",
            "Add secret detection to pre-commit hooks",
        ],
        "complexity": [
            "Refactor complex functions into smaller, single-responsibility functions",
            "Apply the Single Responsibility Principle",
            "Extract complex conditionals into well-named functions",
            "Consider design patterns like Strategy or State",
        ],
        "maintainability": [
            "Improve naming and add documentation",
            "Break down large files into smaller, focused modules",
            "Add unit tests to cover complex logic",
            "Apply consistent code formatting",
        ],
        "duplication": [
            "Extract common code into shared functions or modules",
            "Apply the DRY (Don't Repeat Yourself) principle",
            "Use composition over inheritance where appropriate",
            "Consider using higher-order functions or mixins",
        ],
        "architecture": [
            "Decouple tightly coupled components",
            "Apply dependency inversion principle",
            "Break circular dependencies by introducing interfaces",
            "Consider microservices for large monolithic applications",
        ],
        "quality": [
            "Fix linting and style violations",
            "Add comprehensive unit and integration tests",
            "Implement consistent code formatting",
            "Establish code review processes",
        ],
        "hotspot": [
            "Refactor high-churn, complex code for readability",
            "Add comprehensive tests for hotspot areas",
            "Increase code review coverage for frequently modified files",
            "Consider architectural changes to reduce coupling",
        ],
    }

    @classmethod
    def get_category_info(cls, category: str) -> dict[str, Any]:
        """Get information about a debt category."""
        return cls.CATEGORIES.get(category, {
            "name": category,
            "description": "Unknown debt category",
            "severity_weight": 1.0,
            "remediation_priority": 99,
        })

    @classmethod
    def get_remediation_guidance(cls, category: str) -> list[str]:
        """Get remediation guidance for a debt category."""
        return cls.REMEDIATION_GUIDANCE.get(category, [
            "Review the issue and apply appropriate fixes",
            "Follow team coding standards and best practices",
        ])

    @classmethod
    def calculate_debt_score(cls, findings: list[dict[str, Any]]) -> float:
        """Calculate a weighted debt score from findings."""
        score = 0.0
        for finding in findings:
            category = finding.get("category", "unknown")
            severity = finding.get("severity", "info")
            info = cls.get_category_info(category)

            # Severity multiplier
            severity_mult = {
                "critical": 5.0,
                "high": 3.0,
                "medium": 1.5,
                "low": 0.5,
                "info": 0.1,
            }.get(severity, 1.0)

            score += info["severity_weight"] * severity_mult

        return round(score, 2)

    @classmethod
    def categorize_findings(cls, findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group findings by debt category."""
        categorized = {}
        for finding in findings:
            category = finding.get("category", "unknown")
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(finding)
        return categorized