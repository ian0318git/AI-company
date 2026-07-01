# AI Company

**將 Claude Code 轉化為你個人的嵌入式 + 全端開發團隊。**

任何腦中想法 → 實際運行的軟體/韌體。

## 👑 團隊架構

```
董事長（你）  →  CEO（Claude AI）  →  18 個專業 Agent
    🧑‍💼                  🤖                   👥
 設定方向           自主執行              寫韌體、設計硬體
 批准策略           任務排程              審查程式碼、測試
 最終決策           管線管理              部署、撰寫文件
                   研究掃描
```

| 角色 | 誰 | 職責 |
|------|-----|------|
| 🧑‍💼 **董事長** | **你** | 設定願景、批准重大決策。系統為你工作。 |
| 🤖 **CEO** | **Claude AI** | 24/7 運作整間公司。接手任務、管理管線、掃描新技術。不需任何提示。 |
| 👥 **18 個 Agent** | 專業 AI 角色 | 韌體、硬體、Linux、IoT、前端、後端、DevOps、安全、QA、研究... |

> 💡 *你不是操作員，你是老闆。AI 是你的 CEO。*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Lang](https://img.shields.io/badge/lang-English-blue)](README.md)
[![Lang](https://img.shields.io/badge/語言-繁體中文-green)](README.zh-TW.md)

> 📖 **切換語言:** [English](README.md)

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
# 1. 安裝 uv（如果還沒有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone
git clone https://github.com/ian0318git/AI-company.git
cd AI-company

# 3. 同步依賴
uv sync

# 4. 安裝到 Claude Code
uv run python install.py

# 5. 重啟 Claude Code
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

## 🖥️ 儀表板

你的 AI 工程團隊視覺化指揮中心 — 追蹤每個想法從發想到交付的完整旅程。

```bash
# 方式一：透過 CLI（推薦）
uv run aiteam dashboard

# 方式二：手動透過 npm
cd dashboard && npm run dev -- --host 0.0.0.0
```

在瀏覽器中開啟 **http://localhost:5173**，儀表板會自動將 API 請求代理到後端 `localhost:8765`。

### Dashboard 好用的地方

| 功能 | 說明 |
|------|------|
| 🧠 **想法收件匣** | 用自然語言提交想法，一鍵精煉、一鍵啟動完整工程管線。 |
| 📊 **進度儀表板** | 即時百分比計數器 — 管線階段 × 任務完成度。眼睜睜看著想法從 0% → 100%。 |
| 🔀 **Agent 工作流視覺化** | 清楚看到哪個 agent 做什麼、誰交接給誰、哪些步驟平行執行 — 彩色 DAG 流程圖。 |
| ✅ **互動任務板** | 點擊任務循環切換狀態（待辦 → 進行中 → 完成）。每個任務標示負責 agent。 |
| 🏗️ **管線追蹤** | 每個專案 6 階段進度條。一鍵推進階段，自動偵測完成。 |
| 👥 **團隊名冊** | 看到每個專案的 agent 團隊 — 誰閒置、誰工作中。 |
| 📦 **交付物** | 實際產出檔案掛在每個想法下面。韌體原始碼、研究報告、腳位圖 — 以精美深色主題 HTML 呈現。 |
| 🌐 **雙語介面** | 英文 / 繁體中文一鍵切換。100+ 個 UI 字串全翻譯，偏好自動儲存。 |

### 實際操作流程

```
提交想法              精煉                啟動管線              追蹤進度
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
「想做智慧花園      AI 建議使用        6 階段管線 +        點任務打勾 ✓
自動澆水系統」      embedded-firmware   8 個任務 +          看 agent 工作
                   管線                5 人團隊            交付物產出
                                                          100% 🎉
```

## 🧬 自我進化

系統不只是執行 — 它會**進化**。每一次失敗、每一個研究發現、每一次 agent 互動都會回饋進系統，讓它隨著時間越來越聰明。

### 失敗煉金術

當任務失敗時，系統不只是記錄下來，而是進行**煉金術** — 將失敗轉化為三種黃金：

| 產物 | 說明 | 作用方式 |
|------|------|---------|
| 🛡️ **抗體** | 預防策略 | 儲存在團隊記憶中，防止同類錯誤再次發生 |
| 💉 **疫苗** | 任務前預警 | 在類似任務啟動前注入警告：「開始 I2C 驅動前，確認 timeout 已設定...」 |
| ⚡ **催化劑** | Prompt 優化 | 注入 agent 的 system prompt，改變 agent 思考這類問題的方式 |

**實例**：高溫下 I2C 匯流排掛掉 → 抗體（加入 50ms timeout + bus reset）、疫苗（所有 I2C 驅動的事前檢查清單）、催化劑（agent 從此審查每一個阻塞呼叫的 timeout 覆蓋）。

### 研究循環

研究 agent 持續掃描新技術、競爭者動向、新興模式：

```
研究 Agent 掃描  →  發現提交  →  Agent 辯論相關性
                                    │
                    採納的發現 ─────┘
                         │
                    自動建立為 Idea 進入收件匣
                         │
                    Refine → Pipeline → Tasks → 交付物
```

這個循環自動餵養管線。被採納的研究直接變成實際工作 — 不需要人類輸入任何提示。

### 進化儀表板

打開 **http://localhost:5173/evolution** 可以看到：
- **健康指標卡**：活躍抗體數、疫苗數、研究轉化率、系統健康度
- **失敗煉金術面板**：每個失敗的抗體、疫苗、催化劑
- **研究循環面板**：所有發現與辯論筆記、採納流程、連結的 Idea

> 💡 *「你晚上離開，系統自己運作。隔天回來，發現抗體在你睡著時誕生了。」*

## 🤖 自主執行模式

不用再坐在電腦前按 yes — 系統可以自己跑。

### 快速啟動

```bash
# 啟動自主模式（每 5 分鐘執行一次週期）
./scripts/autonomous.sh

# 自訂間隔
./scripts/autonomous.sh 10m    # 每 10 分鐘
./scripts/autonomous.sh 30m    # 每 30 分鐘

# 只跑一個週期（測試用）
./scripts/autonomous.sh once

# 停止自主循環
./scripts/autonomous.sh stop
```

### 你離開後會發生什麼事

1. **API 伺服器自動啟動**（如果沒在跑）
2. **Dashboard 自動啟動**（如果沒在跑）
3. **Claude Code 進入 `/loop` 模式**，載入自主執行 prompt
4. 每個週期，系統會：
   - 掃描 Idea Inbox 新想法 → 精煉 → 建立管線
   - 檢查任務牆 → 執行下一個高優先級任務
   - 推進已完成的管線階段
   - 回報失敗 → 自動產生抗體/疫苗/催化劑
   - 每 5 個週期：執行研究掃描 → 提交發現
5. **不需要按任何許可** — `.claude/settings.json` 已預先授權

### 實際體驗

```
晚上 9:00 — 你輸入：./scripts/autonomous.sh 10m
晚上 9:00 — 你蓋上筆電去睡覺

你睡覺時：
  9:05 — CEO 接手 2 個高優先級任務
  9:15 — 研究 agent 發現 Zephyr 4.0 發布
  9:25 — 失敗煉金術分析 I2C timeout bug
  9:35 — 3 個任務完成，管線推進到測試階段
  ...

早上 7:00 — 你打開 Evolution 儀表板
          — 4 個抗體誕生，2 個研究發現被採納
          — 所有管線已推進，任務已完成
          — 你一個提示都沒發出
```

### 如何運作

| 組件 | 角色 |
|------|------|
| `scripts/autonomous.sh` | 啟動器 — 啟動 API、Dashboard、Claude Code `/loop` |
| `scripts/autonomous-prompt.md` | 自主執行指令 |
| `.claude/settings.json` | 權限白名單 — 不再跳出 yes/no |
| `/loop` 模式 | Claude Code 內建的重複執行引擎 |

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
# 同步依賴（含 dev tools）
uv sync

# 執行測試
uv run pytest

# Lint
uv run ruff check src/ tests/

# 型別檢查
uv run mypy src/ai_embedded_company/

# 啟動 API 伺服器
uv run aiteam serve --reload

# 啟動 MCP 伺服器
uv run aiteam mcp
```

## 📄 License

MIT — 做任何你想做的事，打造你自己的 AI 公司。
