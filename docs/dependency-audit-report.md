# Dependency Version Audit Report

**Generated:** 2026-07-10 (Cycle #233)
**Project:** AI Embedded Systems Company
**Scope:** Python (uv/pip) + Node.js (npm) dependencies

---

## Executive Summary

- **Total packages audited:** 86 Python + 17 Node.js = 103 packages
- **Outdated Python packages:** 15 (17.4%)
- **Outdated Node.js packages:** 7 (41.2%)
- **Security advisories:** No critical CVEs found at current versions
- **Priority upgrades (no breaking changes):** 12 Python packages
- **Major version jumps (breaking):** 0 Python + 7 Node.js — major upgrades need dedicated sprint

---

## Part 1: Python Dependencies (uv)

### Safe to Upgrade (patch/minor, no breaking changes)

| Package | Current | Latest | Bump Type | Complexity |
|---|---|---|---|---|
| coverage | 7.14.3 | 7.15.0 | minor | trivial |
| cyclopts | 4.20.0 | 4.21.0 | minor | trivial |
| fastapi | 0.138.2 | 0.139.0 | minor | low |
| fastmcp | 3.4.2 | 3.4.4 | patch | trivial |
| fastmcp-slim | 3.4.2 | 3.4.4 | patch | trivial |
| joserfc | 1.7.2 | 1.7.3 | patch | trivial |
| librt | 0.12.0 | 0.13.0 | minor | low |
| mypy | 2.1.0 | 2.2.0 | minor | low |
| pydantic-core | 2.46.4 | 2.47.0 | minor | low |
| rich-rst | 2.0.2 | 2.1.0 | minor | trivial |
| ruff | 0.15.20 | 0.15.21 | patch | trivial |
| typing-extensions | 4.15.0 | 4.16.0 | minor | trivial |
| uvicorn | 0.49.0 | 0.51.0 | minor | low |

### Review Before Upgrade (major version)

| Package | Current | Latest | Notes |
|---|---|---|---|
| caio | 0.9.25 | 0.10.2 | Major bump — check async I/O compatibility |
| cffi | 2.0.0 | 2.1.0 | Major bump — check C extension compatibility |

### Fully Up-to-Date (73 packages)

aiofile, aiosqlite, alembic, annotated-types, anyio, attrs, authlib, beartype, cachetools, certifi, click, cryptography, dnspython, email-validator, griffelib, h11, httpcore, httptools, httpx, idna, pydantic, pytest, pytest-asyncio, pytest-cov, python-dotenv, python-multipart, rich, sqlalchemy, starlette, typer, websockets, etc. all at latest.

---

## Part 2: Node.js Dependencies (npm — Dashboard)

### ALL Major Version Jumps

| Package | Current | Latest | Bump | Risk |
|---|---|---|---|---|
| @vitejs/plugin-react | 4.7.0 | 6.0.3 | major (5→6) | HIGH — bundler plugin API changes |
| lucide-react | 0.460.0 | 1.24.0 | major (0→1) | HIGH — icon API may have breaking changes |
| recharts | 2.15.4 | 3.9.2 | major (2→3) | HIGH — component props likely changed |
| tailwind-merge | 2.6.1 | 3.6.0 | major (2→3) | MEDIUM — utility API changes |
| tailwindcss | 3.4.19 | 4.3.2 | major (3→4) | HIGH — CSS config overhaul, JIT engine changed |
| typescript | 5.9.3 | 7.0.2 | major (5→6→7) | HIGH — breaking language features |
| vite | 6.4.3 | 8.1.4 | major (6→7→8) | HIGH — build system API changes |

### Fully Up-to-Date (10 packages)

React 19, react-dom 19, react-router-dom 7, @radix-ui/react-slot, class-variance-authority, clsx, autoprefixer, postcss.

---

## Part 3: Security Advisory Scan

### Critical Risk — None
- **cryptography** 49.0.0 — latest; no known CVEs at this version
- **certifi** 2026.6.17 — latest; certificate bundle updated Jun 2026

### High Risk — None
- **fastapi** 0.138.2 — latest stable (0.139.0 available, minor)
- **httpx** 0.28.1 — latest; no recent advisories

### Recommendations
- Add `pip-audit` or `uv audit` to CI pipeline for automated CVE scanning
- Add `npm audit` on every build; currently no security advisories flagged
- Schedule monthly dependency review

---

## Part 4: Prioritized Upgrade Plan

### Phase 1 — Immediate (patch/minor, no risk)
1. `ruff` 0.15.20 → 0.15.21
2. `fastmcp` 3.4.2 → 3.4.4
3. `fastmcp-slim` 3.4.2 → 3.4.4
4. `joserfc` 1.7.2 → 1.7.3
5. `coverage` 7.14.3 → 7.15.0
6. `typing-extensions` 4.15.0 → 4.16.0
7. `rich-rst` 2.0.2 → 2.1.0

### Phase 2 — Short-term (minor bumps, low risk)
1. `cyclopts` 4.20.0 → 4.21.0
2. `fastapi` 0.138.2 → 0.139.0
3. `librt` 0.12.0 → 0.13.0
4. `mypy` 2.1.0 → 2.2.0
5. `pydantic-core` 2.46.4 → 2.47.0
6. `uvicorn` 0.49.0 → 0.51.0

### Phase 3 — Review First
1. `caio` 0.9.25 → 0.10.2 (check async compatibility)
2. `cffi` 2.0.0 → 2.1.0 (check CFFI API changes)

### Phase 4 — Node.js Major Upgrades (dedicated sprint)
1. `vite` 6.4.3 → 8.1.4
2. `@vitejs/plugin-react` 4.7.0 → 6.0.3
3. `typescript` 5.9.3 → 7.0.2
4. `tailwindcss` 3.4.19 → 4.3.2
5. `recharts` 2.15.4 → 3.9.2
6. `tailwind-merge` 2.6.1 → 3.6.0
7. `lucide-react` 0.460.0 → 1.24.0

---

## Part 5: CI Integration Recommendations

1. Add `uv lock --check` to CI to detect drift in Python dependency resolution
2. Schedule weekly `uv pip list --outdated` and post to Slack
3. Add `npm audit` to frontend CI pipeline
4. Use Dependabot or Renovate for automated PR generation on patch/minor bumps
5. Create monthly dependency review ticket from auto-generated report
