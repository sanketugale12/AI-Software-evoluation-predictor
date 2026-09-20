from backend.app.analyzers.git_history import analyze_git_history
from backend.app.analyzers.technical_debt import run_complexity_analysis


def analyze_hotspots(repo_path: str, weights: dict = None):
    """
    Combines Git history and code complexity to identify project hotspots.

    Weights default to:
    - Complexity (wc): 0.4
    - Frequency (wf): 0.4
    - Churn (wh): 0.2
    """
    if weights is None:
        weights = {"wc": 0.4, "wf": 0.4, "wh": 0.2}

    # 1. Gather data from existing analyzers
    git_data = analyze_git_history(repo_path)
    complexity_data = run_complexity_analysis(repo_path)

    file_changes = git_data.get("file_changes", {})

    # 2. Aggregate complexity per file
    # radon returns a list of blocks per file. We'll use the sum of complexity as the file metric.
    file_complexity = {}
    for path, blocks in complexity_data.items():
        total_comp = sum(block.get("complexity", 0) for block in blocks)
        file_complexity[path] = total_comp

    # 3. Collect all files involved in either analysis
    all_files = set(file_changes.keys()).union(set(file_complexity.keys()))

    # 4. Normalize and Calculate
    # We need max values for normalization
    max_comp = max([file_complexity.get(f, 0) for f in all_files], default=1) or 1
    max_freq = max([file_changes.get(f, {}).get("commits", 0) for f in all_files], default=1) or 1
    max_churn = max([
        file_changes.get(f, {}).get("added_lines", 0) + file_changes.get(f, {}).get("deleted_lines", 0)
        for f in all_files
    ], default=1) or 1

    hotspots = []
    for f in all_files:
        comp = file_complexity.get(f, 0)
        freq = file_changes.get(f, {}).get("commits", 0)
        churn = file_changes.get(f, {}).get("added_lines", 0) + file_changes.get(f, {}).get("deleted_lines", 0)

        # Normalized values (0.0 to 1.0)
        norm_c = comp / max_comp
        norm_f = freq / max_freq
        norm_h = churn / max_churn

        # Hotspot Score formula
        score = (weights["wc"] * norm_c) + (weights["wf"] * norm_f) + (weights["wh"] * norm_h)

        # Heuristic Status (Transparent rules)
        status = "Normal"
        if score > 0.7 or (norm_c > 0.8 and norm_f > 0.8):
            status = "Review"
        elif score > 0.4:
            status = "Monitor"

        hotspots.append({
            "file": f,
            "complexity": comp,
            "changes": freq,
            "churn": churn,
            "score": round(score, 3),
            "status": status
        })

    # Sort by score descending
    hotspots.sort(key=lambda x: x["score"], reverse=True)

    return hotspots
