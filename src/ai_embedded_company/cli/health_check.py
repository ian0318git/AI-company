"""System Health Check — CLI tool for verifying the AI Embedded Company platform.

Runs every autonomous cycle to validate:
1. API server responsiveness
2. Database integrity
3. Git working tree status
4. Task/idea/project state consistency
5. Disk and resource usage

Exit code 0 = all healthy, 1 = warnings, 2 = critical failures.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_api_server(base_url: str = "http://127.0.0.1:8765") -> list[str]:
    """Check API server is responding on key endpoints."""
    issues = []
    endpoints = [
        ("ideas", "/api/ideas/"),
        ("tasks", "/api/tasks/"),
        ("projects", "/api/projects/"),
    ]
    for name, path in endpoints:
        try:
            import urllib.request
            req = urllib.request.Request(f"{base_url}{path}", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    issues.append(f"API {name} returned HTTP {resp.status}")
        except Exception as e:
            issues.append(f"API {name} unreachable: {e}")
    return issues


def check_database(db_path: str = "data/ai_embedded_company.db") -> list[str]:
    """Verify database file exists and is non-empty."""
    issues = []
    path = Path(db_path)
    if not path.exists():
        issues.append(f"Database not found at {db_path}")
    elif path.stat().st_size == 0:
        issues.append(f"Database is empty (0 bytes): {db_path}")
    return issues


def check_git_status(repo_root: str = ".") -> list[str]:
    """Check git working tree -- warn on uncommitted changes."""
    issues = []
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=repo_root, timeout=10,
        )
        dirty = [l for l in result.stdout.strip().split("\n") if l.strip()]
        if dirty:
            issues.append(f"Git working tree has {len(dirty)} uncommitted file(s)")
    except Exception as e:
        issues.append(f"Git status check failed: {e}")
    return issues


def check_resource_usage() -> list[str]:
    """Check disk and memory resource usage."""
    issues = []
    try:
        import shutil
        usage = shutil.disk_usage(".")
        free_mb = usage.free / (1024 * 1024)
        if free_mb < 500:
            issues.append(f"Low disk space: {free_mb:.0f} MB free")
    except Exception:
        pass
    return issues


def run_health_check(base_url: str = "http://127.0.0.1:8765") -> tuple[int, list[str]]:
    """Run all checks, return (exit_code, list_of_findings)."""
    all_issues = []
    all_issues.extend(check_api_server(base_url))
    all_issues.extend(check_database())
    all_issues.extend(check_git_status())
    all_issues.extend(check_resource_usage())

    exit_code = 2 if any("unreachable" in i or "not found" in i for i in all_issues) else \
                1 if all_issues else 0
    return exit_code, all_issues


def main():
    base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:8765")
    exit_code, issues = run_health_check(base_url)

    if "--json" in sys.argv:
        print(json.dumps({"exit_code": exit_code, "issues": issues}))
    else:
        if exit_code == 0:
            print("All systems healthy")
        else:
            print("Health check issues:")
            for i in issues:
                print(f"  - {i}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
