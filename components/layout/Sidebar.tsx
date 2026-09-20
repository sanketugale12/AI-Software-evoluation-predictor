import { useWorkspace } from "@/context/WorkspaceContext";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  FileText,
  GitBranch,
  GitGraph,
  Shield,
  Bot,
  ChevronLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { UserMenu } from "./UserMenu";

const navigation = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "files", label: "Files", icon: FileText },
  { id: "architecture", label: "Architecture", icon: GitBranch },
  { id: "evolution", label: "Evolution", icon: GitGraph },
  { id: "security", label: "Security", icon: Shield },
  { id: "assistant", label: "Assistant", icon: Bot },
] as const;

type NavItem = (typeof navigation)[number];

export function Sidebar() {
  const { activePage, setActivePage, repoUrl, repoDetails } = useWorkspace();
  const { isAuthenticated } = useAuth();

  return (
    <div className="flex h-full flex-col border-r bg-card">
      {/* Header */}
      <div className="flex h-16 items-center justify-between border-b px-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">A</span>
          </div>
          <span className="font-semibold text-sm">ASEP</span>
        </div>
        {repoUrl && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => window.open(repoUrl, "_blank")}
            title="Open repository on GitHub"
          >
            <ChevronLeft className="h-4 w-4 rotate-180" />
          </Button>
        )}
      </div>

      <Separator />

      {/* Repo Info */}
      {repoDetails && (
        <div className="p-4 border-b">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
            Repository
          </p>
          <p className="text-sm font-medium truncate">{repoDetails.name}</p>
          <p className="text-xs text-muted-foreground truncate mt-1">
            {repoDetails.description || "No description"}
          </p>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto scrollbar-thin">
        {navigation.map((item: NavItem) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <Button
              key={item.id}
              variant={isActive ? "default" : "ghost"}
              className={cn(
                "w-full justify-start gap-3 text-sm",
                isActive && "shadow-sm"
              )}
              onClick={() => setActivePage(item.id)}
              disabled={!isAuthenticated && item.id !== "overview"}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {item.label}
              {!isAuthenticated && item.id !== "overview" && (
                <span className="ml-auto text-xs text-muted-foreground">🔒</span>
              )}
            </Button>
          );
        })}
      </nav>

      <Separator />

      {/* User Menu */}
      <div className="p-2 border-t">
        <UserMenu />
      </div>

      <Separator />

      {/* Footer */}
      <div className="p-2 border-t">
        <p className="text-xs text-muted-foreground text-center">
          AI Software Engineering Platform
        </p>
      </div>
    </div>
  );
}