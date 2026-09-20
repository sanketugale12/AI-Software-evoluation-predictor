import { useWorkspace } from "@/context/WorkspaceContext";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bot, Sparkles, MessageSquare, Code, Zap, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Assistant() {
  const { repoDetails, analysisResults } = useWorkspace();

  if (!repoDetails) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <Bot className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm">No repository loaded</p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-6">
        {/* AI Assistant Header */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Bot className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">ASEP Assistant</h3>
                <p className="text-sm text-muted-foreground">
                  AI-powered code analysis and assistance
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Chat Interface Placeholder */}
        <Card className="flex-1 flex flex-col">
          <div className="flex-1 flex flex-col p-6">
            <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground">
              <MessageSquare className="mx-auto h-16 w-16 text-muted-foreground/30" />
              <h4 className="mt-4 text-lg font-medium">Chat Coming Soon</h4>
              <p className="mt-2 max-w-md">
                The AI assistant will help you understand your codebase, suggest improvements,
                and answer questions about the repository.
              </p>
            </div>

            {/* Quick Actions */}
            <div className="mt-8 w-full max-w-md">
              <h5 className="text-sm font-medium text-muted-foreground mb-3">
                Suggested Actions
              </h5>
              <div className="grid grid-cols-2 gap-3">
                <QuickAction
                  title="Explain Architecture"
                  description="Get an overview of the codebase structure"
                  icon={<Code className="h-4 w-4" />}
                />
                <QuickAction
                  title="Find Bugs"
                  description="Identify potential issues in the code"
                  icon={<Lightbulb className="h-4 w-4" />}
                />
                <QuickAction
                  title="Refactor Suggestions"
                  description="Get ideas for improving code quality"
                  icon={<Zap className="h-4 w-4" />}
                />
                <QuickAction
                  title="Security Review"
                  description="Analyze findings from security scan"
                  icon={<Sparkles className="h-4 w-4" />}
                />
              </div>
            </div>
          </div>

          {/* Input Area */}
          <div className="border-t p-4">
            <div className="flex gap-2 max-w-2xl mx-auto">
              <Input
                placeholder="Ask a question about the repository..."
                className="flex-1"
                disabled
              />
              <Button disabled variant="default">
                <Sparkles className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-2">
              AI features will be available after backend integration
            </p>
          </div>
        </Card>

        {/* Context Info */}
        <Card>
          <CardContent className="pt-6">
            <h4 className="font-medium mb-3">Available Context</h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <ContextItem label="Repository" value={repoDetails.name} />
              <ContextItem
                label="Files"
                value={analysisResults?.results?.history ? "Analyzed" : "Not analyzed"}
              />
              <ContextItem
                label="Dependencies"
                value={analysisResults?.results?.hotspots ? "Mapped" : "Not mapped"}
              />
              <ContextItem
                label="Security"
                value={analysisResults?.results?.security ? "Scanned" : "Not scanned"}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  );
}

function QuickAction({ title, description, icon }: { title: string; description: string; icon: React.ReactNode }) {
  return (
    <Button variant="outline" className="h-auto p-3 text-left justify-start gap-3">
      <div className="p-1.5 rounded bg-primary/10 text-primary">{icon}</div>
      <div className="text-xs">
        <p className="font-medium">{title}</p>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </Button>
  );
}

function ContextItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-muted/50">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}