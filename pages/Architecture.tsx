import { useWorkspace } from "@/context/WorkspaceContext";
import { DependencyGraph } from "@/components/data/DependencyGraph";
import { Card, CardContent } from "@/components/ui/card";
import { Code, RefreshCw, Maximize, AlertTriangle, Network, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { fetchArchitectureMetrics } from "@/services/api";

export function Architecture() {
  const { dependencyGraph, repoDetails, isLoading } = useWorkspace();
  const [fullscreen, setFullscreen] = useState(false);
  const [archMetrics, setArchMetrics] = useState<any>(null);
  const [fetchingMetrics, setFetchingMetrics] = useState(false);

  useEffect(() => {
    async function loadMetrics() {
      if (repoDetails?.id) {
        setFetchingMetrics(true);
        try {
          const metrics = await fetchArchitectureMetrics(repoDetails.id);
          setArchMetrics(metrics);
        } catch (e) {
          console.error("Failed to fetch architecture metrics:", e);
        } finally {
          setFetchingMetrics(false);
        }
      }
    }
    loadMetrics();
  }, [repoDetails]);

  if (!repoDetails) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <Code className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No repository loaded</p>
        </div>
      </div>
    );
  }

  if (!dependencyGraph || dependencyGraph.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <Code className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No dependency data available</p>
          <p className="mt-1 text-xs">Run analysis to generate dependency graph</p>
          <Button
            className="mt-4"
            variant="outline"
            size="sm"
            onClick={() => window.dispatchEvent(new CustomEvent("trigger-analysis"))}
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Run Analysis
          </Button>
        </div>
      </div>
    );
  }

  const stats = {
    nodes: dependencyGraph.nodes.length,
    edges: dependencyGraph.edges.length,
  };

  return (
    <div className="flex h-full">
      <div className="flex-1 relative">
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <Button variant="ghost" size="icon" onClick={() => setFullscreen(!fullscreen)}>
            {fullscreen ? <Maximize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
          </Button>
        </div>
        <Card className="h-full">
          <CardContent className="p-0 h-full">
            <DependencyGraph
              nodes={dependencyGraph.nodes}
              edges={dependencyGraph.edges}
            />
          </CardContent>
        </Card>
      </div>

      {/* Stats Panel */}
      <div className="w-64 border-l bg-card p-4 overflow-y-auto">
        <h3 className="font-medium mb-4">Architecture Intelligence</h3>

        <div className="space-y-3 mb-6">
          <StatItem label="Files (Nodes)" value={stats.nodes} icon={<Code className="h-4 w-4" />} />
          <StatItem label="Dependencies (Edges)" value={stats.edges} icon={<RefreshCw className="h-4 w-4" />} />
        </div>

        {fetchingMetrics ? (
          <div className="text-xs text-muted-foreground animate-pulse">Calculating metrics...</div>
        ) : archMetrics ? (
          <div className="space-y-4">
            <div className="p-3 rounded-lg bg-muted/50 space-y-3">
              <MetricRow
                label="Circular Deps"
                value={archMetrics.circular_dependencies?.length || 0}
                icon={<AlertTriangle className="h-3 w-3 text-yellow-500" />}
                color={archMetrics.circular_dependencies?.length > 0 ? "text-yellow-600" : ""}
              />
              <MetricRow
                label="God Objects"
                value={archMetrics.god_objects?.length || 0}
                icon={<Target className="h-3 w-3 text-red-500" />}
                color={archMetrics.god_objects?.length > 0 ? "text-red-600" : ""}
              />
              <MetricRow
                label="Connectivity"
                value={`${Math.round((stats.edges / (stats.nodes * (stats.nodes - 1) || 1)) * 100)}%`}
                icon={<Network className="h-3 w-3 text-blue-500" />}
              />
            </div>
          </div>
        ) : (
          <div className="text-xs text-muted-foreground italic">No metrics available</div>
        )}

        <div className="mt-6 pt-4 border-t">
          <h4 className="font-medium mb-2 text-sm">Legend</h4>
          <div className="space-y-2 text-xs text-muted-foreground">
            <LegendItem color="#3b82f6" label="Source Files" />
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-gradient-to-r from-yellow-500 via-orange-500 to-red-500" />
              <span>Centrality Heatmap</span>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t">
          <h4 className="font-medium mb-2 text-sm">Controls</h4>
          <div className="space-y-2 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">Scroll</kbd>
              <span>Pan</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">Wheel</kbd>
              <span>Zoom</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">Click</kbd>
              <span>Select Node</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatItem({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      <div className="p-2 rounded bg-background">{icon}</div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xl font-bold">{value}</p>
      </div>
    </div>
  );
}

function MetricRow({ label, value, icon, color = "" }: { label: string; value: any; icon: React.ReactNode; color?: string }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <div className="flex items-center gap-2 text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <span className={`font-bold ${color}`}>{value}</span>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
      <span>{label}</span>
    </div>
  );
}