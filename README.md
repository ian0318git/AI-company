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

Manage projects, tasks, and pipelines through a visual web interface powered by React 19.

```bash
# Option 1: Via CLI (recommended)
uv run aiteam dashboard

# Option 2: Manually via npm
cd dashboard && npm run dev -- --host 0.0.0.0
```

Then open **http://localhost:5173** in your browser. The dashboard proxies API calls to the backend at `localhost:8765`.

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
