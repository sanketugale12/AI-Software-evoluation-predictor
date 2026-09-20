import { useWorkspace } from "@/context/WorkspaceContext";
import { FindingsList } from "@/components/data/FindingsList";
import { Card, CardContent } from "@/components/ui/card";
import { StatCard } from "@/components/data/StatCard";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Shield, AlertTriangle, CheckCircle, Search } from "lucide-react";
import { formatNumber } from "@/lib/utils";

export function Security() {
  const { analysisResults, repoDetails } = useWorkspace();

  if (!repoDetails) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <Shield className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No repository loaded</p>
        </div>
      </div>
    );
  }

  if (!analysisResults?.results?.security) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <Shield className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No security scan data available</p>
          <p className="mt-1 text-xs">Run analysis to scan for vulnerabilities</p>
        </div>
      </div>
    );
  }

  const findings = analysisResults.results.security.findings || [];
  const critical = findings.filter((f) => f.severity === "CRITICAL").length;
  const error = findings.filter((f) => f.severity === "ERROR").length;
  const warning = findings.filter((f) => f.severity === "WARNING").length;
  const info = findings.filter((f) => f.severity === "INFO").length;

  const uniqueFiles = new Set(findings.map((f) => f.file)).size;

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-6">
        {/* Security Overview */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Security Scan Results
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
              <StatCard
                label="Total Findings"
                value={formatNumber(findings.length)}
                icon={<Search className="h-5 w-5" />}
              />
              <StatCard
                label="Critical"
                value={formatNumber(critical)}
                icon={<AlertTriangle className="h-5 w-5 text-red-500" />}
              />
              <StatCard
                label="Errors"
                value={formatNumber(error)}
                icon={<AlertTriangle className="h-5 w-5 text-orange-500" />}
              />
              <StatCard
                label="Warnings"
                value={formatNumber(warning)}
                icon={<AlertTriangle className="h-5 w-5 text-amber-500" />}
              />
              <StatCard
                label="Files Affected"
                value={formatNumber(uniqueFiles)}
                icon={<Shield className="h-5 w-5" />}
              />
            </div>

            {findings.length === 0 && (
              <div className="text-center py-12">
                <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
                <h4 className="mt-4 text-lg font-medium">No Security Issues Found</h4>
                <p className="mt-1 text-muted-foreground">
                  The security scan did not detect any vulnerabilities.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Findings List */}
        <Card>
          <CardContent className="pt-6">
            <FindingsList
              findings={findings}
              title="Security Findings"
              emptyMessage="No security findings"
            />
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  );
}