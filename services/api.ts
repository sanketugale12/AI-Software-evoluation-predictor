import type {
  RepositoryDetails,
  RepositoryTree,
  DependencyGraph,
  AnalysisJob,
  AnalysisResults,
  AnalysisData,
  RepositoryContext,
  BranchesResponse,
  LatestCommitResponse,
  RepositoryListResponse,
  SyncRepositoryResponse,
  AuthStatusResponse,
  UserResponse,
  TreeNode,
  TreeResponse,
  FileContent,
  Snapshot,
  SnapshotListResponse,
  AnalysisJobListResponse,
} from "@/types";

export type { Snapshot, SnapshotListResponse };

const API_URL = "http://127.0.0.1:8001";

let currentUserId: string | null = null;

export function setCurrentUserId(userId: string | null) {
  currentUserId = userId;
}

export function getCurrentUserId(): string | null {
  return currentUserId;
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (currentUserId) {
    headers["X-User-ID"] = currentUserId;
  }
  return headers;
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error: ${response.status} - ${errorText}`);
  }

  return response.json();
}

// Auth APIs
export async function getAuthStatus(): Promise<AuthStatusResponse> {
  return fetchJson<AuthStatusResponse>(`${API_URL}/api/auth/me`);
}

export async function logout(): Promise<{ success: boolean; message: string }> {
  return fetchJson(`${API_URL}/api/auth/logout`, { method: "POST" });
}

export function getGitHubLoginUrl(): string {
  return `${API_URL}/api/auth/github/login`;
}

// Repository APIs (legacy & popup)
export async function analyzeRepository(url: string): Promise<RepositoryDetails> {
  return fetchRepositoryDetails(url);
}

export async function getRepositoryTree(url: string): Promise<string[]> {
  const tree = await fetchRepositoryTree(url);
  return tree.files;
}

export async function fetchRepositoryDetails(url: string): Promise<RepositoryDetails> {
  return fetchJson<RepositoryDetails>(`${API_URL}/api/repository`, {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function fetchRepositoryTree(url: string): Promise<RepositoryTree> {
  const encodedUrl = encodeURIComponent(url);
  return fetchJson<RepositoryTree>(`${API_URL}/api/repository/tree?url=${encodedUrl}`);
}

// Dependency Graph API
export async function fetchDependencyGraph(url: string): Promise<DependencyGraph> {
  return fetchJson<DependencyGraph>(`${API_URL}/api/analysis/dependencies`, {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

// Analysis Job APIs
export async function createAnalysisJob(url: string): Promise<AnalysisJob> {
  return fetchJson<AnalysisJob>(`${API_URL}/api/analysis`, {
    method: "POST",
    body: JSON.stringify({ repository_url: url }),
  });
}

export async function getAnalysisJobStatus(jobId: string): Promise<AnalysisJob> {
  return fetchJson<AnalysisJob>(`${API_URL}/api/analysis/${jobId}`);
}

export async function getAnalysisResults(jobId: string): Promise<AnalysisResults> {
  return fetchJson<AnalysisResults>(`${API_URL}/api/analysis/${jobId}/results`);
}

export async function createAnalysisJobForRepo(
  owner: string,
  repo: string,
  commitSha?: string
): Promise<AnalysisJob> {
  return fetchJson<AnalysisJob>(`${API_URL}/api/analysis`, {
    method: "POST",
    body: JSON.stringify({
      repository_url: `https://github.com/${owner}/${repo}`,
      commit_sha: commitSha,
    }),
  });
}

export async function cancelAnalysisJob(jobId: string): Promise<{ success: boolean }> {
  return fetchJson(`${API_URL}/api/analysis/${jobId}`, {
    method: "DELETE",
  });
}

export async function retryAnalysisJob(jobId: string): Promise<AnalysisJob> {
  return fetchJson<AnalysisJob>(`${API_URL}/api/analysis/${jobId}/retry`, {
    method: "POST",
  });
}

// Polling helper
export async function pollAnalysisJob(
  jobId: string,
  onUpdate: (job: AnalysisJob, results?: AnalysisResults) => void,
  intervalMs: number = 3000,
  maxAttempts: number = 100
): Promise<AnalysisResults> {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const job = await getAnalysisJobStatus(jobId);
    onUpdate(job);

    if (job.status === "completed" || job.status === "failed") {
      const results = await getAnalysisResults(jobId);
      onUpdate(job, results);
      return results;
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    attempts++;
  }

  throw new Error("Analysis timed out");
}

// Authenticated Repository APIs
export async function listUserRepositories(): Promise<RepositoryListResponse> {
  return fetchJson<RepositoryListResponse>(`${API_URL}/api/repositories`);
}

export async function getRepositoryContext(
  owner: string,
  repo: string
): Promise<RepositoryContext> {
  return fetchJson<RepositoryContext>(`${API_URL}/api/repositories/${owner}/${repo}`);
}

export async function getRepositoryBranches(
  owner: string,
  repo: string
): Promise<BranchesResponse> {
  return fetchJson<BranchesResponse>(`${API_URL}/api/repositories/${owner}/${repo}/branches`);
}

export async function getLatestCommit(
  owner: string,
  repo: string,
  branch?: string
): Promise<LatestCommitResponse> {
  const url = branch
    ? `${API_URL}/api/repositories/${owner}/${repo}/commits/latest?branch=${encodeURIComponent(branch)}`
    : `${API_URL}/api/repositories/${owner}/${repo}/commits/latest`;
  return fetchJson<LatestCommitResponse>(url);
}

export async function refreshRepository(
  owner: string,
  repo: string,
  force: boolean = false
): Promise<SyncRepositoryResponse> {
  return fetchJson<SyncRepositoryResponse>(`${API_URL}/api/repositories/${owner}/${repo}/refresh`, {
    method: "POST",
    body: JSON.stringify({ force }),
  });
}

// Health check
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}

// File Explorer APIs (Phase 4)
export async function fetchRepositoryTreeAtCommit(
  owner: string,
  repo: string,
  commitSha: string
): Promise<TreeResponse> {
  return fetchJson<TreeResponse>(
    `${API_URL}/api/repositories/${owner}/${repo}/tree?commit_sha=${encodeURIComponent(commitSha)}`
  );
}

export async function fetchFileContentAtCommit(
  owner: string,
  repo: string,
  path: string,
  commitSha: string
): Promise<FileContent> {
  return fetchJson<FileContent>(
    `${API_URL}/api/repositories/${owner}/${repo}/file?path=${encodeURIComponent(path)}&commit_sha=${encodeURIComponent(commitSha)}`
  );
}

export async function createSnapshot(
  owner: string,
  repo: string,
  commitSha: string,
  commitMessage?: string,
  commitDate?: string,
  treeJson?: Record<string, unknown>
): Promise<Snapshot> {
  return fetchJson<Snapshot>(`${API_URL}/api/repositories/${owner}/${repo}/snapshots`, {
    method: "POST",
    body: JSON.stringify({ commit_sha: commitSha, commit_message: commitMessage, commit_date: commitDate, tree_json: treeJson }),
  });
}

export async function listSnapshots(
  owner: string,
  repo: string,
  limit: number = 50
): Promise<SnapshotListResponse> {
  return fetchJson<SnapshotListResponse>(
    `${API_URL}/api/repositories/${owner}/${repo}/snapshots?limit=${limit}`
  );
}

export async function getLatestSnapshot(
  owner: string,
  repo: string
): Promise<Snapshot> {
  return fetchJson<Snapshot>(
    `${API_URL}/api/repositories/${owner}/${repo}/snapshots/latest`
  );
}

export async function getSnapshot(
  owner: string,
  repo: string,
  snapshotId: string
): Promise<Snapshot> {
  return fetchJson<Snapshot>(
    `${API_URL}/api/repositories/${owner}/${repo}/snapshots/${snapshotId}`
  );
}

export async function deleteSnapshot(
  owner: string,
  repo: string,
  snapshotId: string
): Promise<{ success: boolean; message: string }> {
  return fetchJson(`${API_URL}/api/repositories/${owner}/${repo}/snapshots/${snapshotId}`, {
    method: "DELETE",
  });
}

// Architecture Intelligence APIs
export async function fetchArchitectureMetrics(repoId: string): Promise<any> {
  return fetchJson<any>(`${API_URL}/api/architecture/metrics`, {
    method: "POST",
    body: JSON.stringify({ repo_id: repoId }),
  });
}

export async function fetchSymbolRecords(repoId: string, filePath?: string): Promise<any[]> {
  return fetchJson<any[]>(`${API_URL}/api/architecture/symbols`, {
    method: "POST",
    body: JSON.stringify({ repo_id: repoId, file_path: filePath }),
  });
}
