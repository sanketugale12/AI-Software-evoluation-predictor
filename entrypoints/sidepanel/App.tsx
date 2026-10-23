import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { AuthProvider } from "@/context/AuthContext";
import { Layout } from "@/components/layout/Layout";
import { Overview } from "@/pages/Overview";
import { Files } from "@/pages/Files";
import { Architecture } from "@/pages/Architecture";
import { Evolution } from "@/pages/Evolution";
import { Security } from "@/pages/Security";
import { Assistant } from "@/pages/Assistant";
import { Settings } from "@/pages/Settings";
import { ShellPage } from "@/pages/ShellPage";
import { useWorkspace } from "@/context/WorkspaceContext";
import { TooltipProvider } from "@/components/ui/tooltip";

function WorkspaceContent() {
  const { activePage } = useWorkspace();

  const pages = {
    overview: <Overview />,
    files: <Files />,
    architecture: <Architecture />,
    evolution: <Evolution />,
    security: <Security />,
    assistant: <Assistant />,
    settings: <Settings />,
    pull_requests: <ShellPage title="Pull Requests" description="Analyzing PR impact on architectural debt." />,
    issues: <ShellPage title="Issues" description="Linking issues to high-risk code hotspots." />,
    projects: <ShellPage title="Projects" description="Project-level technical debt tracking." />,
    actions: <ShellPage title="Actions" description="Monitoring CI/CD impact on code health." />,
    releases: <ShellPage title="Releases" description="Comparing architectural health between releases." />,
  };

  return (
    <Layout>
      {pages[activePage] || <Overview />}
    </Layout>
  );
}

function App() {
  return (
    <TooltipProvider>
      <AuthProvider>
        <WorkspaceProvider>
          <WorkspaceContent />
        </WorkspaceProvider>
      </AuthProvider>
    </TooltipProvider>
  );
}

export default App;