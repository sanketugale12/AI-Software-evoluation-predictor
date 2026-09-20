from typing import List, Dict, Any, Optional
import numpy as np

class EvolutionAnalyzer:
    def __init__(self):
        # Weights for risk score: Churn, Complexity, Centrality, Security
        self.weights = {
            "churn": 0.3,
            "complexity": 0.3,
            "centrality": 0.3,
            "security": 0.1
        }

    def normalize(self, value: float, max_val: float) -> float:
        if max_val == 0:
            return 0.0
        return min(value / max_val, 1.0)

    def analyze(self, git_data: Dict[str, Any], arch_data: Dict[str, Any], security_data: List[Any]) -> List[Dict[str, Any]]:
        """
        Correlates Git history, architecture centrality, and security findings
        to identify hotspots.
        """
        file_changes = git_data.get("file_changes", {})
        # arch_data is expected to be a dict of file_path -> centrality_score
        centrality_map = arch_data if isinstance(arch_data, dict) else {}

        # Map security findings to files
        security_map = defaultdict(int)
        for finding in security_data:
            path = finding.get("file_path")
            if path:
                security_map[path] += 1

        # Find max values for normalization
        max_churn = max([f["added_lines"] + f["deleted_lines"] for f in file_changes.values()], default=1)
        max_complexity = max([f["complexity"] for f in file_changes.values()], default=1)
        max_centrality = max(centrality_map.values(), default=1)
        max_sec = max(security_map.values(), default=1)

        hotspots = []
        for path, data in file_changes.items():
            churn = data["added_lines"] + data["deleted_lines"]
            complexity = data["complexity"]
            centrality = centrality_map.get(path, 0.0)
            sec_count = security_map.get(path, 0)

            # Calculate normalized scores
            n_churn = self.normalize(churn, max_churn)
            n_complexity = self.normalize(complexity, max_complexity)
            n_centrality = self.normalize(centrality, max_centrality)
            n_sec = self.normalize(sec_count, max_sec)

            # Final Risk Score
            risk_score = (
                self.weights["churn"] * n_churn +
                self.weights["complexity"] * n_complexity +
                self.weights["centrality"] * n_centrality +
                self.weights["security"] * n_sec
            )

            # Determine status
            if risk_score > 0.7:
                status = "Critical"
            elif risk_score > 0.4:
                status = "Review"
            elif risk_score > 0.2:
                status = "Monitor"
            else:
                status = "Normal"

            hotspots.append({
                "file_path": path,
                "risk_score": round(risk_score, 3),
                "status": status,
                "risk_factors": {
                    "churn": {"value": churn, "impact": "High" if n_churn > 0.6 else "Med" if n_churn > 0.3 else "Low"},
                    "complexity": {"value": complexity, "impact": "High" if n_complexity > 0.6 else "Med" if n_complexity > 0.3 else "Low"},
                    "centrality": {"value": centrality, "impact": "High" if n_centrality > 0.6 else "Med" if n_centrality > 0.3 else "Low"},
                    "security": {"finding_count": sec_count, "impact": "High" if n_sec > 0.6 else "Med" if n_sec > 0.3 else "Low"}
                },
                "knowledge_silo_risk": data.get("concentration_ratio", 0),
                "co_changed_with": git_data.get("co_changes", {}).get(path, [])
            })

        # Sort by risk score descending
        return sorted(hotspots, key=lambda x: x["risk_score"], reverse=True)

from collections import defaultdict
