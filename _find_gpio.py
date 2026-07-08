import json, sys
tasks = json.load(sys.stdin)
for t in tasks:
    if "GPIO" in t.get("title", ""):
        print("ID:", t["id"])
        print("Title:", t["title"])
        print("Status:", t["status"])
        print("Project:", t.get("project_id", "?"))
