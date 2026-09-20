import { useWorkspace } from "@/context/WorkspaceContext";
import { useAuth } from "@/context/AuthContext";
import { StatCard } from "@/components/data/StatCard";
import { AnalysisStatus } from "@/components/feedback/AnalysisStatus";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { formatNumber, formatBytes, formatDate } from "@/lib/utils";
import {
  Star,
  GitFork,
  Code,
  Calendar,
  Database,
  Users,
  Activity,
  AlertTriangle,
  GitBranch,
  GitCommit,
} from "lucide-react";

export function Overview() {
  const { repoDetails, repoTree, analysisResults, isLoading } = useWorkspace();
  const { isAuthenticated } = useAuth();

  if (!repoDetails) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <Code className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No repository loaded</p>
          <p className="mt-1 text-xs">Navigate to a GitHub repository to begin analysis</p>
        </div>
      </div>
    );
  }

  const stats = [
    {
      label: "Stars",
      value: formatNumber(repoDetails.stars),
      icon: <Star className="h-5 w-5" />,
    },
    {
      label: "Forks",
      value: formatNumber(repoDetails.forks),
      icon: <GitFork className="h-5 w-5" />,
    },
    {
      label: "Language",
      value: repoDetails.language || "N/A",
      icon: <Code className="h-5 w-5" />,
    },
    {
      label: "Size",
      value: formatBytes(repoDetails.size * 1024),
      icon: <Database className="h-5 w-5" />,
    },
    {
      label: "Files",
      value: formatNumber(repoTree?.files.length || 0),
      icon: <Activity className="h-5 w-5" />,
    },
    {
      label: "Updated",
      value: formatDate(repoDetails.updated_at),
      icon: <Calendar className="h-5 w-5" />,
    },
  ];

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-6">
        {/* Repository Header */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold">{repoDetails.name}</h2>
                <p className="mt-1 text-muted-foreground">
                  {repoDetails.description || "No description provided"}
                </p>
                <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Code className="h-3.5 w-3.5" />
                    {repoDetails.language || "Unknown"}
                  </span>
                  <span className="flex items-center gap-1">
                    <Star className="h-3.5 w-3.5" />
                    {formatNumber(repoDetails.stars)}
                  </span>
                  <span className="flex items-center gap-1">
                    <GitFork className="h-3.5 w-3.5" />
                    {formatNumber(repoDetails.forks)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Database className="h-3.5 w-3.5" />
                    {formatBytes(repoDetails.size * 1024)}
                  </span>
                </div>

                {/* Repository Context - Branch & Commit */}
                {isAuthenticated && (
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <Badge variant="outline" className="gap-1">
                      <GitBranch className="h-3 w-3" />
                      <span>Default: {repoDetails.default_branch}</span>
                    </Badge>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {stats.map((stat, index) => (
            <StatCard key={index} {...stat} />
          ))}
        </div>

        {/* Repository Context Details (Authenticated) */}
        {isAuthenticated && (
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <GitCommit className="h-5 w-5" />
                Repository Context
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Default Branch
                  </p>
                  <p className="font-mono text-sm">{repoDetails.default_branch}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Repository Owner
                  </p>
                  <p className="font-medium text-sm">
                    {repoDetails.name.split("/")[0] || "Unknown"}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Repository Name
                  </p>
                  <p className="font-medium text-sm">
                    {repoDetails.name.split("/")[1] || repoDetails.name}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Visibility
                  </p>
                  <Badge variant={repoDetails.is_private ? "destructive" : "success"}>
                    {repoDetails.is_private ? "Private" : "Public"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analysis Results Summary */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">Analysis Status</h3>
            <AnalysisStatus />
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <QuickActionCard
                title="View Files"
                description="Browse repository file structure"
                icon={<Activity className="h-5 w-5" />}
                disabled={!isAuthenticated}
              />
              <QuickActionCard
                title="Architecture"
                description="View dependency graph"
                icon={<Code className="h-5 w-5" />}
                disabled={!isAuthenticated}
              />
              <QuickActionCard
                title="Code Evolution"
                description="Analyze git history and hotspots"
                icon={<GitFork className="h-5 w-5" />}
                disabled={!isAuthenticated}
              />
              <QuickActionCard
                title="Security Scan"
                description="Find vulnerabilities with Semgrep"
                icon={<AlertTriangle className="h-5 w-5" />}
                disabled={!isAuthenticated}
              />
              <QuickActionCard
                title="Contributors"
                description="View team and commit activity"
                icon={<Users className="h-5 w-5" />}
                disabled={!isAuthenticated}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  );
}

function QuickActionCard({ title, description, icon, disabled = false }: { title: string; description: string; icon: React.ReactNode; disabled?: boolean }) {
  return (
    <Card className={`hover:shadow-md transition-shadow cursor-pointer ${disabled ? "opacity-50 pointer-events-none" : ""}`}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${disabled ? "bg-muted" : "bg-primary/10"} ${disabled ? "text-muted-foreground" : "text-primary"}`}>
            {icon}
          </div>
          <div>
            <p className="font-medium">{title}</p>
            <p className="text-sm text-muted-foreground">{description}</p>
            {disabled && (
              <p className="text-xs text-amber-600 mt-1">Sign in to access</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}