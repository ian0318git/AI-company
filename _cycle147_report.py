import json, datetime, os

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
ts = now.strftime("%Y-%m-%d %H:%M:%S")

report = f"""# Cycle #147 — Idle Status Report

**Generated**: {ts} (UTC+8)
**Status**: Fully idle — all pipelines drained, no pending tasks, no new ideas.

## Scan Results

### Ideas (/api/ideas/)
- **Total**: 22
- **New**: 0
- **Refined**: 0
- **Archived**: 2
- **Done**: 20

No new or unrefined ideas to process.

### Pipelines (/api/pipelines/)
- **Total**: 28
- **All at phase**: `done`

No active pipelines to advance.

### Tasks (/api/tasks/)
- **All tasks**: `done` status across every project.

No high-priority todo tasks to execute.

## Cycle Actions Taken

1. **Ideas scan** — Checked all 22 ideas; none are new or awaiting refinement.
2. **Pipeline check** — All 28 pipelines are completed. Nothing to advance.
3. **Task audit** — All tasks across all projects are done. No work items to execute.

## Conclusion

System is fully idle. No refiner work, no pipeline starts, no task execution needed. Ready for new input.
"""

reports_dir = "/home/ian/github-project/AI-company/data/deliverables"
os.makedirs(reports_dir, exist_ok=True)
report_path = os.path.join(reports_dir, "cycle-147-idle-report.md")
with open(report_path, "w") as f:
    f.write(report)

print(f"Report written to {report_path}")
