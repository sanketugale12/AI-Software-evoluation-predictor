import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    label: string;
  };
  className?: string;
}

export function StatCard({ label, value, icon, trend, className }: StatCardProps) {
  return (
    <div className={cn("p-4 rounded-lg border bg-card", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {label}
          </p>
          <p className="mt-1 text-2xl font-bold">{value}</p>
          {trend && (
            <p className={cn("mt-1 text-xs", trend.value >= 0 ? "text-green-600" : "text-red-600")}>
              {trend.value >= 0 ? "▲" : "▼"} {Math.abs(trend.value)}% {trend.label}
            </p>
          )}
        </div>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
    </div>
  );
}