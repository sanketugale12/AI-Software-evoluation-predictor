# Project Phases - ASEP

This document defines the roadmap for ASEP. Each phase must be fully completed, verified, and documented before moving to the next.

## Phase 0: Product Foundation
**Goal**: Establish the "Source of Truth".
- Define PRD, Tech Spec, Architecture, and Design.
- Define API contracts and Database schemas.
- Create implementation tracker.
- **Deliverables**: Complete `docs/` directory.

## Phase 1: Core Infrastructure & Auth
**Goal**: Secure access and repository loading.
- GitHub OAuth2 integration.
- Repository metadata fetching.
- User profile management.
- Basic Extension $\leftrightarrow$ Backend bridge.

## Phase 2: Structural Analysis Engine
**Goal**: Extract the "What" of the code.
- AST-based structure extraction.
- Dependency graph generation.
- Module boundary detection.
- Basic complexity metrics (Cyclomatic/Cognitive).

## Phase 3: Temporal Analysis & Hotspots
**Goal**: Extract the "When" and "How" of the code.
- Git commit history mining.
- Churn calculation per file.
- Hotspot Algorithm: $\text{Risk} = f(\text{Complexity}, \text{Churn})$.
- Risk score mapping to file tree.

## Phase 4: Architectural Smell Detection
**Goal**: Identify "Why" it's decaying.
- Implementation of smell detectors (God Objects, Shotgun Surgery, Circular Deps).
- Debt categorization engine.
- Debt quantification (estimated refactoring effort).

## Phase 5: Evolutionary Tracking (Snapshots)
**Goal**: Track change over time.
- Repository snapshotting mechanism.
- Snapshot comparison logic.
- "Evolution" view in the UI.

## Phase 6: AI-Powered Insights
**Goal**: Provide actionable advice.
- Architectural context windowing for LLMs.
- AI-driven refactoring suggestions.
- Debt explanation engine.
- Integration of AI into the IDE extension.

## Phase 7: Final Polish & Validation
**Goal**: Product-ready stability.
- Performance optimization for large repos.
- Comprehensive E2E testing.
- Security audit.
- Final documentation and release.
