# System Architecture - ASEP

## 1. High-Level Overview
ASEP follows a decoupled, asynchronous architecture to handle the computationally expensive task of analyzing large software repositories without blocking the user interface.

### Architecture Diagram (Conceptual)
`[Frontend: VSCode/Browser Extension] <-> [API Gateway: FastAPI] <-> [Async Task Queue: Celery/Redis] <-> [Analysis Engine: AST/Git/ML] <-> [Storage: PostgreSQL/S3]`

## 2. Component Breakdown

### 2.1 Frontend (Client)
- **Technology**: React, TypeScript, WXT (Web Extension Framework).
- **Responsibilities**:
    - User authentication (OAuth flow).
    - Visualization of hotspots and dependency graphs.
    - Triggering analysis jobs and polling for status.
    - Displaying AI-driven refactoring suggestions.
- **State Management**: `WorkspaceContext` (React Context) for repository and job state.

### 2.2 API Layer (Backend)
- **Technology**: Python, FastAPI.
- **Responsibilities**:
    - Managing repository metadata and user profiles.
    - Coordinating analysis job lifecycles (create, cancel, retry).
    - Serving analysis results and snapshots.
    - Proxying requests to the AI/ML services.

### 2.3 Analysis Engine (Worker)
- **Technology**: Python, Celery, Redis.
- **Analysis Pipeline**:
    1. **Cloning/Fetching**: Securely fetching the repo at a specific SHA.
    2. **AST Extraction**: Parsing code into Abstract Syntax Trees (AST) to extract structure.
    3. **Git Mining**: Analyzing commit history for churn and authorship.
    4. **Metric Calculation**: Computing complexity and coupling metrics.
    5. **Prediction Logic**: Applying the hotspot algorithm (Complexity $\times$ Churn).
    6. **Result Aggregation**: Formatting the data for the frontend.

### 2.4 Data Persistence
- **PostgreSQL**: Stores users, repository metadata, analysis job history, and structured results.
- **S3/Object Storage**: Stores large-scale snapshots (JSON dumps of the repo state).
- **Redis**: Used as the Celery broker and for temporary caching of analysis status.

## 3. Data Flow

### 3.1 Analysis Lifecycle
1. **Request**: User clicks "Start Analysis" $\to$ Frontend calls `/api/analysis/create`.
2. **Queue**: FastAPI creates an `AnalysisJob` record in DB $\to$ Enqueues task to Celery.
3. **Execution**: Celery worker executes the pipeline $\to$ Periodically updates `job.progress`.
4. **Completion**: Worker writes final results to `AnalysisJob.result` $\to$ Sets status to `completed`.
5. **Retrieval**: Frontend polls `/api/analysis/status` $\to$ Once completed, fetches `/api/analysis/results`.

### 3.2 Snapshot Comparison
1. **Creation**: User triggers snapshot $\to$ System saves the current analysis result as a `RepositorySnapshot`.
2. **Diffing**: User selects two snapshots $\to$ Backend computes the delta in risk scores and architectural smells.
3. **Visualization**: Frontend renders the "Evolution" view (e.g., "File X risk increased by 20%").

## 4. Technology Stack
| Layer | Technology | Reason |
|---|---|---|
| **Frontend** | React + TS | Industry standard for complex UIs. |
| **Extension** | WXT | Simplifies cross-browser extension development. |
| **Backend** | FastAPI | High performance, native async support, auto-docs. |
| **Task Queue** | Celery + Redis | Robust handling of long-running analysis tasks. |
| **Database** | PostgreSQL | Relational integrity for complex analysis metadata. |
| **Analysis** | Python AST/GitPython | Best-in-class libraries for code and git analysis. |
| **AI** | Claude/GPT-4 | High-reasoning capabilities for architectural advice. |

## 5. Key Constraints
- **Stateless API**: The API layer must remain stateless to allow horizontal scaling.
- **Read-Only Repo Access**: The system must never write to the analyzed repositories.
- **Async-First**: No analysis operation should happen within the request-response cycle.
