# Repo Root Cleanup — Research Scope & Plan

## Audit Summary (2026-07-10)

### Transient / Temporary (Remove via `git rm`)
| File | Reason |
|------|--------|
| cycle148-report.md .. cycle236-report.md (14 files) | Old reports, consolidate into docs/cycles/ |
| tmp_check_db.py, tmp_check_ids.py, tmp_check_pipelines.py, tmp_check_projects.py, tmp_check_teams.py, tmp_check_workflow.py, tmp_complete_tasks.sh, tmp_cycle235_analyze.py, tmp_verify_code.py | Diagnostic scripts from previous cycles |
| comparison_result.json | One-off comparison output |
| performance-baseline.md | Superseded by docs/api-performance-baseline.md |

### Keep / Consolidate
| File | Action |
|------|--------|
| analyze_ideas.py, analyze_tasks.py | Move to tools/ |
| fix_projects.py | Move to tools/ |
| MEMORY.md | Already tracked; stays in root |
| CLAUDE.md, pyproject.toml, README.md, README.zh-TW.md, uv.lock, docker-compose.yml, install.py, alembic.ini | Standard project files — keep |

## Execution Phases

### Phase 1: Consolidate cycle reports
- Create `docs/cycles/` directory
- Move all `cycle*-report.md` → `docs/cycles/`
- Generate summary index `docs/cycles/README.md`

### Phase 2: Move useful scripts
- Move `analyze_ideas.py`, `analyze_tasks.py`, `fix_projects.py` → `tools/`
- Move any `tmp_*.py` with reusable logic (none identified)

### Phase 3: Remove transient files
- `git rm` of all tmp_*, cycle reports, comparison_result.json, performance-baseline.md

### Phase 4: Update .gitignore
- Add patterns: `cycle*-report.md`, `tmp_*`, `comparison_result.json`

## Migration Script (Phase 1)
```bash
mkdir -p docs/cycles
for f in cycle*-report.md; do
  git mv "$f" "docs/cycles/$f"
done
echo "# Cycle Reports Index" > docs/cycles/README.md
ls docs/cycles/cycle*-report.md | sed 's/.*\///; s/\.md$//' | \
  while read name; do echo "- [$name]($name.md)" >> docs/cycles/README.md; done
```
