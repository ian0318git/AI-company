import json, sys
ideas = json.load(sys.stdin)
not_done = [i for i in ideas if i.get("status") != "done"]
print(f"Ideas not done: {len(not_done)}")
for i in not_done:
    print(json.dumps(i, indent=2)[:500])
    print("---")
if not not_done:
    print("All ideas are done.")
    in_progress = [i for i in ideas if i.get("status") == "in_progress"]
    print(f"In progress: {len(in_progress)}")
    for i in in_progress:
        print(f"  {i.get('title')} ({i.get('id')[:8]})")
    # Check created_at for the newest
    with_dates = [(i.get("created_at", ""), i.get("title", "")) for i in ideas]
    with_dates.sort(reverse=True)
    print(f"\nNewest 3 ideas:")
    for d,t in with_dates[:3]:
        print(f"  {d[:19]} - {t[:60]}")
