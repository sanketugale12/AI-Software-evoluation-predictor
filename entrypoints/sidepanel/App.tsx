import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { AuthProvider } from "@/context/AuthContext";
import { Layout } from "@/components/layout/Layout";
import { Overview } from "@/pages/Overview";
import { Files } from "@/pages/Files";
import { Architecture } from "@/pages/Architecture";
import { Evolution } from "@/pages/Evolution";
import { Security } from "@/pages/Security";
import { Assistant } from "@/pages/Assistant";
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