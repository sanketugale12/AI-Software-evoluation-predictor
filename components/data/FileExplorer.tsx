"use client";

import React, { useState, useCallback, useMemo } from "react";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { FileSearch } from "./FileSearch";
import { FilePreview } from "./FilePreview";
import { FileTree } from "./FileTree";
import type { TreeNode, FileContent } from "@/types";

interface FileExplorerProps {
  tree: TreeNode[];
  selectedFile: FileContent | null;
  onSelectFile: (node: TreeNode) => void;
  onLoadFile: (node: TreeNode) => Promise<void>;
  onNavigateFile: (direction: "prev" | "next") => void;
  isLoading: boolean;
}

export function FileExplorer({
  tree,
  selectedFile,
  onSelectFile,
  onLoadFile,
  onNavigateFile,
  isLoading,
}: FileExplorerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);

  // Get all files in order for navigation
  const allFiles = useMemo(() => {
    const files: TreeNode[] = [];
    function collect(node: TreeNode) {
      if (node.type === "blob") {
        files.push(node);
      } else if (node.type === "tree") {
        // This is a simplified version - in reality we'd need children
        // For now, we'll just use the flat tree
      }
    }
    tree.forEach(collect);
    return files;
  }, [tree]);

  // Find current file index for navigation
  const currentFileIndex = useMemo(() => {
    if (!selectedFile) return -1;
    return allFiles.findIndex((f) => f.path === selectedFile.path);
  }, [allFiles, selectedFile]);

  const handleFileClick = useCallback(
    async (node: TreeNode) => {
      onSelectFile(node);
      await onLoadFile(node);
    },
    [onSelectFile, onLoadFile]
  );

  const handleNavigate = useCallback(
    (direction: "prev" | "next") => {
      if (currentFileIndex === -1) return;
      const newIndex =
        direction === "prev"
          ? Math.max(0, currentFileIndex - 1)
          : Math.min(allFiles.length - 1, currentFileIndex + 1);
      if (newIndex !== currentFileIndex) {
        const node = allFiles[newIndex];
        if (node) {
          onSelectFile(node);
          onLoadFile(node);
        }
      }
    },
    [currentFileIndex, allFiles, onSelectFile, onLoadFile]
  );

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Search bar */}
      <div className="p-2 border-b border-border">
        <FileSearch
          tree={tree}
          onSelectFile={handleFileClick}
          onClose={() => setShowSearch(false)}
        />
      </div>

      {/* Main content - Resizable panels */}
      <ResizablePanelGroup direction="horizontal" className="flex-1 overflow-hidden">
        {/* File Tree Panel */}
        <ResizablePanel minSize={200} maxSize={500} defaultSize={300}>
          <div className="h-full flex flex-col border-r border-border bg-background">
            <div className="px-3 py-2 border-b border-border bg-muted/30">
              <h3 className="font-medium text-sm">Files</h3>
            </div>
            <div className="flex-1 overflow-auto">
              <FileTree
                tree={tree}
                selectedPath={selectedFile?.path}
                onFileClick={handleFileClick}
              />
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle
          withHandle
          className="relative flex h-full items-center justify-center border-l border-border bg-muted/50 hover:bg-muted transition-colors"
        >
          <div className="flex h-6 w-px bg-border" />
        </ResizableHandle>

        {/* File Preview Panel */}
        <ResizablePanel minSize={300}>
          <div className="h-full flex flex-col">
            <FilePreview
              file={selectedFile}
              onClose={() => onSelectFile({ path: "", type: "blob", mode: "", sha: "", size: 0, is_binary: false, is_generated: false, is_ignored: false })}
              onNavigate={handleNavigate}
            />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}