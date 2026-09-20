// Shared TypeScript interfaces for ASEP workspace

export interface RepositoryDetails {
  name: string;
  description: string | null;
  language: string | null;
  stars: number;
  forks: number;
  default_branch: string;
  size: number;
  updated_at: string;
  is_private?: boolean;
}

export interface RepositoryTree {
  files: string[];
}

// File Explorer Types (Phase 4)
export interface TreeNode {
  path: string;
  mode: string;
  type: 'blob' | 'tree';
  sha: string;
  size?: number;
  language?: string;
  is_binary: boolean;
  is_generated: boolean;
  is_ignored: boolean;
}

export interface TreeResponse {
  sha: string;
  tree: TreeNode[];
  total_count: number;
  truncated: boolean;
  tree_json?: Record<string, unknown>;
}

export interface FileContent {
  path: string;
  sha: string;
  size: number;
  encoding: 'base64' | 'utf-8';
  content?: string;
  content_base64?: string;
  language?: string;
  is_binary: boolean;
  is_generated: boolean;
  is_ignored: boolean;
}

export interface FileMetadata {
  path: string;
  name: string;
  extension: string;
  size: number;
  size_formatted: string;
  language: string | null;
  is_binary: boolean;
  is_generated: boolean;
  is_ignored: boolean;
  last_modified?: string;
}

export interface Snapshot {
  id: string;
  github_id: number;
  owner: string;
  name: string;
  commit_sha: string;
  commit_message: string | null;
  commit_date: string | null;
  tree_json: Record<string, unknown>;
  total_files: number;
  total_directories: number;
  total_size: number;
  created_at: string;
}

export interface SnapshotListResponse {
  snapshots: Snapshot[];
}

export interface DependencyNode {
  id: string;
  label?: string;
  type?: string;
}

export interface DependencyEdge {
  source: string;
  target: string;
  type?: string;
}

export interface DependencyGraph {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
}

// Analysis Job Types
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'queued' | 'cancelling';

export interface AnalysisProgress {
  current_step: string;
  total_steps: number;
  step_number: number;
  message: string;
}

export interface AnalysisJob {
  job_id: string;
  status: JobStatus;
  created_at?: string;
  progress?: AnalysisProgress;
  started_at?: string;
  completed_at?: string;
  version?: number;
  retry_count?: number;
  cancelled?: boolean;
  commit_sha?: string; // Phase 6: Commit SHA for pinned analysis
}

export interface AnalysisJobListResponse {
  jobs: AnalysisJob[];
  total: number;
}

export interface RepositoryStats {
  file_count: number;
  total_size_mb: number;
  largest_file_mb: number;
  excluded_size_mb: number;
  clone_duration_seconds: number;
}

export interface AnalysisResults {
  job_id: string;
  status: JobStatus;
  results: AnalysisData | null;
  error_message: string | null;
}

export interface AnalysisData {
  complexity?: ComplexityData;
  history?: GitHistoryData;
  hotspots?: HotspotData[];
  security?: SecurityData;
  technical_debt?: TechnicalDebtData;
  commit_sha?: string; // Phase 6: Commit SHA for pinned analysis
  branch?: string;
  repository_stats?: RepositoryStats;
}

export interface ComplexityData {
  [filePath: string]: ComplexityBlock[];
}

export interface ComplexityBlock {
  type: string;
  rank: string;
  complexity: number;
  lineno: number;
  endline: number;
  name: string;
  classname?: string;
  closures?: Closure[];
}

export interface Closure {
  type: string;
  rank: string;
  complexity: number;
  lineno: number;
  endline: number;
  name: string;
}

export interface GitHistoryData {
  total_commits: number;
  commits: Commit[];
  file_changes: FileChanges;
  metrics: GitMetrics;
}

export interface Commit {
  hash: string;
  message: string;
  author: string;
  date: string;
}

export interface FileChanges {
  [filePath: string]: FileChangeData;
}

export interface FileChangeData {
  commits: number;
  added_lines: number;
  deleted_lines: number;
  complexity: number;
  hotspot_score: number;
}

export interface GitMetrics {
  commit_frequency: number;
  contributor_count: number;
  recent_activity: number;
  total_churn: number;
}

export interface HotspotData {
  file: string;
  complexity: number;
  changes: number;
  churn: number;
  score: number;
  status: 'Normal' | 'Monitor' | 'Review';
}

export interface SecurityData {
  findings: SecurityFinding[];
}

export interface SecurityFinding {
  rule_id: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  file: string;
  line: number | null;
  message: string;
  source: string;
}

export interface TechnicalDebtData {
  total_files: number;
  total_complexity: number;
  average_complexity: number;
  high_complexity_files: number;
  total_churn: number;
  commit_frequency: number;
  debt_score: number;
  risk_level: 'High' | 'Medium' | 'Low';
}

// Auth Types
export interface UserResponse {
  id: string;
  github_id: string;
  username: string;
  email: string | null;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuthStatusResponse {
  authenticated: boolean;
  user: UserResponse | null;
}

// Repository Context Types
export interface BranchInfo {
  name: string;
  commit_sha: string;
  protected: boolean;
}

export interface RepositoryContext {
  id: string;
  github_id: number;
  full_name: string;
  owner: string;
  name: string;
  description: string | null;
  default_branch: string;
  is_private: boolean;
  language: string | null;
  stars: number;
  forks: number;
  size: number;
  latest_commit_sha: string | null;
  latest_commit_message: string | null;
  latest_commit_date: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepositoryListResponse {
  repositories: RepositoryContext[];
}

export interface BranchesResponse {
  branches: BranchInfo[];
  default_branch: string;
}

export interface LatestCommitResponse {
  sha: string;
  message: string;
  author: string;
  date: string;
  url: string;
}

export interface SyncRepositoryResponse {
  success: boolean;
  message: string;
  repository: RepositoryContext | null;
}

// API Response Types
export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

// UI State Types
export type ActivePage = 'overview' | 'files' | 'architecture' | 'evolution' | 'security' | 'assistant';

export interface WorkspaceState {
  repoUrl: string;
  repoDetails: RepositoryDetails | null;
  repoTree: RepositoryTree | null;
  dependencyGraph: DependencyGraph | null;
  analysisJob: AnalysisJob | null;
  analysisResults: AnalysisResults | null;
  activePage: ActivePage;
  isLoading: boolean;
  error: string | null;

  // Auth state
  user: UserResponse | null;
  isAuthenticated: boolean;

  // File explorer state
  repoContext: RepositoryContext | null;
  branches: BranchInfo[];
  selectedCommit: string;
  treeAtCommit: TreeResponse | null;
  selectedFile: FileContent | null;
  isFileLoading: boolean;
  isSnapshotSaving: boolean;
}