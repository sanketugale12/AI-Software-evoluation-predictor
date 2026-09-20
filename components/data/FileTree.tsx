"use client";

import React, { useState, useMemo, useCallback } from "react";
import {
  Search,
  File,
  FolderOpen,
  FolderClosed,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  Zap,
  EyeOff,
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { TreeNode } from "@/types";

interface FileTreeNode {
  path: string;
  name: string;
  type: "blob" | "tree";
  children?: FileTreeNode[];
  depth: number;
  // Metadata
  size?: number;
  language?: string;
  is_binary: boolean;
  is_generated: boolean;
  is_ignored: boolean;
}

function buildFileTree(nodes: TreeNode[]): FileTreeNode[] {
  const root: FileTreeNode = {
    path: "",
    name: "",
    type: "tree",
    children: [],
    depth: -1,
    is_binary: false,
    is_generated: false,
    is_ignored: false,
  };

  // Sort nodes: directories first, then files, both alphabetically
  const sortedNodes = [...nodes].sort((a, b) => {
    if (a.type !== b.type) {
      return a.type === "tree" ? -1 : 1;
    }
    return a.path.localeCompare(b.path);
  });

  sortedNodes.forEach((node) => {
    const parts = node.path.split("/");
    let current = root;

    parts.forEach((part, index) => {
      const isLast = index === parts.length - 1;
      const currentPath = parts.slice(0, index + 1).join("/");

      let child = current.children?.find((c) => c.name === part);

      if (!child) {
        child = {
          path: currentPath,
          name: part,
          type: isLast ? node.type : "tree",
          children: isLast ? undefined : [],
          depth: index,
          // Only pass metadata for the final node
          size: isLast ? node.size : undefined,
          language: isLast ? node.language : undefined,
          is_binary: isLast ? node.is_binary : false,
          is_generated: isLast ? node.is_generated : false,
          is_ignored: isLast ? node.is_ignored : false,
        };
        current.children?.push(child);
      }

      current = child;
    });
  });

  return root.children || [];
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const size = bytes / Math.pow(1024, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function getFileIcon(node: FileTreeNode) {
  if (node.type === "tree") return null;

  const ext = node.name.split(".").pop()?.toLowerCase();
  if (["js", "jsx", "ts", "tsx"].includes(ext || "")) return <File className="h-3.5 w-3.5 text-yellow-500" />;
  if (["py"].includes(ext || "")) return <File className="h-3.5 w-3.5 text-blue-500" />;
  if (["java"].includes(ext || "")) return <File className="h-3.5 w-3.5 text-red-500" />;
  if (["cpp", "cc", "cxx", "hpp", "h", "c"].includes(ext || "")) return <File className="h-3.5 w-3.5 text-purple-500" />;
  if (["go"].includes(ext || "")) return <File className="h-3.5 w-3.5 text-cyan-500" />;
  if (["rs"].includes(ext || "")) return <File className="h-3.5 w-3.5 text-orange-500" />;
  if (["json", "yaml", "yml", "toml", "xml"].includes(ext || "")) return <File className="h-3.5 w-3.5 text-gray-500" />;
  if (["md", "markdown", "txt"].includes(ext || "")) return <File className="h-3.5 w-3.5 text-gray-500" />;
  return <File className="h-3.5 w-3.5 text-gray-500" />;
}

interface FileTreeProps {
  tree: TreeNode[];
  selectedPath?: string;
  onFileClick: (node: TreeNode) => void;
}

export function FileTree({ tree, selectedPath, onFileClick }: FileTreeProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<string | null>(selectedPath || null);

  const treeData = useMemo(() => buildFileTree(tree), [tree]);

  const filteredTree = useMemo(() => {
    if (!searchQuery) return treeData;

    const query = searchQuery.toLowerCase();
    const filterNode = (nodes: FileTreeNode[]): FileTreeNode[] => {
      return nodes
        .map((node) => {
          const nameMatch = node.name.toLowerCase().includes(query);
          const pathMatch = node.path.toLowerCase().includes(query);

          if (node.type === "blob") {
            return nameMatch || pathMatch ? node : null;
          }

          const filteredChildren = filterNode(node.children || []);
          if (filteredChildren.length > 0 || nameMatch || pathMatch) {
            return { ...node, children: filteredChildren };
          }
          return null;
        })
        .filter((n): n is FileTreeNode => n !== null);
    };

    // If searching, expand all matching folders
    if (searchQuery) {
      const expandMatching = (nodes: FileTreeNode[]) => {
        nodes.forEach((node) => {
          if (node.type === "tree" && node.children) {
            const hasMatch = node.children.some(
              (c) => c.name.toLowerCase().includes(query) || c.path.toLowerCase().includes(query)
            );
            if (hasMatch) {
              setExpandedFolders((prev) => new Set(prev).add(node.path));
            }
            expandMatching(node.children);
          }
        });
      };
      expandMatching(treeData);
    }

    return filterNode(treeData);
  }, [treeData, searchQuery]);

  const toggleFolder = useCallback((path: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  }, []);

  const handleFileClick = useCallback(
    (node: TreeNode) => {
      setSelected(node.path);
      onFileClick(node);
    },
    [onFileClick]
  );

  const renderNode = useCallback(
    (node: FileTreeNode, depth: number = 0): React.ReactNode => {
      const isExpanded = expandedFolders.has(node.path);
      const isSelected = selected === node.path;
      const hasChildren = node.type === "tree" && (node.children?.length || 0) > 0;

      // Determine badge
      let badge: React.ReactNode = null;
      if (node.type === "blob") {
        if (node.is_binary) {
          badge = <span className="ml-1 px-1 py-0.5 text-[10px] bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 rounded" title="Binary file">BIN</span>;
        } else if (node.is_generated) {
          badge = <span className="ml-1 px-1 py-0.5 text-[10px] bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 rounded" title="Generated file"><Zap className="h-2.5 w-2.5" /></span>;
        } else if (node.is_ignored) {
          badge = <span className="ml-1 px-1 py-0.5 text-[10px] bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 rounded" title="Ignored"><EyeOff className="h-2.5 w-2.5" /></span>;
        }
      }

      if (node.type === "blob") {
        return (
          <div
            key={node.path}
            className={cn(
              "flex items-center gap-1 px-2 py-1 text-sm rounded hover:bg-accent cursor-pointer transition-colors",
              isSelected && "bg-accent text-accent-foreground font-medium",
              node.is_ignored && "opacity-50",
              `pl-${4 + depth * 2}`
            )}
            onClick={() => {
              // Find the original TreeNode
              const originalNode = tree.find((n) => n.path === node.path);
              if (originalNode) handleFileClick(originalNode);
            }}
            title={node.path}
          >
            {getFileIcon(node)}
            <span className="truncate flex-1">{node.name}</span>
            {badge}
            {node.size && (
              <span className="text-xs text-muted-foreground ml-auto whitespace-nowrap">
                {formatFileSize(node.size)}
              </span>
            )}
          </div>
        );
      }

      return (
        <div key={node.path}>
          <div
            className={cn(
              "flex items-center gap-1 px-2 py-1 text-sm rounded hover:bg-accent cursor-pointer transition-colors",
              isSelected && "bg-accent text-accent-foreground font-medium",
              node.is_ignored && "opacity-50",
              `pl-${4 + depth * 2}`
            )}
            onClick={() => toggleFolder(node.path)}
          >
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
              )
            ) : (
              <span className="h-3.5 w-3.5 flex-shrink-0" />
            )}
            {isExpanded ? (
              <FolderOpen className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
            ) : (
              <FolderClosed className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
            )}
            <span className="truncate font-medium flex-1">{node.name}</span>
            {node.is_ignored && <EyeOff className="h-3.5 w-3.5 text-muted-foreground" />}
          </div>
          {isExpanded && node.children && (
            <div>{node.children.map((child) => renderNode(child, depth + 1))}</div>
          )}
        </div>
      );
    },
    [expandedFolders, selected, tree, handleFileClick, toggleFolder]
  );

  return (
    <div className="flex h-full flex-col">
      <div className="p-2 border-b">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-1.5 bg-background border border-input rounded-md text-sm outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2">{filteredTree.map((node) => renderNode(node))}</div>
      </ScrollArea>
    </div>
  );
}