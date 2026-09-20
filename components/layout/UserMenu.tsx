import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator, DropdownMenuLabel } from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LogOut, User, Github, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

export function UserMenu() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated || !user) {
    return (
      <Button variant="default" className="w-full justify-start gap-2" onClick={() => window.open(getGitHubLoginUrl(), "_blank", "width=600,height=700")}>
        <Github className="h-4 w-4" />
        <span>Sign in with GitHub</span>
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="w-full justify-start gap-2 h-10 px-3">
          <Avatar className="h-8 w-8">
            <AvatarImage src={user.avatar_url || undefined} alt={user.username} />
            <AvatarFallback>{user.username.charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>
          <div className="text-left flex-1 truncate">
            <p className="text-sm font-medium truncate">{user.username}</p>
            <p className="text-xs text-muted-foreground truncate">{user.email}</p>
          </div>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="font-medium">
          {user.username}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <a href={`https://github.com/${user.username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
            <Github className="h-4 w-4" />
            View GitHub Profile
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => logout()}>
          <LogOut className="h-4 w-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// Helper function to avoid circular import
function getGitHubLoginUrl(): string {
  return "http://127.0.0.1:8001/api/auth/github/login";
}