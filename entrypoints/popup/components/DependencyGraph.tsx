import { ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

export default function DependencyGraph({ nodes, edges }: any) {
  const flowNodes = nodes.map((node: any) => ({
    id: node.id,
    position: { x: 0, y: 0 },
    data: { label: node.label },
  }));

  const flowEdges = edges.map((edge: any, index: number) => ({
    id: `edge-${index}`,
    source: edge.source,
    target: edge.target,
  }));

  return (
    <div style={{ height: 500 }}>
      <ReactFlow nodes={flowNodes} edges={flowEdges} fitView />
    </div>
  );
}
