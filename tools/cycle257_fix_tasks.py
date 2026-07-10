"""Fix the active project's tasks for Cycle 257.

The auto-seed mechanism created wrong tasks (AI research instead of repo cleanup).
This script cancels those tasks and adds correct cleanup tasks.
"""
import urllib.request
import json

PROJECT_ID = "8889d34e-7ec4-4770-ace9-a0a09eeeb7d9"
BASE = "http://127.0.0.1:8765/api"


def main():
    # Get all tasks for this project
    req = urllib.request.Request(f"{BASE}/tasks/?project_id={PROJECT_ID}&limit=50")
    with urllib.request.urlopen(req) as r:
        data = json.load(r)

    tasks = data.get("items", [])
    print(f"Found {len(tasks)} tasks in project")

    # Mark each todo task as "cancelled"
    cancelled = 0
    for t in tasks:
        task_id = t["id"]
        if t.get("status") == "todo":
            print(f"Cancelling: {t['title'][:60]} (id={task_id[:8]}...)")
            body = json.dumps({"status": "cancelled"}).encode()
            req2 = urllib.request.Request(
                f"{BASE}/tasks/{task_id}/status",
                data=body,
                method="PATCH",
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req2) as r2:
                    result = json.load(r2)
                    print(f"  -> {result.get('status', 'ok')}")
                    cancelled += 1
            except Exception as e:
                print(f"  -> Failed: {e}")

    # Now add the REAL cleanup tasks
    cleanup_tasks = [
        "Audit root-level files categorize as transient vs persistent",
        "Move stale diagnostic scripts to tools/ directory",
        "Consolidate cycle reports with summary index",
        "Clean up comparison_result.json and other stale root artifacts",
        "Finalize .gitignore patterns and commit cleanup",
    ]

    created = 0
    for title in cleanup_tasks:
        print(f"Creating task: {title}")
        body = json.dumps(
            {
                "title": title,
                "description": "Part of Repo Root Cleanup & Report Consolidation project",
                "project_id": PROJECT_ID,
                "priority": "high",
                "status": "todo",
            }
        ).encode()
        req3 = urllib.request.Request(
            f"{BASE}/tasks/",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req3) as r3:
                result = json.load(r3)
                print(f"  -> Created (id={result.get('id', '?')[:8]}...)")
                created += 1
        except Exception as e:
            print(f"  -> Failed: {e}")

    print(f"\nDone! Cancelled {cancelled} wrong tasks, created {created} correct tasks.")


if __name__ == "__main__":
    main()
