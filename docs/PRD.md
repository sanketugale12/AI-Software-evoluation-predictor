# Product Requirements Document (PRD) - ASEP

## 1. Executive Summary
**ASEP (Architectural Software Evolution Predictor)** is an AI-powered analysis tool designed to identify technical debt, architectural decay, and predict future hotspots in large-scale software repositories. Unlike static analysis tools that only report *what* is wrong, ASEP focuses on *where* the codebase is likely to fail or become unmaintainable in the future.

### Vision
To move software maintenance from reactive ("fixing bugs") to predictive ("preventing decay").

## 2. Target Audience
- **CTOs & Engineering Managers**: To identify high-risk modules and allocate refactoring resources.
- **Software Architects**: To visualize architectural erosion and enforce structural boundaries.
- **Lead Developers**: To pinpoint "hotspots" where changes frequently introduce bugs.

## 3. Core Value Propositions
- **Predictive Hotspot Detection**: Combines AST analysis with commit history to find modules with high "churn" and high "complexity".
- **Technical Debt Quantification**: Categorizes debt into actionable types (e.g., God Objects, Shotgun Surgery).
- **Evolutionary Tracking**: Snapshots the repository state to show how technical debt grows or shrinks over time.
- **Contextual AI Insights**: Provides LLM-driven suggestions for refactoring based on the actual code structure.

## 4. Functional Requirements

### 4.1 Repository Integration
- **GitHub Integration**: OAuth2 authentication and repository scanning.
- **Commit Pinning**: Ability to analyze a specific commit SHA rather than just the default branch.
- **Snapshotting**: Save a "frozen" state of the repository for longitudinal analysis.

### 4.2 Analysis Engine
- **Structural Analysis**: Generation of dependency graphs and module boundaries.
- **Complexity Metrics**: Cyclomatic complexity, cognitive complexity, and depth of inheritance.
- **Churn Analysis**: Integration with git logs to identify files with frequent changes.
- **Hotspot Mapping**: Intersection of high churn and high complexity.
- **Debt Categorization**: Identification of smells (God Classes, Feature Envy, etc.).

### 4.3 Prediction Model
- **Decay Prediction**: Probability that a module will require significant refactoring in the next $N$ commits.
- **Risk Scoring**: A composite score (0-100) for every file/module.

### 4.4 User Interface (IDE Extension)
- **Visual Heatmaps**: Overlaying risk scores directly on the file explorer.
- **Dependency Visualizer**: Interactive graph of module relationships.
- **Debt Dashboard**: Summary of total technical debt and top 5 "at-risk" files.
- **AI Refactoring Assistant**: Chat interface that understands the architectural context.

## 5. Non-Functional Requirements
- **Performance**: Analysis of a medium-sized repo (<100k LOC) should complete within 5 minutes.
- **Scalability**: Support for repositories up to 1M LOC.
- **Accuracy**: Prediction model must be grounded in empirical software engineering metrics (e.g., Adam Opel's hotspot theory).
- **Security**: GitHub tokens must be encrypted at rest; strictly read-only access to repositories.

## 6. User Stories
| ID | User | Requirement | Goal |
|----|------|-------------|------|
| US1 | Architect | I want to see a dependency graph | To find circular dependencies |
| US2 | Lead Dev | I want a list of files with high churn and complexity | To prioritize refactoring |
| US3 | Manager | I want to see if technical debt decreased after a sprint | To measure refactoring ROI |
| US4 | Developer | I want AI to explain *why* this file is a hotspot | To understand the decay pattern |

## 7. Acceptance Criteria
- [ ] User can authenticate via GitHub and load a repository.
- [ ] System generates a risk score for every file in the repo.
- [ ] System identifies at least 3 types of architectural smells.
- [ ] User can compare two snapshots of the same repo.
- [ ] IDE extension highlights high-risk files in the file tree.
