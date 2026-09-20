import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn, getHotspotStatusColor, formatNumber } from "@/lib/utils";
import type { HotspotData } from "@/types";
import { AlertTriangle, AlertCircle } from "lucide-react";

interface HotspotTableProps {
  hotspots: any[]; // Using any as we extended the schema in backend
}

export function HotspotTable({ hotspots }: HotspotTableProps) {
  if (hotspots.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p className="text-sm">No hotspot data available</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="p-4 border-b">
        <h3 className="text-sm font-medium">Code Hotspots</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Files with high risk based on churn, complexity, centrality, and security.
        </p>
      </div>
      <ScrollArea className="flex-1">
        <table className="w-full">
          <thead className="sticky top-0 bg-background z-10">
            <tr className="border-b text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
              <th className="pb-2 pr-4">File</th>
              <th className="pb-2 pr-4 text-right">Complexity</th>
              <th className="pb-2 pr-4 text-right">Centrality</th>
              <th className="pb-2 pr-4 text-right">Churn</th>
              <th className="pb-2 pr-4 text-right">Risk Score</th>
              <th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {hotspots.map((hotspot, index) => {
              const factors = hotspot.risk_factors || {};
              const isSilo = hotspot.knowledge_silo_risk > 0.8;

              return (
                <tr key={`${hotspot.file_path}-${index}`} className="hover:bg-accent/50 group">
                  <td className="py-2 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="font-mono text-xs truncate max-w-[200px]" title={hotspot.file_path}>
                        {hotspot.file_path}
                      </div>
                      {isSilo && (
                        <div className="relative group/silo">
                          <AlertTriangle className="h-3 w-3 text-amber-500" title="Knowledge Silo Risk" />
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="py-2 pr-4 text-right font-mono text-xs text-muted-foreground">
                    <span className={cn(
                      factors.complexity?.impact === "High" && "text-red-500 font-bold",
                      factors.complexity?.impact === "Med" && "text-amber-500"
                    )}>
                      {factors.complexity?.value.toFixed(1) || "1.0"}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-right font-mono text-xs text-muted-foreground">
                    <span className={cn(
                      factors.centrality?.impact === "High" && "text-red-500 font-bold",
                      factors.centrality?.impact === "Med" && "text-amber-500"
                    )}>
                      {factors.centrality?.value.toFixed(2) || "0.00"}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-right font-mono text-xs text-muted-foreground">
                    <span className={cn(
                      factors.churn?.impact === "High" && "text-red-500 font-bold",
                      factors.churn?.impact === "Med" && "text-amber-500"
                    )}>
                      {formatNumber(factors.churn?.value || 0)}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-right font-mono text-xs font-medium">
                    {(hotspot.risk_score * 100).toFixed(1)}%
                  </td>
                  <td className="py-2">
                    <Badge
                      variant="outline"
                      className={cn(getHotspotStatusColor(hotspot.status))}
                    >
                      {hotspot.status}
                    </Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </ScrollArea>
    </div>
  );
}