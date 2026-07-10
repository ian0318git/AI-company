# Cycle #251 — Dependency Version Audit & Upgrade Plan

Generated: 2026-07-10

## Summary

Comprehensive audit of 17 Python dependencies (pyproject.toml) and 16 Node.js
dependencies (dashboard/package.json). Result: **most dependencies are
up-to-date** within their pinned ranges. One critical upgrade identified: Vite
6 → Vite 8 (major breaking change with Rolldown).

---

## Python Dependencies

### Core (12 packages)

| Package | Pinned | Installed | Latest | Status | Notes |
|---|---|---|---|---|---|
| fastapi | >=0.115 | 0.138.2 | 0.138.2 | ✅ | Up-to-date |
| uvicorn | >=0.32 | 0.49.0 | 0.49.0 | ✅ | Up-to-date |
| fastmcp | >=3.0 | 3.4.2 | 3.4.2 | ✅ | Starlette CVE fixed in 3.4.1 |
| typer | >=0.15 | 0.26.8 | 0.26.8 | ✅ | Up-to-date (0.26.x is current line) |
| rich | >=13.0 | 15.0.0 | 15.0.0 | ✅ | Up-to-date |
| pyyaml | >=6.0 | 6.0.3 | 6.0.3 | ✅ | Up-to-date |
| pydantic | >=2.0 | 2.13.4 | 2.13.4 | ✅ | Latest stable (v2.14.0a1 pre-release) |
| pydantic-settings | >=2.0 | 2.14.2 | 2.14.2 | ✅ | Up-to-date |
| aiosqlite | >=0.20 | 0.22.1 | 0.22.1 | ✅ | Up-to-date |
| sqlalchemy | >=2.0 | 2.0.51 | 2.0.51 | ✅ | Latest stable (2.1.0b3 pre-release) |
| alembic | >=1.14 | 1.18.5 | 1.18.4 | ⚠️ | Slightly ahead of latest reported |
| anyio | >=4.0 | 4.14.1 | 4.14.1 | ✅ | Up-to-date |

### Dev Dependencies (5 packages)

| Package | Pinned | Installed | Latest | Status | Notes |
|---|---|---|---|---|---|
| pytest | >=8.0 | 9.1.1 | 9.1.1 | ✅ | Up-to-date |
| pytest-asyncio | >=0.24 | 1.4.0 | 1.4.0 | ✅ | Up-to-date |
| pytest-cov | >=6.0 | 7.1.0 | 7.1.0 | ✅ | Up-to-date |
| ruff | >=0.8 | 0.15.20 | 0.15.20 | ✅ | Up-to-date |
| mypy | >=1.13 | 2.1.0 | 2.1.0 | ✅ | Well within spec |

### Optional Dependencies

| Package | Pinned | Installed | Status | Notes |
|---|---|---|---|---|
| websockets | >=12.0 | 16.0 | ✅ | Up-to-date |
| redis | >=5.0 | not installed | 📦 | Optional — not needed for core |
| asyncpg | >=0.30 | not installed | 📦 | Optional — not needed for SQLite |
| psycopg2-binary | >=2.9 | not installed | 📦 | Optional — not needed for SQLite |

---

## Node.js Dependencies (16 packages)

| Package | Pinned | Installed | Latest | Status | Notes |
|---|---|---|---|---|---|
| react | ^19.0.0 | 19.2.7 | 19.2.7 | ✅ | Up-to-date |
| react-dom | ^19.0.0 | 19.2.7 | 19.2.7 | ✅ | Up-to-date |
| @radix-ui/react-slot | ^1.1.0 | 1.3.0 | 1.3.0 | ✅ | Up-to-date |
| @types/react | ^19.0.0 | 19.2.17 | 19.2.17 | ✅ | Up-to-date |
| @vitejs/plugin-react | ^4.3.0 | 4.7.0 | 4.7.0 | ✅ | Compatible with Vite 6 |
| autoprefixer | ^10.4.0 | 10.5.2 | 10.5.2 | ✅ | Up-to-date |
| class-variance-authority | ^0.7.0 | 0.7.1 | 0.7.1 | ✅ | Up-to-date |
| clsx | ^2.1.0 | 2.1.1 | 2.1.1 | ✅ | Up-to-date |
| lucide-react | ^0.460.0 | 0.460.0 | 0.460.0 | ✅ | Up-to-date |
| postcss | ^8.4.0 | 8.5.16 | 8.5.16 | ✅ | Up-to-date |
| react-router-dom | ^7.0.0 | 7.18.1 | 7.18.1 | ✅ | Up-to-date |
| recharts | ^2.15.0 | 2.15.4 | 2.15.4 | ✅ | Up-to-date |
| tailwind-merge | ^2.5.0 | 2.6.1 | 2.6.1 | ✅ | Up-to-date |
| tailwindcss | ^3.4.0 | 3.4.19 | 3.4.19 | ✅ | Up-to-date |
| typescript | ^5.7.0 | 5.9.3 | 5.9.3 | ✅ | Up-to-date |
| vite | ^6.0.0 | 6.4.3 | **8.0.16** | 🚨 | **Critical upgrade needed** |

---

## Critical Finding: Vite 6 → Vite 8

**Severity: HIGH** — Vite 8 is 2 major versions ahead of our pinned `^6.0.0`.

### Benefits of upgrading
- **Rolldown bundler**: Rust-based, unified for dev & production, 10–30x faster builds
- **@vitejs/plugin-react v6**: Uses Oxc for React Refresh, drops Babel dependency
- **Built-in devtools**: new `devtools` config option
- **TS path alias resolution**: new `resolve.tsconfigPaths` setting

### Breaking changes
- Requires Node.js 20.19+ or 22.12+ (likely satisfied)
- Required Vite 7 migration steps first (incremental)
- @vitejs/plugin-react needs upgrade from v4 to v6
- Config may need migration for new `defineConfig` shape

### Recommendation
Create a separate task for Vite 6 → 7 → 8 migration. Not urgent for current
functionality but worthwhile for build performance.

---

## Security Advisory Report

| Package | CVE Count | Severity | Status |
|---|---|---|---|
| fastapi | 0 | — | ✅ Safe |
| uvicorn | 0 | — | ✅ Safe |
| fastmcp | 0 (Starlette CVE fixed in >=3.4.1) | Fixed | ✅ Safe |
| sqlalchemy | 0 | — | ✅ Safe |
| pydantic | 0 | — | ✅ Safe |
| All Node.js deps | 0 | — | ✅ Safe |

**No active CVEs found** for any currently installed dependency. All known
advisories have been addressed in the installed versions.

---

## Prioritised Upgrade Plan

1. **(HIGH) Vite 6 → 7 → 8 migration** — major build tool upgrade with breaking
   changes. Requires incremental upgrade path. Effort: medium.
2. **(LOW) alembic 1.18.5** — already at latest or slightly ahead. No action
   needed.
3. **(LOW) Pydantic v2.14.0a1** — alpha pre-release, wait for stable.
4. **(LOW) SQLAlchemy 2.1.0** — beta pre-release, wait for stable.
5. **(INFO) redis/asyncpg/psycopg2** — optional deps not installed. No action.
