"use client";

import React, { useState, useEffect } from "react";
import { ChevronDown, GitBranch, GitCommitHorizontal, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWorkspace } from "@/context/WorkspaceContext";
import type { BranchInfo } from "@/types";

interface CommitSelectorProps {
  className?: string;
}

export function CommitSelector({ className }: CommitSelectorProps) {
  const { repoContext, branches, selectedCommit, selectCommit, treeAtCommit, isFileLoading } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const [customSha, setCustomSha] = useState("");
  const [isLoadingBranches, setIsLoadingBranches] = useState(false);

  // Load branches when repoContext changes
  useEffect(() => {
    if (repoContext && branches.length === 0) {
      // Branches will be loaded by the parent via loadRepositoryContext
    }
  }, [repoContext, branches]);

  const handleBranchSelect = (branch: BranchInfo) => {
    selectCommit(branch.commit_sha);
    setIsOpen(false);
  };

  const handleCustomShaSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customSha.trim()) {
      selectCommit(customSha.trim());
      setCustomSha("");
      setIsOpen(false);
    }
  };

  const getCurrentCommitInfo = () => {
    if (!treeAtCommit) return null;
    return {
      sha: treeAtCommit.sha.slice(0, 8),
      fullSha: treeAtCommit.sha,
    };
  };

  const currentCommit = getCurrentCommitInfo();
  const currentBranch = branches.find(b => b.commit_sha === selectedCommit);

  return (
    <div className={cn("relative", className)}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 bg-background border border-input rounded-md text-sm",
          "hover:bg-accent transition-colors",
          "min-w-[200px] max-w-[350px]"
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <GitBranch className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        <div className="flex-1 min-w-0 text-left">
          <p className="font-medium truncate">
            {currentBranch?.name || currentCommit?.sha || "Select commit/branch"}
          </p>
          {currentCommit && (
            <p className="text-xs text-muted-foreground truncate font-mono">
              {currentCommit.sha}
            </p>
          )}
        </div>
        {isFileLoading && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
        <ChevronDown className={cn("w-4 h-4 text-muted-foreground flex-shrink-0", isOpen && "rotate-180")} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 z-50 w-72 origin-top-right rounded-md bg-popover border border-input shadow-lg animate-in fade-in-0 zoom-in-95">
          {/* Branches Section */}
          {branches.length > 0 && (
            <div className="p-2">
              <p className="px-2 py-1 text-xs font-medium text-muted-foreground uppercase">Branches</p>
              {branches.map((branch) => (
                <button
                  key={branch.name}
                  onClick={() => handleBranchSelect(branch)}
                  className={cn(
                    "w-full flex items-center gap-2 px-2 py-1.5 text-sm rounded hover:bg-accent transition-colors",
                    branch.commit_sha === selectedCommit && "bg-accent text-accent-foreground"
                  )}
                >
                  <GitBranch className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate flex-1">{branch.name}</span>
                  {branch.protected && (
                    <span className="text-xs text-muted-foreground" title="Protected branch">🔒</span>
                  )}
                  {branch.commit_sha === selectedCommit && (
                    <GitCommitHorizontal className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                  )}
                </button>
              ))}
            </div>
          )}

          <Separator />

          {/* Custom Commit SHA */}
          <div className="p-2">
            <p className="px-2 py-1 text-xs font-medium text-muted-foreground uppercase">Custom Commit</p>
            <form onSubmit={handleCustomShaSubmit} className="flex gap-2 px-2">
              <input
                type="text"
                value={customSha}
                onChange={(e) => setCustomSha(e.target.value)}
                placeholder="Enter commit SHA..."
                className="flex-1 px-2 py-1.5 text-sm bg-background border border-input rounded outline-none focus:ring-2 focus:ring-ring"
                maxLength={40}
                autoFocus
              />
              <button
                type="submit"
                disabled={!customSha.trim() || isFileLoading}
                className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Go
              </button>
            </form>
            <p className="px-2 py-1 text-xs text-muted-foreground">
              Enter a full or short commit SHA
            </p>
          </div>

          {/* Current Commit Info */}
          {currentCommit && (
            <div className="px-2 py-2 border-t border-border">
              <p className="text-xs text-muted-foreground mb-1">Current Commit</p>
              <div className="flex items-center gap-2 px-2 py-1.5 bg-muted rounded text-sm">
                <GitCommitHorizontal className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                <code className="font-mono text-xs flex-1 truncate">{currentCommit.fullSha}</code>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}
    </div>
  );
}

// Simple separator component
function Separator({ className }: { className?: string }) {
  return <div className={cn("border-t border-border my-1", className)} />;
}