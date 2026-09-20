from pydriller import Repository
import lizard
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os

def analyze_git_history(repo_path: str):
    commits = []
    file_changes = {}
    authors = set()

    # Co-occurrence matrix: (file_a, file_b) -> count
    co_changes = defaultdict(int)
    # Author mapping per file: file -> { author: commit_count }
    file_authors = defaultdict(lambda: defaultdict(int))
    # First commit date per file: file -> date
    file_first_commit = {}
    # Temporal churn: month_key -> {added, deleted}
    temporal_churn = defaultdict(lambda: {"added": 0, "deleted": 0})

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    recent_commits_count = 0

    repo = Repository(repo_path)
    # traverse_commits yields commits from newest to oldest
    commit_list = list(repo.traverse_commits())

    if not commit_list:
        return {
            "total_commits": 0,
            "commits": [],
            "file_changes": {},
            "metrics": {}
        }

    for commit in commit_list:
        commit_date = commit.author_date
        if commit_date.tzinfo is None:
            commit_date = commit_date.replace(tzinfo=timezone.utc)

        commits.append({
            "hash": commit.hash,
            "message": commit.msg,
            "author": commit.author.name,
            "date": commit_date.isoformat(),
        })

        authors.add(commit.author.name)

        if commit_date >= thirty_days_ago:
            recent_commits_count += 1

        # Extract temporal data for the timeline (YYYY-MM)
        month_key = commit_date.strftime("%Y-%m")

        modified_paths = []
        for modification in commit.modified_files:
            path = modification.new_path or modification.old_path
            if not path:
                continue

            modified_paths.append(path)

            if path not in file_changes:
                file_changes[path] = {
                    "commits": 0,
                    "added_lines": 0,
                    "deleted_lines": 0,
                    "complexity": 0,
                    "hotspot_score": 0,
                }

            file_changes[path]["commits"] += 1
            added = modification.added_lines or 0
            deleted = modification.deleted_lines or 0
            file_changes[path]["added_lines"] += added
            file_changes[path]["deleted_lines"] += deleted

            # Update temporal churn
            temporal_churn[month_key]["added"] += added
            temporal_churn[month_key]["deleted"] += deleted

            # Track author for concentration ratio
            file_authors[path][commit.author.name] += 1

            # Track first commit (commit_list is newest to oldest, so the last one we see is the first)
            file_first_commit[path] = commit_date

        # Calculate co-changes for this commit
        for i in range(len(modified_paths)):
            for j in range(i + 1, len(modified_paths)):
                p1, p2 = modified_paths[i], modified_paths[j]
                # Sort to ensure consistency in key
                pair = tuple(sorted([p1, p2]))
                co_changes[pair] += 1

    # Calculate time-based frequency
    # commit_list is newest to oldest.
    # Index 0 is newest, index -1 is oldest.
    end_date = commit_list[0].author_date
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    start_date = commit_list[-1].author_date
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    duration_days = (end_date - start_date).days or 1
    commit_frequency = len(commits) / duration_days

    # Calculate Complexity and add Advanced Git Metrics to file_changes
    for path, data in file_changes.items():
        # 1. Complexity (Current version)
        try:
            full_path = os.path.join(repo_path, path)
            if os.path.exists(full_path):
                analysis = lizard.analyze_file(full_path)
                if analysis.function_list:
                    avg_complexity = sum(f.cyclomatic_complexity for f in analysis.function_list) / len(analysis.function_list)
                else:
                    avg_complexity = 1
                data["complexity"] = avg_complexity
                data["hotspot_score"] = data["commits"] * avg_complexity
        except Exception:
            data["complexity"] = 1
            data["hotspot_score"] = data["commits"] * 1

        # 2. Contributor Concentration Ratio
        authors_map = file_authors[path]
        if authors_map:
            top_author_commits = max(authors_map.values())
            total_commits = sum(authors_map.values())
            data["concentration_ratio"] = top_author_commits / total_commits if total_commits > 0 else 0
        else:
            data["concentration_ratio"] = 0

        # 3. File Age (days from first commit to now)
        if path in file_first_commit:
            first_date = file_first_commit[path]
            data["age_days"] = (now - first_date).days
        else:
            data["age_days"] = 0

    # Process co-changes into a usable format: path -> [{file, frequency}]
    file_co_changes = defaultdict(list)
    for (p1, p2), count in co_changes.items():
        file_co_changes[p1].append({"file": p2, "frequency": count})
        file_co_changes[p2].append({"file": p1, "frequency": count})

    # Sort co-changes by frequency
    for path in file_co_changes:
        file_co_changes[path].sort(key=lambda x: x["frequency"], reverse=True)

    return {
        "total_commits": len(commits),
        "commits": commits,
        "file_changes": file_changes,
        "co_changes": dict(file_co_changes),
        "temporal_churn": dict(temporal_churn),
        "metrics": {
            "commit_frequency": commit_frequency,
            "contributor_count": len(authors),
            "recent_activity": recent_commits_count,
            "total_churn": sum(f["added_lines"] + f["deleted_lines"] for f in file_changes.values()),
        }
    }
