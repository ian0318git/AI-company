# AI Embedded Systems Company

**Turn Claude Code into your personal embedded + full-stack dev team.**

任何腦中想法 → 實際運行的軟體/韌體。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 核心能力

| 能力 | 說明 |
|------|------|
| 🧠 **Idea → Software** | 從模糊想法到部署的完整 Pipeline |
| 🔌 **硬體橋接** | 自動偵測開發板、燒錄韌體、監聽序列埠 |
| 👥 **18 個 AI Agent** | 嵌入式 × 6 + 軟體 × 5 + 管理 × 5 + 特殊 × 2 |
| 📋 **5 種 Pipeline** | Firmware / Linux / Fullstack / Prototype / Research |
| 💾 **知識庫** | M5Stack、ESP32 腳位定義與程式碼模式內建 |
| 🔒 **零額外成本** | 無外部 API 呼叫，完全本地運作 |

## 🚀 快速開始

### 安裝

```bash
# 1. Clone
git clone https://github.com/ian0318git/AI-company.git
cd AI-company

# 2. Install
python install.py

# 3. Restart Claude Code
```

### 第一個專案

在 Claude Code 中直接說：

> "我想做一個 M5Stack Core S3 的溫濕度監測器，會在 LCD 上顯示數值，也能透過 WiFi 上傳到雲端"

系統會自動：
1. **Idea Refiner** 精煉需求
2. **Pipeline** 建立 `embedded-firmware` 流程
3. **Firmware Engineer** 撰寫 ESP32-S3 程式碼
4. **Hardware Engineer** 規劃腳位
5. 編譯 → 燒錄到你的 M5Stack

## 🏗️ 架構

```
┌─────────────────────────────────────────┐
│  Dashboard (React 19 + Shadcn UI)       │  可視化
├─────────────────────────────────────────┤
│  REST API (FastAPI) + CLI (Typer)       │  控制層
├─────────────────────────────────────────┤
│  Orchestrator (LangGraph)               │  編排層
├─────────────────────────────────────────┤
│  Memory & Knowledge (SQLite)            │  記憶層
├─────────────────────────────────────────┤
│  MCP Server (FastMCP) — 107 tools      │  工具層
└─────────────────────────────────────────┘
```

## 📦 支援硬體

| 開發板 | 晶片 | 狀態 |
|--------|------|------|
| M5Stack Core S3 | ESP32-S3 | ✅ 深度整合 |
| M5Stack Core2 | ESP32 | 🔄 計畫中 |
| ESP32-DevKit | ESP32 | ✅ 支援 |
| Raspberry Pi Pico | RP2040 | 🔄 計畫中 |
| STM32F4 Discovery | STM32F407 | 🔄 計畫中 |
| nRF52840 DK | nRF52840 | 🔄 計畫中 |

## 🤖 Agent 團隊

**嵌入式工程 (6)**:
`firmware-engineer` · `hardware-engineer` · `linux-engineer` · `iot-engineer` · `sensor-driver-dev` · `testing-engineer`

**軟體工程 (5)**:
`software-architect` · `backend-developer` · `frontend-developer` · `fullstack-developer` · `devops-engineer`

**管理與品質 (5)**:
`tech-lead` · `project-manager` · `code-reviewer` · `qa-engineer` · `technical-writer`

**特殊 (2)**:
`idea-refiner` · `rapid-prototyper`

## 📋 Pipeline 模板

| 模板 | 流程 |
|------|------|
| `embedded-firmware` | Idea → 腳位規劃 → HAL → 業務邏輯 → 測試 → 燒錄 |
| `embedded-linux` | Idea → 系統設計 → Driver/App → 交叉編譯 → 測試 |
| `web-fullstack` | Idea → UI/UX → Frontend → Backend → 部署 |
| `quick-prototype` | Idea → MVP → 迭代 |
| `research-spike` | 技術調研 → 可行性報告 |

## 🛠️ 開發

```bash
# Editable install
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/ai_embedded_company/

# Start API server
aiteam serve --reload

# Start MCP server
aiteam mcp
```

## 📄 License

MIT — 做任何你想做的事，打造你自己的 AI 公司。
