# AI Company

**Turn Claude Code into your personal embedded + full-stack dev team.**

Any idea → working software/firmware.

## 👑 Team Structure

```
Chairman (You)  →  CEO (Claude AI)  →  18 Specialized Agents
    🧑‍💼                  🤖                   👥
 Set direction     Autonomous execution    Write firmware,
 Approve strategy  Task scheduling         design hardware,
 Final decisions   Pipeline management     review code, test,
                   Research scanning       deploy, document
```

| Role | Who | Responsibility |
|------|-----|---------------|
| 🧑‍💼 **Chairman** | **You** | Set the vision. Approve the big decisions. The system works for you. |
| 🤖 **CEO** | **Claude AI** | Runs the company 24/7. Picks up tasks, manages pipelines, scans for new tech. Zero prompts needed. |
| 👥 **18 Agents** | Specialized AI roles | Firmware, hardware, Linux, IoT, frontend, backend, DevOps, security, QA, research... |

> 💡 *You're not the operator. You're the owner. The AI is your CEO.*

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
| ⏱ **Time Tracking** | Automatic per-task elapsed time, pause/resume on status changes, per-agent breakdown |
| 🪙 **Token Tracking** | Per-agent token consumption tracking, cumulative totals across projects |
| 🧬 **Self-Evolution** | Auto-detect slow tasks, create failure records, trigger improvement cycles |

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

**After the pipeline is created**, don't wait for tasks to run by themselves. Open the Dashboard → **Idea Inbox** → click **"Start Auto Schedule"** (top bar) → watch tasks execute in real time.

> 💡 **Common mistake**: Users submit an idea, start a pipeline, and wonder why nothing happens. Tasks start in `todo` state — you must kick off the scheduler or click individual tasks to begin execution.

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
| ⏱ **Time Tracking** | Every task tracks elapsed work time automatically. Pause/resume on blocked/review transitions. See cumulative time per agent across all projects. |
| 🪙 **Token Usage** | Per-agent token consumption with progress bars. Track LLM costs at a glance — task-level, agent-level, and project-level totals. |
| 🚨 **Slow Task Detection** | Tasks exceeding time thresholds (configurable, default 2h) auto-trigger the evolution system. Background monitor catches stuck in-progress tasks. |
| 📊 **Project Time Analytics** | Each project shows total time, agent breakdown with mini-bars, and token usage per agent. Active projects panel on the Dashboard home. |
| ▶️ **Auto Schedule** | One-click global scheduler in Idea Inbox. Green dot = running, red dot = stopped. Start/Stop directly from the UI — no terminal needed. |
| 👤 **Agent Performance Table** | Combined time + token view for all agents. Sortable columns with distribution bars. See who's working hardest at a glance. |
| 📈 **Daily Token Chart** | 7-day token usage bar chart on the Dashboard home. Track daily LLM costs and spot usage trends. |
| 🙈 **Archive Ideas** | Hide unwanted ideas from the inbox without deleting data. Toggle "Show archived" to restore. Soft-delete keeps your database intact. |
| 📋 **Per-Project Agent Breakdown** | Each project card shows agent-level time and token breakdown. Recently completed projects also visible on the Dashboard home. |

### ⚠️ Important: Execution Flow

The Dashboard is a **command center**, not an auto-executor. After you start a pipeline, tasks are created in `todo` state — **they won't run by themselves.**

```
Your Idea → Refine → Start Pipeline → Tasks created (all todo)
                                           │
                              ┌────────────┴────────────┐
                              ▼                         ▼
                    ▶ Start Auto Schedule         Manual: click each
                    (Idea Inbox top bar)          task ▶ Run / ⏹ Done
                              │
                              ▼
                    Autonomous mode runs:
                     • Picks next todo task
                     • Sets it to in_progress
                     • Does the work
                     • Sets it to done
                     • Repeats for all projects
```

**To start execution**, click **"Start Auto Schedule"** at the top of the Idea Inbox. It starts directly from the UI — no terminal needed.

The status bar turns **green** when running, **red** when stopped. Click **Stop** to pause. No more wondering why tasks aren't progressing.

### Case Studies

#### Case 1: M5Stack Smart Garden (Embedded Firmware)

```
"I want a smart garden     →  AI suggests embedded-firmware pipeline
 that auto-waters plants"     6 phases, 8 tasks, 5-agent team

Deliverables:
  📄 firmware.cpp (13 KB)  — Complete ESP32-S3 Arduino firmware
  📄 platformio.ini         — Build configuration  
  📄 pinout.md              — GPIO assignments + calibration table
```

#### Case 2: Enterprise AI Transformation Strategy (Business Debate)

```
"Should we replace 30% of    →  AI suggests quick-prototype pipeline
 staff with AI agents?"          4-phase debate structure

The debate:
  🔴 Automation_Advocate argues for full AI replacement, 30% workforce reduction
  🔵 Collaboration_Advocate argues for human-AI collaboration, zero layoffs  
  ⚖️ CEO rules: "Human-AI Collaboration First" — upskill everyone, automate
     only proven-safe workflows, start with 3 internal pilot projects

Deliverables:
  📄 debate.md (8 KB) — 4-dimension structured debate + 18-month roadmap
```

## 🧬 Self-Evolution

The system doesn't just execute — it **evolves**. Every failure, every research discovery, every agent interaction feeds back into the system, making it smarter over time.

### Failure Alchemy

When a task fails **or takes too long**, the system doesn't just log it. It performs **alchemy** — turning failure into three kinds of gold:

> ⏱ **Auto-detection**: Tasks exceeding their time estimate × 2 (or global 120 min threshold) are automatically reported as timeout failures. The evolution system learns from slow tasks just as it learns from failures.

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

From the Dashboard — open **Idea Inbox** → click **"Start Auto Schedule"** (top bar).

Or from your terminal:

```bash
# Safety: --yes is required to prevent accidental runs
./scripts/autonomous.sh --yes          # Start (every 5 min)
./scripts/autonomous.sh --yes 10m      # Every 10 minutes
./scripts/autonomous.sh --yes 30m      # Every 30 minutes

# Without --yes, the script only prints instructions and exits
./scripts/autonomous.sh                 # ⚠️  Prints help, does NOT start

# Stop the autonomous loop
./scripts/autonomous.sh stop
```

The Dashboard status bar shows green when running, red when stopped — no need to check the terminal.

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

## 💾 Database Safety

The system auto-protects your data. Every server startup creates a timestamped backup.

```bash
# Manual backup
uv run python scripts/db_tool.py backup

# List all backups
uv run python scripts/db_tool.py list

# Interactive restore (with preview)
uv run python scripts/db_tool.py restore

# Check database status
uv run python scripts/db_tool.py status
```

Backups live in `data/db_backups/`. Restore previews table counts before overwriting. Never lose data to accidental `rm` again.

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
