# AI Company

**Turn Claude Code into your personal embedded + full-stack dev team.**

Any idea → working software/firmware.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Lang](https://img.shields.io/badge/lang-English-blue)](README.md)
[![Lang](https://img.shields.io/badge/語言-繁體中文-green)](README.zh-TW.md)

> 📖 **Read this in:** [繁體中文](README.zh-TW.md)

## 🎯 Core Capabilities

| Capability | Description |
|------------|-------------|
| 🧠 **Idea → Software** | Complete pipeline from vague idea to deployment |
| 🔌 **Hardware Bridge** | Auto-detect dev boards, flash firmware, monitor serial |
| 👥 **18 AI Agents** | Embedded × 6 + Software × 5 + Management × 5 + Special × 2 |
| 📋 **5 Pipelines** | Firmware / Linux / Fullstack / Prototype / Research |
| 💾 **Knowledge Base** | M5Stack, ESP32 pin definitions and code patterns built-in |
| 🔒 **Zero External Cost** | No external API calls, fully local operation |

## 🚀 Quick Start

### Installation

```bash
# 1. Install uv (if you haven't already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone
git clone https://github.com/ian0318git/AI-company.git
cd AI-company

# 3. Sync dependencies
uv sync

# 4. Install into Claude Code
uv run python install.py

# 5. Restart Claude Code
```

### Your First Project

Just say this inside Claude Code:

> "I want to build a temperature and humidity monitor for M5Stack Core S3 that displays readings on the LCD and uploads data to the cloud via WiFi"

The system will automatically:
1. **Idea Refiner** — Refine the requirements
2. **Pipeline** — Create an `embedded-firmware` workflow
3. **Firmware Engineer** — Write ESP32-S3 code
4. **Hardware Engineer** — Plan pin assignments
5. Compile → Flash to your M5Stack

## 🖥️ Dashboard

A visual command center for your AI engineering team — track every idea from conception to delivery.

```bash
# Option 1: Via CLI (recommended)
uv run aiteam dashboard

# Option 2: Manually via npm
cd dashboard && npm run dev -- --host 0.0.0.0
```

Open **http://localhost:5173** — the dashboard proxies API calls to the backend at `localhost:8765`.

### What makes it powerful

| Feature | What you get |
|---------|-------------|
| 🧠 **Idea Inbox** | Submit ideas in plain language. One click to refine, one click to spin up a full engineering pipeline. |
| 📊 **Progress Dashboard** | Live percentage counter — pipeline phases × task completion. Watch ideas go from 0% → 100%. |
| 🔀 **Agent Workflow Visualization** | See exactly which agents work on what, who hands off to whom, and which steps run in parallel — rendered as a color-coded DAG. |
| ✅ **Interactive Task Board** | Click any task to cycle its status (todo → in progress → done). Each task shows its assigned agent. |
| 🏗️ **Pipeline Tracking** | 6-phase progress bar per pipeline. Advance phases with one click. Auto-completion detection. |
| 👥 **Team Roster** | See the assembled agent team for each project — who's idle, who's working. |
| 📦 **Deliverables** | Actual output files attached to each idea. Firmware source code, research reports, pinout diagrams — rendered as styled HTML for comfortable reading. |
| 🌐 **Bilingual UI** | English / 繁體中文 toggle. 100+ UI strings localized. Preferences saved across sessions. |

### Example workflow

```
Submit Idea           Refine              Start Pipeline       Track Progress
    │                    │                      │                    │
    ▼                    ▼                      ▼                    ▼
"I want a smart    AI suggests         6-phase pipeline     Click tasks ✓
garden monitor"    embedded-firmware    with 8 tasks +      Watch agents work
                   pipeline             5-agent team        Deliverables land
                                                            100% 🎉
```

## 🧬 Self-Evolution

The system doesn't just execute — it **evolves**. Every failure, every research discovery, every agent interaction feeds back into the system, making it smarter over time.

### Failure Alchemy

When a task fails, the system doesn't just log it. It performs **alchemy** — turning failure into three kinds of gold:

| Output | What it is | How it works |
|--------|-----------|--------------|
| 🛡️ **Antibody** | Prevention strategy | Stored in team memory. Prevents the same class of error from recurring. |
| 💉 **Vaccine** | Pre-task warning | Injected before similar future tasks. "Before starting I2C driver work, verify timeout is set..." |
| ⚡ **Catalyst** | Prompt improvement | Injected into agent system prompts. Changes *how* agents think about the problem class. |

**Example**: An I2C bus hang under high temperature → antibody (add 50ms timeout + bus reset), vaccine (pre-flight checklist for all I2C drivers), catalyst (agent now audits every blocking call for timeout coverage).

### Research Loop

Research agents continuously scan for new technology, competitor moves, and emerging patterns:

```
Research Agent scans  →  Finding submitted  →  Agents debate relevance
                                                    │
                          Accepted findings ─────────┘
                                │
                          Auto-created as Ideas in Inbox
                                │
                          Refine → Pipeline → Tasks → Deliverables
```

The loop feeds the pipeline. Accepted research becomes real work — without a human typing a single prompt.

### Evolution Dashboard

Open **http://localhost:5173/evolution** to see:
- **Health cards**: Active antibodies, vaccines, research conversion rate, system health
- **Failure alchemy panel**: Every failure with its antibody, vaccine, and catalyst
- **Research loop panel**: All findings with debate notes, acceptance flow, linked ideas

> 💡 *"You leave at night. The system runs. You come back to antibodies that were born while you slept."*

## 🤖 Autonomous Mode

Stop clicking "yes" — the system can run on its own.

### Quick Start

```bash
# Start autonomous mode (runs every 5 minutes)
./scripts/autonomous.sh

# Custom interval
./scripts/autonomous.sh 10m    # Every 10 minutes
./scripts/autonomous.sh 30m    # Every 30 minutes

# One cycle only (test run)
./scripts/autonomous.sh once

# Stop the autonomous loop
./scripts/autonomous.sh stop
```

### What happens when you walk away

1. **API server auto-starts** if not running
2. **Dashboard auto-starts** if not running
3. **Claude Code enters `/loop` mode** with the autonomous prompt
4. Every cycle, the system:
   - Scans the Idea Inbox for new ideas → refines them → creates pipelines
   - Checks the Task Wall → executes the next high-priority task
   - Advances pipelines when phases are complete
   - Reports failures → antibodies/vaccines/catalysts auto-generated
   - Every 5 cycles: runs research scan → submits findings
5. **No permission prompts** — `.claude/settings.json` pre-authorizes common operations

### The experience

```
9:00 PM — You type: ./scripts/autonomous.sh 10m
9:00 PM — You close your laptop and go to sleep

While you sleep:
  9:05 — CEO picks up 2 high-priority tasks
  9:15 — Research agent finds Zephyr 4.0 release notes
  9:25 — Failure alchemy analyzes an I2C timeout bug
  9:35 — 3 tasks marked done, pipeline advances to testing
  ...

7:00 AM — You open the Evolution dashboard
         — 4 antibodies born, 2 research findings accepted
         — All pipelines advanced, tasks completed
         — Zero prompts from you
```

### How it works

| Component | Role |
|-----------|------|
| `scripts/autonomous.sh` | Launcher — starts API, dashboard, and Claude Code `/loop` |
| `scripts/autonomous-prompt.md` | The autonomous execution instructions |
| `.claude/settings.json` | Permission allowlist — no more yes/no prompts |
| `/loop` mode | Claude Code's built-in recurring execution engine |

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Dashboard (React 19 + Shadcn UI)       │  Visualization
├─────────────────────────────────────────┤
│  REST API (FastAPI) + CLI (Typer)       │  Control Layer
├─────────────────────────────────────────┤
│  Orchestrator (LangGraph)               │  Orchestration
├─────────────────────────────────────────┤
│  Memory & Knowledge (SQLite)            │  Memory Layer
├─────────────────────────────────────────┤
│  MCP Server (FastMCP) — 107 tools      │  Tool Layer
└─────────────────────────────────────────┘
```

## 📦 Supported Hardware

| Dev Board | Chip | Status |
|-----------|------|--------|
| M5Stack Core S3 | ESP32-S3 | ✅ Deep Integration |
| M5Stack Core2 | ESP32 | 🔄 Planned |
| ESP32-DevKit | ESP32 | ✅ Supported |
| Raspberry Pi Pico | RP2040 | 🔄 Planned |
| STM32F4 Discovery | STM32F407 | 🔄 Planned |
| nRF52840 DK | nRF52840 | 🔄 Planned |

## 🤖 Agent Team

**Embedded Engineering (6)**:
`firmware-engineer` · `hardware-engineer` · `linux-engineer` · `iot-engineer` · `sensor-driver-dev` · `testing-engineer`

**Software Engineering (5)**:
`software-architect` · `backend-developer` · `frontend-developer` · `fullstack-developer` · `devops-engineer`

**Management & Quality (5)**:
`tech-lead` · `project-manager` · `code-reviewer` · `qa-engineer` · `technical-writer`

**Special (2)**:
`idea-refiner` · `rapid-prototyper`

## 📋 Pipeline Templates

| Template | Workflow |
|----------|----------|
| `embedded-firmware` | Idea → Pin Planning → HAL → Business Logic → Test → Flash |
| `embedded-linux` | Idea → System Design → Driver/App → Cross-compile → Test |
| `web-fullstack` | Idea → UI/UX → Frontend → Backend → Deploy |
| `quick-prototype` | Idea → MVP → Iterate |
| `research-spike` | Technology Research → Feasibility Report |

## 🛠️ Development

```bash
# Sync dependencies (including dev tools)
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/ai_embedded_company/

# Start API server
uv run aiteam serve --reload

# Start Dashboard
uv run aiteam dashboard

# Start MCP server
uv run aiteam mcp
```

## 📄 License

MIT — Do whatever you want. Build your own AI company.
