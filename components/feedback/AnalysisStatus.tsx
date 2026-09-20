import { useWorkspace } from "@/context/WorkspaceContext";
import { cn, getStatusColor } from "@/lib/utils";
import { Loader2, CheckCircle, XCircle, AlertCircle, Clock, RotateCcw, PlayCircle, Trash2, GitCommit, FileText, Database, AlertTriangle } from "lucide-react";
import { useState, useEffect } from "react";

const statusConfig = {
  pending: { icon: Clock, label: "Queued", description: "Analysis is queued for processing" },
  queued: { icon: Clock, label: "Queued", description: "Analysis is queued for processing" },
  running: { icon: Loader2, label: "Running", description: "Analysis is in progress" },
  completed: { icon: CheckCircle, label: "Completed", description: "Analysis completed successfully" },
  failed: { icon: XCircle, label: "Failed", description: "Analysis encountered an error" },
  cancelling: { icon: Loader2, label: "Cancelling", description: "Analysis is being cancelled" },
} as const;

const analysisSteps = [
  { id: "cloning", label: "Cloning Repository", description: "Downloading repository source code" },
  { id: "validation", label: "Validating Repository", description: "Checking repository size and limits" },
  { id: "complexity", label: "Complexity Analysis", description: "Measuring code complexity metrics" },
  { id: "git_history", label: "Git History", description: "Analyzing commit history and contributors" },
  { id: "security", label: "Security Scan", description: "Scanning for security vulnerabilities" },
  { id: "hotspots", label: "Hotspot Detection", description: "Identifying code hotspots" },
  { id: "technical_debt", label: "Technical Debt", description: "Calculating technical debt metrics" },
];

export function AnalysisStatus() {
  const { analysisJob, analysisResults, isLoading, cancelAnalysis, retryAnalysis } = useWorkspace();
  const [elapsedTime, setElapsedTime] = useState(0);

  // Track elapsed time for running jobs
  useEffect(() => {
    if (!analysisJob) return;

    const status = analysisJob.status;
    if (status === "running" || status === "queued" || status === "pending") {
      const interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    } else if (analysisJob.started_at) {
      // Calculate elapsed from started_at to completed_at or now
      const start = new Date(analysisJob.started_at).getTime();
      const end = analysisJob.completed_at ? new Date(analysisJob.completed_at).getTime() : Date.now();
      setElapsedTime(Math.floor((end - start) / 1000));
    }
  }, [analysisJob]);

  if (!analysisJob && !analysisResults) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No analysis started</p>
          <p className="mt-1 text-xs">Click "Analyze" to start a full repository analysis</p>
        </div>
      </div>
    );
  }

  const status = analysisJob?.status || "pending";
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
  const Icon = config.icon;
  const progress = analysisJob?.progress;

  return (
    <div className="flex h-full flex-col">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div
              className={cn(
                "p-2 rounded-full flex-shrink-0",
                getStatusColor(status)
              )}
            >
              <Icon className={cn("h-5 w-5", status === "running" && "animate-spin")} />
            </div>
            <div className="min-w-0">
              <h3 className="font-medium truncate">{config.label}</h3>
              <p className="text-sm text-muted-foreground truncate">{config.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {status === "running" && (
              <button
                onClick={cancelAnalysis}
                className="p-1.5 hover:bg-destructive/10 text-destructive rounded transition-colors"
                title="Cancel analysis"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
            {(status === "failed" || (status as string) === "cancelled") && (
              <button
                onClick={retryAnalysis}
                className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Retry
              </button>
            )}
          </div>
        </div>

        {/* Commit Info (Phase 6) */}
        {analysisJob?.commit_sha && (
          <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
            <GitCommit className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="font-mono">Pinned to: {analysisJob.commit_sha.substring(0, 8)}</span>
          </div>
        )}

        {/* Repository Stats (Phase 6) */}
        {analysisResults?.results?.repository_stats && (
          <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <FileText className="h-3.5 w-3.5" />
              <span>{analysisResults.results.repository_stats.file_count} files</span>
            </div>
            <div className="flex items-center gap-1">
              <Database className="h-3.5 w-3.5" />
              <span>{analysisResults.results.repository_stats.total_size_mb.toFixed(1)} MB</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              <span>Cloned in {analysisResults.results.repository_stats.clone_duration_seconds.toFixed(1)}s</span>
            </div>
            {analysisResults.results.repository_stats.excluded_size_mb > 0 && (
              <div className="flex items-center gap-1 text-amber-500">
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>{analysisResults.results.repository_stats.excluded_size_mb.toFixed(1)} MB excluded</span>
              </div>
            )}
          </div>
        )}

        {/* Progress Steps */}
        {status === "running" && progress && (
          <div className="mt-4 space-y-2">
            {analysisSteps.map((step, index) => {
              const isCurrent = step.id === progress.current_step;
              const isCompleted = index < progress.step_number - 1 || (isCurrent && progress.step_number > index);
              const isActive = isCurrent && progress.step_number - 1 === index;

              return (
                <div key={step.id} className="flex items-center gap-3 text-sm">
                  <div className={cn(
                    "flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center",
                    isCompleted ? "bg-primary border-primary text-primary-foreground" :
                    isActive ? "border-primary bg-primary/10" :
                    "border-muted bg-muted"
                  )}>
                    {isCompleted ? (
                      <CheckCircle className="w-3.5 h-3.5" />
                    ) : isActive ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <span className="text-xs font-medium">{index + 1}</span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={cn("font-medium truncate", isActive && "text-foreground", !isActive && !isCompleted && "text-muted-foreground")}>
                      {step.label}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">{step.description}</p>
                  </div>
                  {isActive && (
                    <span className="text-xs text-primary font-mono">{progress.message}</span>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Elapsed Time */}
        {(status === "running" || status === "completed" || status === "failed") && analysisJob?.started_at && (
          <div className="mt-2 text-xs text-muted-foreground">
            Elapsed: {formatElapsedTime(elapsedTime)}
          </div>
        )}
      </div>

      {analysisResults?.error_message && (
        <div className="p-4 border-b bg-destructive/10 border-destructive/20">
          <div className="flex items-start gap-2 text-destructive">
            <XCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Analysis Failed</p>
              <p className="text-sm mt-1">{analysisResults.error_message}</p>
              {analysisJob?.retry_count && analysisJob.retry_count > 0 && (
                <p className="text-xs text-muted-foreground mt-1">Retry attempt: {analysisJob.retry_count}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {analysisResults?.results && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AnalysisResultsSummary results={analysisResults.results} />
        </div>
      )}

      {(status === "running" || status === "pending" || status === "queued") && !analysisResults?.results ? (
        <div className="p-4 border-t">
          <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: progress ? `${(progress.step_number / progress.total_steps) * 100}%` : "0%" }}
            />
          </div>
          <p className="mt-2 text-xs text-muted-foreground text-center">
            {progress?.message || (status === "running"
              ? "Analyzing repository... this may take a few minutes"
              : "Waiting for analysis to start...")}
          </p>
        </div>
      ) : null}
    </div>
  );
}

function formatElapsedTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
}

function AnalysisResultsSummary({ results }: { results: any }) {
  const sections = [];

  if (results.complexity) {
    const files = Object.keys(results.complexity).length;
    const totalComplexity = Object.values(results.complexity).flat().reduce(
      (sum: number, block: any) => sum + (block.complexity || 0),
      0
    );
    sections.push({
      title: "Complexity Analysis",
      value: `${files} files analyzed`,
      detail: `Total complexity: ${totalComplexity.toFixed(1)}`,
    });
  }

  if (results.history) {
    sections.push({
      title: "Git History",
      value: `${results.history.total_commits} commits`,
      detail: `${results.history.metrics.contributor_count} contributors • ${results.history.metrics.commit_frequency.toFixed(1)} commits/day`,
    });
  }

  if (results.hotspots) {
    const reviewCount = results.hotspots.filter((h: any) => h.status === "Review").length;
    const monitorCount = results.hotspots.filter((h: any) => h.status === "Monitor").length;
    sections.push({
      title: "Code Hotspots",
      value: `${results.hotspots.length} files analyzed`,
      detail: `${reviewCount} need review • ${monitorCount} to monitor`,
    });
  }

  if (results.security) {
    const findings = results.security.findings?.length || 0;
    const critical = results.security.findings?.filter((f: any) => f.severity === "CRITICAL").length || 0;
    const error = results.security.findings?.filter((f: any) => f.severity === "ERROR").length || 0;
    sections.push({
      title: "Security Scan",
      value: `${findings} findings`,
      detail: `${critical} critical • ${error} errors`,
    });
  }

  // Technical Debt (Phase 6)
  if (results.technical_debt) {
    const td = results.technical_debt;
    const riskColor = td.risk_level === "High" ? "text-destructive" : td.risk_level === "Medium" ? "text-amber-500" : "text-green-500";
    sections.push({
      title: "Technical Debt",
      value: `Score: ${td.debt_score} (${td.risk_level})`,
      detail: `${td.total_files} files • ${td.high_complexity_files} high complexity • ${td.total_churn} total churn`,
    });
  }

  // Commit Info in results (Phase 6)
  if (results.commit_sha) {
    sections.push({
      title: "Analysis Commit",
      value: results.commit_sha.substring(0, 12),
      detail: `Branch: ${results.branch || 'unknown'}`,
    });
  }

  if (sections.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <p className="text-sm">Analysis completed but no results to display</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium">Results Summary</h4>
      {sections.map((section, index) => (
        <div key={index} className="p-3 rounded-lg border bg-card">
          <p className="font-medium text-sm">{section.title}</p>
          <p className="text-lg font-bold mt-1">{section.value}</p>
          <p className="text-xs text-muted-foreground">{section.detail}</p>
        </div>
      ))}
    </div>
  );
}