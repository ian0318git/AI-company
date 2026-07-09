import json, sys

ideas = json.load(sys.stdin)

print(f"Total ideas: {len(ideas)}")

status_counts = {}
for i in ideas:
    s = i["status"]
    status_counts[s] = status_counts.get(s, 0) + 1
print(f"By status: {json.dumps(status_counts, indent=2)}")

refined_count = sum(1 for i in ideas if i.get("refined_description") is not None)
unrefined_count = sum(1 for i in ideas if i.get("refined_description") is None)
print(f"\nRefined (has refined_description): {refined_count}")
print(f"Unrefined (null refined_description): {unrefined_count}")

print("\n=== Unrefined ideas (refined_description == null) ===")
for i in ideas:
    if i.get("refined_description") is None:
        print(f"  ID: {i['id']}")
        print(f"  Title: {i['title']}")
        print(f"  Status: {i['status']}")
        print()

print("=== Refined ideas ===")
for i in ideas:
    if i.get("refined_description") is not None:
        print(f"  ID: {i['id']}")
        print(f"  Title: {i['title']}")
        print(f"  Status: {i['status']}")
        print()
