"use client";

import React, { useCallback } from "react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { FileExplorer } from "@/components/data/FileExplorer";
import { CommitSelector } from "@/components/data/CommitSelector";
import { SnapshotActions } from "@/components/data/SnapshotActions";
import { PageHeader } from "@/components/layout/PageHeader";
import { Code, Download } from "lucide-react";

export function Files() {
  const {
    repoContext,
    treeAtCommit,
    selectedFile,
    isFileLoading,
    loadRepositoryContext,
    selectCommit,
    loadFile,
    clearSelectedFile,
  } = useWorkspace();

  // Load repository context on first mount
  React.useEffect(() => {
    if (repoContext) {
      loadRepositoryContext(repoContext.owner, repoContext.name);
    }
  }, [repoContext, loadRepositoryContext]);

  if (!repoContext) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <Code className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No repository selected</p>
          <p className="mt-1 text-xs">Select a repository from the sidebar to browse files</p>
        </div>
      </div>
    );
  }

  if (!treeAtCommit) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
          <PageHeader
            title="Files"
            subtitle={`${repoContext.owner}/${repoContext.name}`}
            action={
              <CommitSelector />
            }
          />
          <SnapshotActions />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center p-8">
            <Download className="mx-auto h-12 w-12 text-muted-foreground/50 animate-pulse" />
            <p className="mt-4 text-sm">Loading repository tree...</p>
            <p className="mt-1 text-xs text-muted-foreground">Fetching files at selected commit</p>
          </div>
        </div>
      </div>
    );
  }

  if (treeAtCommit.tree.length === 0) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
          <PageHeader
            title="Files"
            subtitle={`${repoContext.owner}/${repoContext.name}`}
            action={
              <CommitSelector />
            }
          />
          <SnapshotActions />
        </div>
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          <div className="text-center p-8">
            <Code className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-sm">No files found</p>
            <p className="mt-1 text-xs">This commit may be empty or have no files</p>
          </div>
        </div>
      </div>
    );
  }

  const handleNavigateFile = React.useCallback(
    (direction: "prev" | "next") => {
      // File navigation is handled internally by FileExplorer
      // This is a placeholder for future external navigation
    },
    []
  );

  return (
    <div className="flex h-full flex-col">
      {/* Header with Commit Selector and Snapshot Actions */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/30">
        <PageHeader
          title="Files"
          subtitle={`${repoContext.owner}/${repoContext.name}`}
          action={
            <CommitSelector />
          }
        />
        <SnapshotActions />
      </div>

      {/* File Explorer */}
      <FileExplorer
        tree={treeAtCommit.tree}
        selectedFile={selectedFile}
        onSelectFile={loadFile}
        onLoadFile={loadFile}
        onNavigateFile={handleNavigateFile}
        isLoading={isFileLoading}
      />
    </div>
  );
}