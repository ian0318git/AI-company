"""Clean up stale tasks from cycle 40 health-check pipeline."""
import subprocess, sys

stale_task_ids = [
    "6342002a-7f7c-418a-80ce-10f1954f2d68",
    "8f971af1-af01-4d90-a000-ecf3caa7d4f9",
    "63454b6e-ac34-46e0-91a0-99ec30529d6a",
    "c225b29b-49ed-466c-b419-b839f53d5bbc",
    "c21644f9-56e3-47a5-b6d5-812029350fef",
    "fdd3f6cd-896b-4f78-89c6-5065ef6849a9",
    "298a25a5-a919-495c-bc37-c9843a267e74",
    "6ff458f2-0451-4a03-b6c3-371441929b7f",
]

for tid in stale_task_ids:
    result = subprocess.run(
        ["curl", "-s", "-X", "PATCH", f"http://127.0.0.1:8765/api/tasks/{tid}/status?status=done"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        import json
        data = json.loads(result.stdout)
        print(f"  Done: {tid[:12]} -> status={data.get('status')}")
    else:
        print(f"  Error: {tid[:12]} -> {result.stderr}")
print("Cleanup complete.")
