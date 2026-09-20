import json
import subprocess


def run_complexity_analysis(repo_path: str):
    result = subprocess.run(
        ["radon", "cc", repo_path, "-s", "-j"],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )

    return json.loads(result.stdout)
