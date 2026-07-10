"""Revive the Deprecated API Cleanup idea and create a pipeline for it."""
import urllib.request
import json

BASE = "http://127.0.0.1:8765/api"


def main():
    # Find the idea
    req = urllib.request.Request(f"{BASE}/ideas/?limit=50")
    with urllib.request.urlopen(req) as r:
        ideas = json.load(r)["items"]

    target = None
    for idea in ideas:
        if "Deprecated API Cleanup" in idea.get("title", ""):
            target = idea
            break

    if not target:
        print("Idea not found")
        return

    idea_id = target["id"]
    print(f"Reviving: {target['title']} (status={target['status']})")

    # Create project
    desc = (target.get("refined_description") or target.get("raw_description", ""))
    project_body = json.dumps({
        "name": target["title"],
        "description": desc,
        "source_idea_id": idea_id,
        "board_family": "unknown",
        "status": "active",
    }).encode()

    req2 = urllib.request.Request(
        f"{BASE}/projects/",
        data=project_body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req2) as r2:
            project = json.load(r2)
            pid = project.get("id", "?")
            print(f"Project created: {pid[:8]}...")
    except Exception as e:
        print(f"Project creation failed: {e}")
        return

    # Add tasks
    tasks = [
        "Restart FastAPI server to pick up code changes",
        "Verify PATCH status updates work end-to-end",
        "Add integration test for project status PATCH updates",
        "Verify zero datetime.utcnow deprecation warnings in test output",
    ]

    for title in tasks:
        task_body = json.dumps({
            "title": title,
            "description": f"Part of {target['title']}",
            "project_id": pid,
            "priority": "high",
            "status": "todo",
        }).encode()
        req3 = urllib.request.Request(
            f"{BASE}/tasks/",
            data=task_body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req3) as r3:
            t = json.load(r3)
            print(f"  Task: {title[:50]}... ({t.get('id','?')[:8]}...)")

    print("Done reviving Deprecated API Cleanup pipeline!")


if __name__ == "__main__":
    main()
