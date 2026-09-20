import { useWorkspace } from "@/context/WorkspaceContext";
import { Button } from "@/components/ui/button";
import { Loader2, Play, RefreshCw, AlertCircle } from "lucide-react";
import { cn, getStatusColor } from "@/lib/utils";

export function PageHeader() {
  const { repoDetails, isLoading, startAnalysis, analysisJob, analysisResults, clearError, error } = useWorkspace();

  const isAnalyzing = analysisJob?.status === "running" || analysisJob?.status === "pending";
  const isComplete = analysisJob?.status === "completed";

  return (
    <div className="flex h-16 items-center justify-between border-b px-4 bg-card">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold">
          {repoDetails?.name || "ASEP Workspace"}
        </h1>
        {repoDetails && (
          <span className="text-sm text-muted-foreground">
            {repoDetails.language && (
              <>
                <span className="px-2 py-0.5 rounded bg-secondary text-secondary-foreground">
                  {repoDetails.language}
                </span>
              </>
            )}
            <span className="px-2 py-0.5 rounded bg-secondary text-secondary-foreground">
              ⭐ {repoDetails.stars}
            </span>
            <span className="px-2 py-0.5 rounded bg-secondary text-secondary-foreground">
              🍴 {repoDetails.forks}
            </span>
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {error && (
          <Button
            variant="destructive"
            size="sm"
            className="gap-1"
            onClick={clearError}
          >
            <AlertCircle className="h-3 w-3" />
            Error
          </Button>
        )}

        <Button
          variant={isAnalyzing ? "secondary" : "default"}
          size="sm"
          className="gap-1"
          onClick={startAnalysis}
          disabled={isLoading || isAnalyzing || !repoDetails}
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="h-3 w-3 animate-spin" />
              Analyzing...
            </>
          ) : isComplete ? (
            <>
              <RefreshCw className="h-3 w-3" />
              Re-analyze
            </>
          ) : (
            <>
              <Play className="h-3 w-3" />
              Analyze
            </>
          )}
        </Button>

        {analysisJob && (
          <span
            className={cn(
              "px-2 py-0.5 rounded text-xs font-medium",
              getStatusColor(analysisJob.status)
            )}
          >
            {analysisJob.status}
          </span>
        )}
      </div>
    </div>
  );
}