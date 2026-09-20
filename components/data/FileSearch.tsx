"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Fuse from "fuse.js";
import { Search, X, ChevronDown, ChevronUp, File, Folder, Code } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TreeNode } from "@/types";

interface FileSearchProps {
  tree: TreeNode[];
  onSelectFile: (node: TreeNode) => void;
  onClose?: () => void;
}

export function FileSearch({ tree, onSelectFile, onClose }: FileSearchProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(true);

  // Filter only files (not directories)
  const files = useMemo(() => tree.filter((node) => node.type === "blob"), [tree]);

  // Initialize Fuse.js
  const fuse = useMemo(
    () =>
      new Fuse(files, {
        keys: ["path"],
        threshold: 0.4,
        includeScore: true,
        includeMatches: true,
        minMatchCharLength: 2,
        ignoreLocation: true,
        findAllMatches: true,
      }),
    [files]
  );

  // Search results
  const results = useMemo(() => {
    if (!query.trim()) return [];
    return fuse.search(query).slice(0, 50);
  }, [fuse, query]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => Math.max(prev - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (results[selectedIndex]) {
            onSelectFile(results[selectedIndex].item);
            setQuery("");
            setSelectedIndex(0);
            if (onClose) onClose();
          }
          break;
        case "Escape":
          e.preventDefault();
          setQuery("");
          if (onClose) onClose();
          break;
      }
    },
    [results, onSelectFile, onClose]
  );

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Get file icon
  const getFileIcon = (path: string) => {
    const ext = path.split(".").pop()?.toLowerCase();
    if (["js", "jsx", "ts", "tsx"].includes(ext || "")) return <Code className="w-4 h-4 text-yellow-500" />;
    if (["py"].includes(ext || "")) return <Code className="w-4 h-4 text-blue-500" />;
    if (["java"].includes(ext || "")) return <Code className="w-4 h-4 text-red-500" />;
    if (["cpp", "cc", "cxx", "hpp", "h"].includes(ext || "")) return <Code className="w-4 h-4 text-purple-500" />;
    if (["go"].includes(ext || "")) return <Code className="w-4 h-4 text-cyan-500" />;
    if (["rs"].includes(ext || "")) return <Code className="w-4 h-4 text-orange-500" />;
    if (["json", "yaml", "yml", "toml", "xml"].includes(ext || "")) return <Code className="w-4 h-4 text-gray-500" />;
    if (["md", "markdown", "txt"].includes(ext || "")) return <File className="w-4 h-4 text-gray-500" />;
    return <File className="w-4 h-4 text-gray-500" />;
  };

  // Highlight match in path
  const highlightPath = (path: string, matches?: readonly any[]) => {
    if (!matches || matches.length === 0) return <span>{path}</span>;

    const match = matches[0];
    if (!match.indices || match.indices.length === 0) return <span>{path}</span>;

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    for (const [start, end] of match.indices) {
      if (start > lastIndex) {
        parts.push(path.slice(lastIndex, start));
      }
      parts.push(
        <mark key={`${start}-${end}`} className="bg-yellow-300 dark:bg-yellow-800 text-black dark:text-white px-0.5 rounded">
          {path.slice(start, end + 1)}
        </mark>
      );
      lastIndex = end + 1;
    }

    if (lastIndex < path.length) {
      parts.push(path.slice(lastIndex));
    }

    return <span>{parts}</span>;
  };

  if (!isOpen && !query) return null;

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search files... (Ctrl+P)"
          className="w-full pl-10 pr-10 py-2 bg-background border border-input rounded-md text-sm outline-none focus:ring-2 focus:ring-ring"
          autoFocus
        />
        {query && (
          <button
            onClick={() => {
              setQuery("");
              setSelectedIndex(0);
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {query && (
        <div className="mt-2 max-h-96 overflow-auto bg-popover border border-input rounded-md shadow-lg">
          {results.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              No files found matching "{query}"
            </div>
          ) : (
            <ul className="py-1" role="listbox">
              {results.map((result, index) => {
                const node = result.item;
                const isSelected = index === selectedIndex;
                return (
                  <li
                    key={node.path}
                    role="option"
                    aria-selected={isSelected}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 text-sm cursor-pointer",
                      isSelected && "bg-accent text-accent-foreground"
                    )}
                    onClick={() => {
                      onSelectFile(node);
                      setQuery("");
                      if (onClose) onClose();
                    }}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    {getFileIcon(node.path)}
                    <span className="flex-1 truncate">{highlightPath(node.path, result.matches)}</span>
                    {node.size && (
                      <span className="text-xs text-muted-foreground ml-2">
                        {formatFileSize(node.size)}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
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