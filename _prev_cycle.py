import json, sys
ideas = json.load(sys.stdin)
auto_ideas = [i for i in ideas if "health check" in i.get("title","").lower() or "idle cycle" in i.get("title","").lower()]
auto_ideas.sort(key=lambda x: x.get("created_at",""))
print("Latest autonomous cycle ideas:")
for i in auto_ideas[-3:]:
    print(f"  id={i['id'][:16]} title={i['title']} status={i['status']} created={i.get('created_at','?')[:19]}")
    print(f"  raw_desc={i.get('raw_description','')[:300]}")
    print()
