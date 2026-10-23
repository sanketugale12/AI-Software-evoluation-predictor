"use client";

import React, { useState, useCallback } from "react";
import { Download, Database, Loader2, CheckCircle, AlertCircle, Trash2, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWorkspace } from "@/context/WorkspaceContext";
import { asepClient } from "@/services/api";
import type { Snapshot, RepositoryContext } from "@/types";

interface SnapshotActionsProps {
  className?: string;
}

export function SnapshotActions({ className }: SnapshotActionsProps) {
  const { repoContext, selectedCommit, treeAtCommit } = useWorkspace();
  const [isSaving, setIsSaving] = useState(false);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [showSnapshots, setShowSnapshots] = useState(false);
  const [isLoadingSnapshots, setIsLoadingSnapshots] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  const loadSnapshots = useCallback(async () => {
    if (!repoContext) return;

    setIsLoadingSnapshots(true);
    try {
      const response = await asepClient.listSnapshots(repoContext.owner, repoContext.name);
      setSnapshots(response.snapshots);
    } catch (err) {
      console.error("Failed to load snapshots:", err);
    } finally {
      setIsLoadingSnapshots(false);
    }
  }, [repoContext]);

  const handleSaveSnapshot = useCallback(async () => {
    if (!repoContext || !selectedCommit || !treeAtCommit) return;

    setIsSaving(true);
    setSaveStatus("idle");
    setSaveError(null);

    try {
      // Get commit message from latest commit if available
      let commitMessage: string | undefined;
      let commitDate: string | undefined;

      // Try to get commit details from the tree response or we could fetch separately
      // For now, we'll save with the commit SHA and tree

      const treeJson = treeAtCommit.tree_json as Record<string, unknown> | undefined;

      await asepClient.createSnapshot(
        repoContext.owner,
        repoContext.name,
        selectedCommit,
        commitMessage,
        commitDate,
        treeJson
      );

      setSaveStatus("success");
      // Refresh snapshots list
      await loadSnapshots();
    } catch (err: any) {
      setSaveStatus("error");
      setSaveError(err.message || "Failed to save snapshot");
    } finally {
      setIsSaving(false);
      // Reset status after 3 seconds
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  }, [repoContext, selectedCommit, treeAtCommit, loadSnapshots]);

  // Load snapshots when component mounts or repoContext changes
  React.useEffect(() => {
    if (repoContext) {
      loadSnapshots();
    }
  }, [repoContext, loadSnapshots]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatSha = (sha: string) => sha.slice(0, 8);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {/* Save Snapshot Button */}
      <button
        onClick={handleSaveSnapshot}
        disabled={isSaving || !repoContext || !treeAtCommit}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 bg-background border border-input rounded-md text-sm",
          "hover:bg-accent transition-colors",
          "disabled:opacity-50 disabled:cursor-not-allowed"
        )}
        title="Save repository snapshot at current commit"
      >
        {isSaving ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : saveStatus === "success" ? (
          <CheckCircle className="w-4 h-4 text-green-500" />
        ) : saveStatus === "error" ? (
          <AlertCircle className="w-4 h-4 text-red-500" />
        ) : (
          <Database className="w-4 h-4" />
        )}
        <span className="hidden sm:inline">
          {isSaving ? "Saving..." : saveStatus === "success" ? "Saved!" : "Save Snapshot"}
        </span>
      </button>

      {saveStatus === "error" && saveError && (
        <div className="absolute bottom-full mb-2 right-0 px-3 py-2 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300 whitespace-nowrap">
          {saveError}
        </div>
      )}

      {/* Snapshots Dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowSnapshots(!showSnapshots)}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 bg-background border border-input rounded-md text-sm",
            "hover:bg-accent transition-colors",
            showSnapshots && "bg-accent"
          )}
          title="View saved snapshots"
        >
          <Clock className="w-4 h-4" />
          <span className="hidden sm:inline">Snapshots</span>
          {snapshots.length > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-primary/10 text-primary rounded-full">
              {snapshots.length}
            </span>
          )}
        </button>

        {showSnapshots && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowSnapshots(false)}
              aria-hidden="true"
            />
            <div className="absolute right-0 top-full mt-1 z-50 w-80 origin-top-right rounded-md bg-popover border border-input shadow-lg animate-in fade-in-0 zoom-in-95 max-h-96 overflow-auto">
              <div className="p-2 border-b border-border">
                <p className="text-xs font-medium text-muted-foreground uppercase">Saved Snapshots</p>
              </div>
              {isLoadingSnapshots ? (
                <div className="p-4 flex items-center justify-center">
                  <Loader2 className="w-5 h-5 animate-spin" />
                </div>
              ) : snapshots.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground text-sm">
                  No snapshots saved yet
                </div>
              ) : (
                <ul className="py-1">
                  {snapshots.map((snapshot) => (
                    <li key={snapshot.id} className="px-3 py-2 hover:bg-accent cursor-pointer transition-colors">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 text-sm">
                            <Database className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                            <code className="font-mono text-xs flex-1 truncate">{formatSha(snapshot.commit_sha)}</code>
                          </div>
                          {snapshot.commit_message && (
                            <p className="text-xs text-muted-foreground mt-1 truncate">{snapshot.commit_message}</p>
                          )}
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {formatDate(snapshot.created_at)} • {snapshot.total_files} files • {formatFileSize(snapshot.total_size)}
                          </p>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Helper function (also in file-detection.ts)
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const size = bytes / Math.pow(1024, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}