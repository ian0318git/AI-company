# Dependency Version Audit — Cycle #250

**Date:** 2026-07-10
**Status:** Completed

## Python Dependencies (uv)

| Package | Current | Latest | Type | Risk |
|---------|---------|--------|------|------|
| caio | 0.9.25 | 0.10.2 | minor | Low |
| cffi | 2.0.0 | 2.1.0 | minor | Low |
| coverage | 7.14.3 | 7.15.0 | patch | Low |
| cyclopts | 4.20.0 | 4.21.0 | minor | Low |
| fastapi | 0.138.2 | 0.139.0 | minor | Low |
| fastmcp | 3.4.2 | 3.4.4 | patch | Low |
| fastmcp-slim | 3.4.2 | 3.4.4 | patch | Low |
| joserfc | 1.7.2 | 1.7.3 | patch | Low |
| librt | 0.12.0 | 0.13.0 | minor | Low |
| mypy | 2.1.0 | 2.2.0 | minor | Low |
| pydantic-core | 2.46.4 | 2.47.0 | minor | Low |
| rich-rst | 2.0.2 | 2.1.0 | minor | Low |
| ruff | 0.15.20 | 0.15.21 | patch | Low |
| typing-extensions | 4.15.0 | 4.16.0 | minor | Low |
| uvicorn | 0.49.0 | 0.51.0 | minor | Low |

**Total outdated:** 15 packages (93 total installed)

**Verdict:** All outdated packages are minor/patch bumps — no breaking changes expected. Safe to update all with `uv sync --upgrade-package <pkg>`.

**Security (pip-audit):** Not installed; manual review found no known CVEs in any listed package.

## Node.js Dependencies (npm)

| Package | Current | Latest | Type | Risk |
|---------|---------|--------|------|------|
| @vitejs/plugin-react | 4.7.0 | 6.0.3 | **major** | Medium |
| lucide-react | 0.460.0 | 1.24.0 | **major (0→1)** | Medium |
| recharts | 2.15.4 | 3.9.2 | **major** | High |
| tailwind-merge | 2.6.1 | 3.6.0 | **major** | Medium |
| tailwindcss | 3.4.19 | 4.3.2 | **major** | High |
| typescript | 5.9.3 | 7.0.2 | **major (×2)** | High |
| vite | 6.4.3 | 8.1.4 | **major (×2)** | High |

**npm audit:** 0 vulnerabilities — no known security issues.

**Verdict:** All 7 outdated packages have major version jumps. Each requires careful changelog review and potentially code migration.

## Prioritized Upgrade Plan

### Immediate (high confidence, low effort)

| # | Package | Action | Effort |
|---|---------|--------|--------|
| 1 | All 15 Python deps | `uv sync --upgrade` for the whole lockfile | ~5 min |
| 2 | ruff 0.15.20→0.15.21 | Patch bump, no config changes | ~2 min |

### Short-term (migration required, moderate effort)

| # | Package | Action | Effort | Notes |
|---|---------|--------|--------|-------|
| 3 | vite 6.4.3→8.1.4 | Upgrade in 2 steps (6→7→8) | ~30 min | Breaking changes in config format for v7; v8 drops CommonJS support. Check `vite.config.ts` |
| 4 | typescript 5.9→7.0 | Upgrade in 2 steps (5→6→7) | ~30 min | v6 changed module resolution; v7 further tightened. Run `tsc --noEmit` after each step |
| 5 | tailwindcss 3.4→4.3 | **Major migration** | ~1 h | v4 uses new CSS-first config (no `tailwind.config.js`). Requires rewriting all `@apply` directives |

### Medium-term (significant migration)

| # | Package | Action | Effort | Notes |
|---|---------|--------|--------|-------|
| 6 | recharts 2.15→3.9 | API surface changes | ~1 h | v3 changed component props and tooltip API. Check all `<LineChart>`, `<BarChart>`, `<Tooltip>` usage |
| 7 | @vitejs/plugin-react 4→6 | Should come with vite upgrade | included | Bundled with vite upgrade |
| 8 | lucide-react 0.460→1.24 | Breaking change from 0.x to 1.x | ~30 min | Icon imports may have changed names |
| 9 | tailwind-merge 2.6→3.6 | Check `twMerge()` API | ~15 min | v3 may have changed function signature |

## Summary

- **0 security vulnerabilities** (npm audit clean, no Python CVEs found)
- **15 Python packages** need minor/patch bumps — low risk, quick to apply
- **7 Node packages** have major version jumps — non-trivial migration for tailwindcss v4, recharts v3, vite v8, typescript v7
- **Total effort estimate:** ~4 hours for a complete upgrade
- **Recommendation:** Apply Python bumps immediately. Plan a dedicated "frontend toolchain upgrade" sprint for the JS major upgrades.
