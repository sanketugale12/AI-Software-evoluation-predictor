"use client";

import { useEffect, useRef, useMemo } from "react";
import { ReactFlow, Background, Controls, MiniMap, BackgroundVariant, useReactFlow } from "@xyflow/react";
import type { Node, Edge, NodeTypes } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { cn } from "@/lib/utils";
import type { DependencyNode, DependencyEdge } from "@/types";

interface CustomNodeData {
  label: string;
  type?: string;
}

interface CustomNodeProps {
  data: CustomNodeData;
}

const CustomNode: React.FC<CustomNodeProps> = ({ data }) => {
  const { label, type, centrality } = data;

  // Color based on centrality (heat map)
  const getBgColor = () => {
    if (!centrality) return "bg-card";
    if (centrality > 0.5) return "bg-red-500/20 border-red-500 text-red-600";
    if (centrality > 0.2) return "bg-orange-500/20 border-orange-500 text-orange-600";
    if (centrality > 0.1) return "bg-yellow-500/20 border-yellow-500 text-yellow-600";
    return "bg-card";
  };

  return (
    <div
      className={cn(
        "px-3 py-1.5 rounded-lg border text-sm font-mono text-xs",
        "shadow-sm hover:shadow-md transition-shadow",
        "max-w-[200px] truncate",
        getBgColor()
      )}
      title={label}
    >
      {label}
    </div>
  );
};

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

interface DependencyGraphProps {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
}

export function DependencyGraph({ nodes, edges }: DependencyGraphProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { fitView } = useReactFlow();

  const flowNodes = useMemo(() => {
    return nodes.map((node, index) => ({
      id: node.id,
      type: "custom",
      position: { x: Math.random() * 800, y: Math.random() * 600 },
      data: { label: node.label || node.id, type: node.type, centrality: node.centrality },
    }));
  }, [nodes]);

  const flowEdges = useMemo(() => {
    return edges.map((edge, index) => ({
      id: `edge-${index}`,
      source: edge.source,
      target: edge.target,
      type: "default",
      animated: true,
      style: { strokeWidth: 1.5 },
    }));
  }, [edges]);

  useEffect(() => {
    if (flowNodes.length > 0) {
      const timer = setTimeout(() => {
        fitView({ padding: 0.2, duration: 500 });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [flowNodes, fitView]);

  if (nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <div className="text-center p-8">
          <svg className="mx-auto h-12 w-12 text-muted-foreground/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <p className="mt-4 text-sm">No dependency data available</p>
          <p className="text-xs">Run analysis to generate dependency graph</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        fitView={false}
        attributionPosition="bottom-right"
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
        <Controls />
        <MiniMap
          nodeColor={(node: any) => (node.type === "custom" ? "#3b82f6" : "#64748b")}
          maskColor="rgba(0,0,0,0.1)"
        />
      </ReactFlow>
    </div>
  );
}