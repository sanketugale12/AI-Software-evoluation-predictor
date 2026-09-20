import { useWorkspace } from "@/context/WorkspaceContext";
import { HotspotTable } from "@/components/data/HotspotTable";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StatCard } from "@/components/data/StatCard";
import { Separator } from "@/components/ui/separator";
import { GitGraph, Users, Clock, TrendingUp, FileText, Activity } from "lucide-react";
import { formatNumber } from "@/lib/utils";

export function Evolution() {
  const { analysisResults, repoDetails } = useWorkspace();

  if (!repoDetails) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <GitGraph className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No repository loaded</p>
        </div>
      </div>
    );
  }

  if (!analysisResults?.results?.history && !analysisResults?.results?.hotspots) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <GitGraph className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No evolution data available</p>
          <p className="mt-1 text-xs">Run analysis to see git history and hotspots</p>
        </div>
      </div>
    );
  }

  const history = analysisResults.results.history;
  const hotspots = analysisResults.results.hotspots || [];
  const temporalChurn = history?.temporal_churn || {};

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-6">
        {/* Git Metrics */}
        {history && (
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <GitGraph className="h-5 w-5" />
                Git History Metrics
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <StatCard
                  label="Total Commits"
                  value={formatNumber(history.total_commits)}
                  icon={<FileText className="h-5 w-5" />}
                />
                <StatCard
                  label="Contributors"
                  value={history.metrics.contributor_count}
                  icon={<Users className="h-5 w-5" />}
                />
                <StatCard
                  label="Commit Frequency"
                  value={`${history.metrics.commit_frequency.toFixed(1)}/day`}
                  icon={<Clock className="h-5 w-5" />}
                />
                <StatCard
                  label="Total Churn"
                  value={formatNumber(history.metrics.total_churn)}
                  icon={<TrendingUp className="h-5 w-5" />}
                />
              </div>

              <Separator className="my-4" />

              {/* Evolution Timeline (Custom SVG Sparkline) */}
              <div className="mb-6">
                <h4 className="font-medium mb-3 flex items-center gap-2 text-sm">
                  <Activity className="h-4 w-4" />
                  Temporal Churn (Monthly)
                </h4>
                <div className="h-32 w-full bg-muted/30 rounded-lg relative flex items-end gap-1 p-2 border">
                  {Object.entries(temporalChurn)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .map(([month, data]: [string, any], i) => {
                      const total = data.added + data.deleted;
                      const max = Math.max(...Object.values(temporalChurn).map((d: any) => d.added + d.deleted), 1);
                      const height = (total / max) * 100;
                      return (
                        <div key={month} className="flex-1 group relative flex flex-col justify-end h-full">
                          <div
                            className="bg-primary/60 rounded-t-sm transition-all hover:bg-primary"
                            style={{ height: `${height}%` }}
                          />
                          <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity text-[10px] whitespace-nowrap bg-popover px-1 rounded border">
                            {month}: {formatNumber(total)}
                          </div>
                        </div>
                      );
                    })}
                </div>
                <div className="flex justify-between mt-1 text-[10px] text-muted-foreground">
                  <span>Oldest</span>
                  <span>Recent Activity Timeline</span>
                  <span>Now</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-muted-foreground">Commits (30 days)</p>
                  <p className="text-2xl font-bold">{history.metrics.recent_activity}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-muted-foreground">Project Age</p>
                  <p className="text-2xl font-bold">
                    {history.commits.length > 0
                      ? Math.ceil(
                          (new Date(history.commits[0].date).getTime() -
                            new Date(history.commits[history.commits.length - 1].date).getTime()) /
                            (1000 * 60 * 60 * 24 * 30)
                        )
                      : 0} months
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Hotspots */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Code Hotspots
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Files with high risk based on churn, complexity, centrality, and security.
            </p>
            <HotspotTable hotspots={hotspots} />
          </CardContent>
        </Card>

        {/* Top Contributors */}
        {history && history.commits.length > 0 && (
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Users className="h-5 w-5" />
                Top Contributors
              </h3>
              <ContributorList commits={history.commits} />
            </CardContent>
          </Card>
        )}
      </div>
    </ScrollArea>
  );
}

function ContributorList({ commits }: { commits: any[] }) {
  const contributorStats = commits.reduce((acc, commit) => {
    const author = commit.author;
    if (!acc[author]) {
      acc[author] = { commits: 0, firstCommit: commit.date, lastCommit: commit.date };
    }
    acc[author].commits++;
    if (new Date(commit.date) < new Date(acc[author].firstCommit)) {
      acc[author].firstCommit = commit.date;
    }
    if (new Date(commit.date) > new Date(acc[author].lastCommit)) {
      acc[author].lastCommit = commit.date;
    }
    return acc;
  }, {} as Record<string, { commits: number; firstCommit: string; lastCommit: string }>);

  const sortedContributors = Object.entries(contributorStats)
    .sort(([, a], [, b]) => b.commits - a.commits)
    .slice(0, 10);

  return (
    <div className="space-y-2">
      {sortedContributors.map(([author, stats], index) => (
        <div key={author} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-sm">
              {author.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-medium text-sm">{author}</p>
              <p className="text-xs text-muted-foreground">
                {stats.commits} commits • {new Date(stats.lastCommit).toLocaleDateString()}
              </p>
            </div>
          </div>
          <span className="text-sm font-medium text-primary">{stats.commits}</span>
        </div>
      ))}
    </div>
  );
}