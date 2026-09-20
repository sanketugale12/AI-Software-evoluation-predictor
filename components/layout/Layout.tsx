import { Sidebar } from "./Sidebar";
import { PageHeader } from "./PageHeader";
import { cn } from "@/lib/utils";

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-full bg-background font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <PageHeader />
        <main className="flex-1 overflow-auto p-4">{children}</main>
      </div>
    </div>
  );
}