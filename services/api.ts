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

const API_URL = "http://127.0.0.1:8000";

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

class AsepClient {
  async getAuthStatus(): Promise<AuthStatusResponse> {
    return fetchJson<AuthStatusResponse>(`${API_URL}/api/auth/me`);
  }

  async logout(): Promise<{ success: boolean; message: string }> {
    return fetchJson(`${API_URL}/api/auth/logout`, { method: "POST" });
  }

  getGitHubLoginUrl(): string {
    return `${API_URL}/api/auth/github/login`;
  }

  async analyzeRepository(url: string): Promise<RepositoryDetails> {
    return fetchJson<RepositoryDetails>(`${API_URL}/api/repository`, {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  }

  async getRepositoryTree(url: string): Promise<RepositoryTree> {
    const encodedUrl = encodeURIComponent(url);
    return fetchJson<RepositoryTree>(`${API_URL}/api/repository/tree?url=${encodedUrl}`);
  }

  async fetchDependencyGraph(url: string): Promise<DependencyGraph> {
    return fetchJson<DependencyGraph>(`${API_URL}/api/analysis/dependencies`, {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  }

  async createAnalysisJob(url: string): Promise<AnalysisJob> {
    return fetchJson<AnalysisJob>(`${API_URL}/api/analysis`, {
      method: "POST",
      body: JSON.stringify({ repository_url: url }),
    });
  }

  async getAnalysisJobStatus(jobId: string): Promise<AnalysisJob> {
    return fetchJson<AnalysisJob>(`${API_URL}/api/analysis/${jobId}`);
  }

  async getAnalysisResults(jobId: string): Promise<AnalysisResults> {
    return fetchJson<AnalysisResults>(`${API_URL}/api/analysis/${jobId}/results`);
  }

  async createAnalysisJobForRepo(owner: string, repo: string, commitSha?: string): Promise<AnalysisJob> {
    return fetchJson<AnalysisJob>(`${API_URL}/api/analysis`, {
      method: "POST",
      body: JSON.stringify({
        repository_url: `https://github.com/${owner}/${repo}`,
        commit_sha: commitSha,
      }),
    });
  }

  async cancelAnalysisJob(jobId: string): Promise<{ success: boolean }> {
    return fetchJson(`${API_URL}/api/analysis/${jobId}`, {
      method: "DELETE",
    });
  }

  async retryAnalysisJob(jobId: string): Promise<AnalysisJob> {
    return fetchJson<AnalysisJob>(`${API_URL}/api/analysis/${jobId}/retry`, {
      method: "POST",
    });
  }

  async listUserRepositories(): Promise<RepositoryListResponse> {
    return fetchJson<RepositoryListResponse>(`${API_URL}/api/repositories`);
  }

  async getRepositoryContext(owner: string, repo: string): Promise<RepositoryContext> {
    return fetchJson<RepositoryContext>(`${API_URL}/api/repositories/${owner}/${repo}`);
  }

  async getRepositoryBranches(owner: string, repo: string): Promise<BranchesResponse> {
    return fetchJson<BranchesResponse>(`${API_URL}/api/repositories/${owner}/${repo}/branches`);
  }

  async getLatestCommit(owner: string, repo: string, branch?: string): Promise<LatestCommitResponse> {
    const url = branch
      ? `${API_URL}/api/repositories/${owner}/${repo}/commits/latest?branch=${encodeURIComponent(branch)}`
      : `${API_URL}/api/repositories/${owner}/${repo}/commits/latest`;
    return fetchJson<LatestCommitResponse>(url);
  }

  async refreshRepository(owner: string, repo: string, force: boolean = false): Promise<SyncRepositoryResponse> {
    return fetchJson<SyncRepositoryResponse>(`${API_URL}/api/repositories/${owner}/${repo}/refresh`, {
      method: "POST",
      body: JSON.stringify({ force }),
    });
  }

  async fetchRepositoryTreeAtCommit(owner: string, repo: string, commitSha: string): Promise<TreeResponse> {
    return fetchJson<TreeResponse>(
      `${API_URL}/api/repositories/${owner}/${repo}/tree?commit_sha=${encodeURIComponent(commitSha)}`
    );
  }

  async fetchFileContentAtCommit(owner: string, repo: string, path: string, commitSha: string): Promise<FileContent> {
    return fetchJson<FileContent>(
      `${API_URL}/api/repositories/${owner}/${repo}/file?path=${encodeURIComponent(path)}&commit_sha=${encodeURIComponent(commitSha)}`
    );
  }

  async createSnapshot(owner: string, repo: string, commitSha: string, commitMessage?: string, commitDate?: string, treeJson?: Record<string, unknown>): Promise<Snapshot> {
    return fetchJson<Snapshot>(`${API_URL}/api/repositories/${owner}/${repo}/snapshots`, {
      method: "POST",
      body: JSON.stringify({ commit_sha: commitSha, commit_message: commitMessage, commit_date: commitDate, tree_json: treeJson }),
    });
  }

  async listSnapshots(owner: string, repo: string, limit: number = 50): Promise<SnapshotListResponse> {
    return fetchJson<SnapshotListResponse>(
      `${API_URL}/api/repositories/${owner}/${repo}/snapshots?limit=${limit}`
    );
  }

  async getLatestSnapshot(owner: string, repo: string): Promise<Snapshot> {
    return fetchJson<Snapshot>(`${API_URL}/api/repositories/${owner}/${repo}/snapshots/latest`);
  }

  async getSnapshot(owner: string, repo: string, snapshotId: string): Promise<Snapshot> {
    return fetchJson<Snapshot>(`${API_URL}/api/repositories/${owner}/${repo}/snapshots/${snapshotId}`);
  }

  async deleteSnapshot(owner: string, repo: string, snapshotId: string): Promise<{ success: boolean; message: string }> {
    return fetchJson(`${API_URL}/api/repositories/${owner}/${repo}/snapshots/${snapshotId}`, {
      method: "DELETE",
    });
  }

  async fetchArchitectureMetrics(repoId: string): Promise<any> {
    return fetchJson<any>(`${API_URL}/api/architecture/metrics`, {
      method: "POST",
      body: JSON.stringify({ repo_id: repoId }),
    });
  }

  async fetchSymbolRecords(repoId: string, filePath?: string): Promise<any[]> {
    return fetchJson<any[]>(`${API_URL}/api/architecture/symbols`, {
      method: "POST",
      body: JSON.stringify({ repo_id: repoId, file_path: filePath }),
    });
  }

  async compareAnalyses(id1: string, id2: string): Promise<any> {
    return fetchJson<any>(`${API_URL}/api/analysis/compare?id1=${id1}&id2=${id2}`);
  }

  async checkBackendHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/health`, { method: "GET" });
      return response.ok;
    } catch {
      return false;
    }
  }
}

export const asepClient = new AsepClient();

