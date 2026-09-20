import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { cn, getSeverityColor } from "@/lib/utils";
import type { SecurityFinding } from "@/types";

interface FindingsListProps {
  findings: SecurityFinding[];
  title?: string;
  emptyMessage?: string;
}

export function FindingsList({ findings, title = "Findings", emptyMessage = "No findings" }: FindingsListProps) {
  if (findings.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p className="text-sm">{emptyMessage}</p>
      </div>
    );
  }

  // Group findings by file
  const findingsByFile = findings.reduce((acc, finding) => {
    const file = finding.file || "Unknown";
    if (!acc[file]) acc[file] = [];
    acc[file].push(finding);
    return acc;
  }, {} as Record<string, SecurityFinding[]>);

  return (
    <div className="flex h-full flex-col">
      {title && (
        <div className="px-4 py-2 border-b text-sm font-medium">
          {title} ({findings.length})
        </div>
      )}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {Object.entries(findingsByFile).map(([file, fileFindings]) => (
            <div key={file} className="space-y-2">
              <div className="px-2 py-1 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {file}
              </div>
              {fileFindings.map((finding, index) => (
                <div
                  key={`${file}-${index}`}
                  className={cn(
                    "p-3 rounded-lg border",
                    getSeverityColor(finding.severity)
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Badge variant={finding.severity.toLowerCase() as any}>
                          {finding.severity}
                        </Badge>
                        {finding.rule_id && (
                          <span className="text-xs font-mono text-muted-foreground">
                            {finding.rule_id}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm">{finding.message}</p>
                      {finding.line && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          Line {finding.line}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}