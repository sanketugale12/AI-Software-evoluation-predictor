import React, { createContext, useContext, useReducer, useEffect, type ReactNode, useCallback } from "react";
import { useAuth } from "./AuthContext";
import type {
  WorkspaceState,
  RepositoryDetails,
  RepositoryTree,
  DependencyGraph,
  AnalysisJob,
  AnalysisResults,
  ActivePage,
  TreeNode,
  TreeResponse,
  FileContent,
  BranchInfo,
  RepositoryContext,
} from "@/types";
import { asepClient } from "@/services/api";

async function pollAnalysisJobLocal(
  jobId: string,
  onUpdate: (job: AnalysisJob, results?: AnalysisResults) => void,
  intervalMs: number = 3000,
  maxAttempts: number = 100
): Promise<AnalysisResults> {
  let attempts = 0;
  while (attempts < maxAttempts) {
    const job = await asepClient.getAnalysisJobStatus(jobId);
    onUpdate(job);
    if (job.status === "completed" || job.status === "failed") {
      const results = await asepClient.getAnalysisResults(jobId);
      onUpdate(job, results);
      return results;
    }
    if (job.status === "cancelled") {
      onUpdate(job);
      throw new Error("Analysis cancelled");
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    attempts++;
  }
  throw new Error("Analysis timed out");
}

type Action =
  | { type: "SET_REPO_URL"; payload: string }
  | { type: "SET_REPO_DETAILS"; payload: RepositoryDetails | null }
  | { type: "SET_REPO_TREE"; payload: RepositoryTree | null }
  | { type: "SET_DEPENDENCY_GRAPH"; payload: DependencyGraph | null }
  | { type: "SET_ANALYSIS_JOB"; payload: AnalysisJob | null }
  | { type: "SET_ANALYSIS_RESULTS"; payload: AnalysisResults | null }
  | { type: "SET_ACTIVE_PAGE"; payload: ActivePage }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "SET_USER"; payload: import("@/types").UserResponse | null }
  | { type: "SET_AUTHENTICATED"; payload: boolean }
  | { type: "SET_REPO_CONTEXT"; payload: RepositoryContext | null }
  | { type: "SET_BRANCHES"; payload: BranchInfo[] }
  | { type: "SET_SELECTED_COMMIT"; payload: string }
  | { type: "SET_TREE_AT_COMMIT"; payload: TreeResponse | null }
  | { type: "SET_SELECTED_FILE"; payload: FileContent | null }
  | { type: "SET_FILE_LOADING"; payload: boolean }
  | { type: "SET_SNAPSHOT_SAVING"; payload: boolean }
  | { type: "RESET_WORKSPACE" };

const initialState: WorkspaceState = {
  repoUrl: "",
  repoDetails: null,
  repoTree: null,
  dependencyGraph: null,
  analysisJob: null,
  analysisResults: null,
  activePage: "overview",
  isLoading: false,
  error: null,
  user: null,
  isAuthenticated: false,
  repoContext: null,
  branches: [],
  selectedCommit: "",
  treeAtCommit: null,
  selectedFile: null,
  isFileLoading: false,
  isSnapshotSaving: false,
};

function workspaceReducer(state: WorkspaceState, action: Action): WorkspaceState {
  switch (action.type) {
    case "SET_REPO_URL":
      return { ...state, repoUrl: action.payload };
    case "SET_REPO_DETAILS":
      return { ...state, repoDetails: action.payload };
    case "SET_REPO_TREE":
      return { ...state, repoTree: action.payload };
    case "SET_DEPENDENCY_GRAPH":
      return { ...state, dependencyGraph: action.payload };
    case "SET_ANALYSIS_JOB":
      return { ...state, analysisJob: action.payload };
    case "SET_ANALYSIS_RESULTS":
      return { ...state, analysisResults: action.payload };
    case "SET_ACTIVE_PAGE":
      return { ...state, activePage: action.payload };
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    case "SET_ERROR":
      return { ...state, error: action.payload };
    case "SET_USER":
      return { ...state, user: action.payload };
    case "SET_AUTHENTICATED":
      return { ...state, isAuthenticated: action.payload };
    case "SET_REPO_CONTEXT":
      return { ...state, repoContext: action.payload };
    case "SET_BRANCHES":
      return { ...state, branches: action.payload };
    case "SET_SELECTED_COMMIT":
      return { ...state, selectedCommit: action.payload };
    case "SET_TREE_AT_COMMIT":
      return { ...state, treeAtCommit: action.payload };
    case "SET_SELECTED_FILE":
      return { ...state, selectedFile: action.payload };
    case "SET_FILE_LOADING":
      return { ...state, isFileLoading: action.payload };
    case "SET_SNAPSHOT_SAVING":
      return { ...state, isSnapshotSaving: action.payload };
    case "RESET_WORKSPACE":
      return initialState;
    default:
      return state;
  }
}

interface WorkspaceContextType extends WorkspaceState {
  loadRepository: (url: string) => Promise<void>;
  startAnalysis: () => Promise<void>;
  cancelAnalysis: () => Promise<void>;
  retryAnalysis: () => Promise<void>;
  setActivePage: (page: ActivePage) => void;
  clearError: () => void;
  loadRepositoryContext: (owner: string, repo: string) => Promise<void>;
  loadBranches: (owner: string, repo: string) => Promise<void>;
  selectCommit: (commitSha: string) => Promise<void>;
  loadFile: (node: TreeNode) => Promise<void>;
  clearSelectedFile: () => void;
  createSnapshot: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(workspaceReducer, initialState);
  const { user, isAuthenticated } = useAuth();

  useEffect(() => {
    dispatch({ type: "SET_USER", payload: user });
    dispatch({ type: "SET_AUTHENTICATED", payload: isAuthenticated });
  }, [user, isAuthenticated]);

  // Listen for repo detection from content script
  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.type === "REPO_DETECTED" && message.url) {
        if (isAuthenticated) {
          loadRepository(message.url);
        } else {
          // Store pending repo to load after login
          localStorage.setItem("asep_pending_repo", message.url);
        }
      }
    };

    if (typeof browser !== "undefined" && browser.runtime?.onMessage) {
      browser.runtime.onMessage.addListener(handleMessage);
      return () => browser.runtime.onMessage.removeListener(handleMessage);
    }
  }, [isAuthenticated]);

  // Auto-load pending repo after authentication or on mount
  useEffect(() => {
    if (isAuthenticated) {
      const pendingRepo = localStorage.getItem("asep_pending_repo");
      if (pendingRepo) {
        console.log("ASEP: Loading pending repository:", pendingRepo);
        loadRepository(pendingRepo);
        localStorage.removeItem("asep_pending_repo");
      }
    }
  }, [isAuthenticated]);

  const loadRepository = async (url: string) => {
    dispatch({ type: "SET_REPO_URL", payload: url });
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });
    dispatch({ type: "SET_REPO_DETAILS", payload: null });
    dispatch({ type: "SET_REPO_TREE", payload: null });
    dispatch({ type: "SET_DEPENDENCY_GRAPH", payload: null });
    dispatch({ type: "SET_ANALYSIS_JOB", payload: null });
    dispatch({ type: "SET_ANALYSIS_RESULTS", payload: null });

    try {
      const [details, tree] = await Promise.all([
        asepClient.analyzeRepository(url),
        asepClient.getRepositoryTree(url),
      ]);

      dispatch({ type: "SET_REPO_DETAILS", payload: details });
      dispatch({ type: "SET_REPO_TREE", payload: tree });

      try {
        const graph = await asepClient.fetchDependencyGraph(url);
        dispatch({ type: "SET_DEPENDENCY_GRAPH", payload: graph });
      } catch (graphError) {
        console.warn("Failed to fetch dependency graph:", graphError);
      }
    } catch (err: any) {
      dispatch({ type: "SET_ERROR", payload: err.message || "Failed to load repository" });
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  };

  const loadRepositoryContext = useCallback(async (owner: string, repo: string) => {
    try {
      const context = await asepClient.getRepositoryContext(owner, repo);
      dispatch({ type: "SET_REPO_CONTEXT", payload: context });
      dispatch({ type: "SET_SELECTED_COMMIT", payload: context.default_branch });
      await loadBranches(owner, repo);
    } catch (err: any) {
      console.error("Failed to load repository context:", err);
    }
  }, []);

  const loadBranches = useCallback(async (owner: string, repo: string) => {
    try {
      const response = await asepClient.getRepositoryBranches(owner, repo);
      dispatch({ type: "SET_BRANCHES", payload: response.branches });
    } catch (err: any) {
      console.error("Failed to load branches:", err);
    }
  }, []);

  const selectCommit = useCallback(async (commitSha: string) => {
    if (!state.repoContext) return;
    dispatch({ type: "SET_SELECTED_COMMIT", payload: commitSha });
    dispatch({ type: "SET_FILE_LOADING", payload: true });
    dispatch({ type: "SET_SELECTED_FILE", payload: null });
    try {
      const treeResponse = await asepClient.fetchRepositoryTreeAtCommit(
        state.repoContext.owner,
        state.repoContext.name,
        commitSha
      );
      dispatch({ type: "SET_TREE_AT_COMMIT", payload: treeResponse });
    } catch (err: any) {
      console.error("Failed to load tree at commit:", err);
      dispatch({ type: "SET_TREE_AT_COMMIT", payload: null });
    } finally {
      dispatch({ type: "SET_FILE_LOADING", payload: false });
    }
  }, [state.repoContext]);

  const loadFile = useCallback(async (node: TreeNode) => {
    if (!state.repoContext || !state.selectedCommit) return;
    dispatch({ type: "SET_FILE_LOADING", payload: true });
    try {
      const fileContent = await asepClient.fetchFileContentAtCommit(
        state.repoContext.owner,
        state.repoContext.name,
        node.path,
        state.selectedCommit
      );
      dispatch({ type: "SET_SELECTED_FILE", payload: fileContent });
    } catch (err: any) {
      console.error("Failed to load file:", err);
      dispatch({ type: "SET_SELECTED_FILE", payload: null });
    } finally {
      dispatch({ type: "SET_FILE_LOADING", payload: false });
    }
  }, [state.repoContext, state.selectedCommit]);

  const clearSelectedFile = useCallback(() => {
    dispatch({ type: "SET_SELECTED_FILE", payload: null });
  }, []);

  const createSnapshot = useCallback(async () => {
    if (!state.repoContext || !state.selectedCommit || !state.treeAtCommit) return;
    dispatch({ type: "SET_SNAPSHOT_SAVING", payload: true });
    try {
      const treeJson = state.treeAtCommit.tree_json as Record<string, unknown> | undefined;
      await asepClient.createSnapshot(
        state.repoContext.owner,
        state.repoContext.name,
        state.selectedCommit,
        undefined,
        undefined,
        treeJson
      );
    } catch (err: any) {
      console.error("Failed to create snapshot:", err);
    } finally {
      dispatch({ type: "SET_SNAPSHOT_SAVING", payload: false });
    }
  }, [state.repoContext, state.selectedCommit, state.treeAtCommit]);

  const startAnalysis = async () => {
    if (!state.repoContext) {
      dispatch({ type: "SET_ERROR", payload: "No repository selected" });
      return;
    }
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });
    dispatch({ type: "SET_ANALYSIS_JOB", payload: null });
    dispatch({ type: "SET_ANALYSIS_RESULTS", payload: null });
    try {
      const commitSha = state.selectedCommit || state.repoContext.default_branch;
      const job = await asepClient.createAnalysisJobForRepo(state.repoContext.owner, state.repoContext.name, commitSha);
      dispatch({ type: "SET_ANALYSIS_JOB", payload: job });
      const results = await pollAnalysisJobLocal(
        job.job_id,
        (jobUpdate, resultsUpdate) => {
          dispatch({ type: "SET_ANALYSIS_JOB", payload: jobUpdate });
          if (resultsUpdate) {
            dispatch({ type: "SET_ANALYSIS_RESULTS", payload: resultsUpdate });
          }
        }
      );
      dispatch({ type: "SET_ANALYSIS_RESULTS", payload: results });
    } catch (err: any) {
      dispatch({ type: "SET_ERROR", payload: err.message || "Analysis failed" });
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  };

  const cancelAnalysis = async () => {
    if (!state.analysisJob) return;
    try {
      await asepClient.cancelAnalysisJob(state.analysisJob.job_id);
    } catch (err: any) {
      dispatch({ type: "SET_ERROR", payload: err.message || "Failed to cancel analysis" });
    }
  };

  const retryAnalysis = async () => {
    if (!state.analysisJob) return;
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });
    dispatch({ type: "SET_ANALYSIS_RESULTS", payload: null });
    try {
      const job = await asepClient.retryAnalysisJob(state.analysisJob.job_id);
      dispatch({ type: "SET_ANALYSIS_JOB", payload: job });
      const results = await pollAnalysisJobLocal(
        job.job_id,
        (jobUpdate, resultsUpdate) => {
          dispatch({ type: "SET_ANALYSIS_JOB", payload: jobUpdate });
          if (resultsUpdate) {
            dispatch({ type: "SET_ANALYSIS_RESULTS", payload: resultsUpdate });
          }
        }
      );
      dispatch({ type: "SET_ANALYSIS_RESULTS", payload: results });
    } catch (err: any) {
      dispatch({ type: "SET_ERROR", payload: err.message || "Analysis retry failed" });
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  };

  const setActivePage = (page: ActivePage) => {
    dispatch({ type: "SET_ACTIVE_PAGE", payload: page });
  };

  const clearError = () => {
    dispatch({ type: "SET_ERROR", payload: null });
  };

  return (
    <WorkspaceContext.Provider
      value={{
        ...state,
        loadRepository,
        startAnalysis,
        cancelAnalysis,
        retryAnalysis,
        setActivePage,
        clearError,
        loadRepositoryContext,
        loadBranches,
        selectCommit,
        loadFile,
        clearSelectedFile,
        createSnapshot,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
