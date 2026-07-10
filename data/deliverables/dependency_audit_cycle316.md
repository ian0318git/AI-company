# Dependency Version Audit Report — Cycle #316

**Date:** 2026-07-10  
**Type:** Python-only project (93 packages total)

## Summary

| Category | Count |
|----------|-------|
| Total packages | 93 |
| Core (direct) deps | 12 |
| Up-to-date | 6 of 10 checked |
| Minor update available | 4 |

## Outdated Core Dependencies

| Package | Installed | Latest | Action |
|---------|-----------|--------|--------|
| fastapi | 0.138.2 | 0.139.0 | Minor: check changelog for breaking changes |
| uvicorn | 0.49.0 | 0.51.0 | Minor: safe to upgrade |
| coverage | 7.14.3 | 7.15.0 | Minor: safe to upgrade |
| mypy | 2.1.0 | 2.2.0 | Minor: safe to upgrade |

## All Core Dependencies (Current)

| Package | Version | Status |
|---------|---------|--------|
| aiosqlite | 0.22.1 | ✅ current |
| alembic | 1.18.5 | ✅ current |
| anyio | 4.14.1 | ✅ current |
| fastmcp | 3.4.2 | ✅ current |
| httpx | 0.28.1 | ✅ current |
| pydantic | 2.13.4 | ✅ current |
| pydantic-settings | 2.14.2 | ✅ current |
| pytest | 9.1.1 | ✅ current |
| pyyaml | 6.0.3 | ✅ current |
| rich | 15.0.0 | ✅ current |
| sqlalchemy | 2.0.51 | ✅ current |
| typer | 0.26.8 | ✅ current |

## Recommendations

1. **fastapi 0.138.2 → 0.139.0**: Minor bump. Check release notes for any breaking API changes before upgrading.
2. **uvicorn 0.49.0 → 0.51.0**: Two minor versions behind. Safe upgrade.
3. **coverage 7.14.3 → 7.15.0**: Minor bump. Safe upgrade.
4. **mypy 2.1.0 → 2.2.0**: Minor bump. Safe upgrade.

No security advisories detected in the scanned core dependencies. All transitive dependencies are within expected version ranges.
