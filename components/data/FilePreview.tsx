"use client";

import React, { useEffect, useState, useRef } from "react";
import { X, Download, Copy, ChevronLeft, ChevronRight, FileCode, Info, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { highlightCode, getLanguageFromFilename } from "@/lib/syntax-highlighting";
import type { FileContent } from "@/types";

interface FilePreviewProps {
  file: FileContent | null;
  onClose: () => void;
  onNavigate?: (direction: "prev" | "next") => void;
}

export function FilePreview({ file, onClose, onNavigate }: FilePreviewProps) {
  const [highlightedHtml, setHighlightedHtml] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);
  const [activeTheme, setActiveTheme] = useState<"github-dark" | "github-light">("github-dark");
  const containerRef = useRef<HTMLDivElement>(null);

  // Detect theme from CSS
  useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark");
    setActiveTheme(isDark ? "github-dark" : "github-light");

    const observer = new MutationObserver(() => {
      const isDarkNow = document.documentElement.classList.contains("dark");
      setActiveTheme(isDarkNow ? "github-dark" : "github-light");
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    return () => observer.disconnect();
  }, []);

  // Highlight code when file changes
  useEffect(() => {
    const currentFile = file;
    if (!currentFile) return;

    async function loadHighlighted() {
      if (!currentFile.content && currentFile.encoding !== "utf-8") {
        setError("Binary file cannot be displayed");
        setHighlightedHtml("");
        return;
      }

      if (!currentFile.content) {
        setError("No content available");
        setHighlightedHtml("");
        return;
      }

      // Check file size (limit to 500KB for highlighting)
      if (currentFile.size > 500_000) {
        setError("File too large for syntax highlighting (>500KB)");
        setHighlightedHtml("");
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const language = currentFile.language || getLanguageFromFilename(currentFile.path);
        const html = await highlightCode(currentFile.content, language, activeTheme);
        setHighlightedHtml(html);
      } catch (err) {
        console.error("Highlighting failed:", err);
        // Fallback to plain text
        setHighlightedHtml(`<pre class="p-4 font-mono text-sm">${escapeHtml(currentFile.content)}</pre>`);
      } finally {
        setIsLoading(false);
      }
    }

    loadHighlighted();
  }, [file, activeTheme]);

  const escapeHtml = (text: string) => {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  const handleCopy = async () => {
    if (file?.content) {
      await navigator.clipboard.writeText(file.content);
      // Could add toast notification here
    }
  };

  const handleDownload = () => {
    if (!file?.content) return;
    const blob = new Blob([file.content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = file.path.split("/").pop() || "file";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!file) {
    return (
      <div className="flex-1 flex items-center justify-center bg-muted/50">
        <div className="text-center p-8">
          <FileCode className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">Select a file to preview</p>
          <p className="text-xs text-muted-foreground/70 mt-1">Click a file in the tree to view its contents</p>
        </div>
      </div>
    );
  }

  const fileName = file.path.split("/").pop() || file.path;
  const isBinary = file.is_binary || file.encoding === "base64";
  const isGenerated = file.is_generated;
  const isIgnored = file.is_ignored;

  return (
    <div className="flex-1 flex flex-col bg-background border-l border-border">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-muted/30">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <button onClick={onClose} className="p-1 hover:bg-muted rounded transition-colors" aria-label="Close preview">
            <X className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <FileCode className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            <span className="font-mono text-sm truncate">{fileName}</span>
            <span className="text-xs text-muted-foreground flex-shrink-0">({file.path})</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Badges */}
          {isBinary && (
            <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 rounded">
              Binary
            </span>
          )}
          {isGenerated && (
            <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 rounded">
              Generated
            </span>
          )}
          {isIgnored && (
            <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 rounded">
              Ignored
            </span>
          )}
          {file.language && (
            <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded">
              {file.language}
            </span>
          )}

          {/* Actions */}
          <div className="flex items-center gap-1 ml-2">
            {onNavigate && (
              <>
                <button
                  onClick={() => onNavigate?.("prev")}
                  className="p-1.5 hover:bg-muted rounded transition-colors"
                  aria-label="Previous file"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => onNavigate?.("next")}
                  className="p-1.5 hover:bg-muted rounded transition-colors"
                  aria-label="Next file"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </>
            )}
            <button
              onClick={handleCopy}
              className="p-1.5 hover:bg-muted rounded transition-colors"
              aria-label="Copy content"
            >
              <Copy className="w-4 h-4" />
            </button>
            <button
              onClick={handleDownload}
              className="p-1.5 hover:bg-muted rounded transition-colors"
              aria-label="Download file"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowRaw(!showRaw)}
              className="p-1.5 hover:bg-muted rounded transition-colors"
              aria-label={showRaw ? "Show highlighted" : "Show raw"}
            >
              <Info className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4" ref={containerRef}>
        {isLoading && (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        )}

        {error && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <AlertTriangle className="w-12 h-12 text-yellow-500 mb-4" />
            <p className="text-muted-foreground">{error}</p>
            {file.content && file.size <= 500_000 && (
              <button
                onClick={() => setShowRaw(true)}
                className="mt-2 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
              >
                View as plain text
              </button>
            )}
          </div>
        )}

        {!isLoading && !error && (
          <div
            className={cn(
              "font-mono text-sm",
              showRaw ? "whitespace-pre-wrap" : ""
            )}
            dangerouslySetInnerHTML={{ __html: showRaw ? `<pre class="p-4">${escapeHtml(file.content || "")}</pre>` : highlightedHtml }}
          />
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-border bg-muted/30 flex items-center justify-between text-xs text-muted-foreground">
        <span>{file.size} bytes</span>
        <span>{file.sha.slice(0, 8)}</span>
        <span>Line count: {file.content?.split("\n").length || 0}</span>
      </div>
    </div>
  );
}