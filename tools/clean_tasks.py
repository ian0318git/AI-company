"""Clean up stale todo tasks — mark tasks from completed projects as done."""
import json
import urllib.request

BASE = "http://127.0.0.1:8765"


def api_get(path: str) -> dict | list:
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())


def api_patch(path: str) -> dict | list:
    req = urllib.request.Request(f"{BASE}{path}", method="PATCH")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main():
    # Get all projects and their statuses
    projects = api_get("/api/projects/")
    if isinstance(projects, dict):
        projects = projects.get("items", [])
    project_status = {p["id"]: p.get("status", "unknown") for p in projects}
    print(f"Loaded {len(project_status)} projects")

    # Get all todo tasks
    resp = api_get("/api/tasks/?status=todo&limit=200")
    tasks = resp.get("items", []) if isinstance(resp, dict) else resp
    print(f"Found {len(tasks)} todo tasks")

    # Categorize
    from_completed = []
    from_active = []
    for t in tasks:
        pid = t.get("project_id")
        ps = project_status.get(pid, "no-project")
        if ps == "completed" or ps == "done":
            from_completed.append(t)
        else:
            from_active.append(t)

    print(f"\nTasks from completed projects: {len(from_completed)}")
    for t in from_completed:
        pid = t.get("project_id", "")[:12]
        print(f"  done: {t['id'][:12]} | proj={pid} | {t['title'][:40]}")

    # Mark them all as done
    for t in from_completed:
        tid = t["id"]
        result = api_patch(f"/api/tasks/{tid}/status?status=done")
        assert result["status"] == "done", f"Failed to mark {tid} as done"
    print(f"\n✅ Marked {len(from_completed)} stale tasks as done")

    # Report remaining
    print(f"\nRemaining active todo tasks: {len(from_active)}")
    for t in from_active:
        pid = t.get("project_id", "")[:12]
        print(f"  todo: {t['id'][:12]} | proj={pid} | {t['title'][:40]}")


if __name__ == "__main__":
    main()
