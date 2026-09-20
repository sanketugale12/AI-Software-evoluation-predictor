import networkx as nx
from typing import List, Dict, Any, Tuple
from .ast_analyzer import SymbolRecord, SymbolType

class ArchitectureIntelligence:
    def __init__(self, symbols: List[SymbolRecord]):
        self.symbols = symbols
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()

        # Add all symbols as nodes
        for symbol in self.symbols:
            graph.add_node(symbol.id, name=symbol.name, type=symbol.type)

        # Add dependency edges
        for symbol in self.symbols:
            for dep_id in symbol.dependencies:
                if graph.has_node(dep_id):
                    graph.add_edge(symbol.id, dep_id)

        return graph

    def calculate_metrics(self) -> Dict[str, Any]:
        if not self.graph.nodes:
            return {}

        # 1. Circular Dependencies
        cycles = list(nx.simple_cycles(self.graph))

        # 2. Centrality
        betweenness = nx.betweenness_centrality(self.graph)
        pagerank = nx.pagerank(self.graph)

        # 3. Fan-in / Fan-out
        metrics_per_node = {}
        for node in self.graph.nodes:
            metrics_per_node[node] = {
                "fan_in": self.graph.in_degree(node),
                "fan_out": self.graph.out_degree(node),
                "betweenness": betweenness.get(node, 0),
                "pagerank": pagerank.get(node, 0)
            }

        # 4. Identify Isolated Modules
        isolated = [node for node in self.graph.nodes if self.graph.degree(node) == 0]

        # Find most central module
        most_central = max(pagerank, key=pagerank.get) if pagerank else None

        return {
            "summary": {
                "total_symbols": self.graph.number_of_nodes(),
                "total_dependencies": self.graph.number_of_edges(),
                "cycle_count": len(cycles),
                "most_central_symbol": most_central,
                "isolated_count": len(isolated)
            },
            "cycles": cycles,
            "node_metrics": metrics_per_node,
            "isolated_modules": isolated
        }

def analyze_architecture(symbols: List[SymbolRecord]) -> Dict[str, Any]:
    intelligence = ArchitectureIntelligence(symbols)
    return intelligence.calculate_metrics()
