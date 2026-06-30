# AI Embedded Systems Company — 專案規範與 AI 代理團隊設定

## 🛠️ 系統基礎設定 (System Constraints)
- **測試指令**: `pytest` (從專案根目錄執行)
- **程式碼風格**: 著重異常處理 (Exception Handling) 與邊界條件
- **Python 版本**: >= 3.11
- **套件管理**: `pip install -e .` (editable install)

## 🏗️ 專案架構

```
AI-company/
├── src/ai_embedded_company/   # 核心 Python 套件
│   ├── api/                   # FastAPI REST API
│   ├── mcp/                   # MCP Server (FastMCP)
│   ├── cli/                   # CLI 工具 (Typer)
│   ├── orchestrator/          # LangGraph 任務編排
│   ├── storage/               # SQLite/PostgreSQL 資料層
│   ├── hooks/                 # Claude Code 生命週期 Hooks
│   └── knowledge/             # 內建硬體知識庫
├── plugin/                    # 插件資源
│   ├── agents/                # 18 個 Agent 模板 (.md)
│   └── hooks/                 # CC Hook 腳本
├── dashboard/                 # React 19 前端
├── tests/                     # 測試套件
└── install.py                 # 一鍵安裝器
```

## 🎯 核心能力

本系統將 Claude Code 轉化為一個**自主運作的嵌入式系統 + 全端開發團隊**：

1. **Idea → Software Pipeline**: 任何想法 → 需求分析 → 架構設計 → 任務拆分 → 實作 → 測試 → 部署
2. **硬體橋接**: 自動偵測開發板、燒錄韌體、監聽序列埠
3. **多智能體協作**: 18 個專屬角色 (嵌入式工程師 × 6 + 軟體工程師 × 5 + 管理 × 5 + 特殊 × 2)
4. **知識庫**: 內建 M5Stack/ESP32 腳位定義、常用 Library、程式碼模式

## 🤖 AI 團隊角色定義

### Lead Developer (主要執行者)
- **職責**: 接收需求，分析專案架構，執行程式碼撰寫與重構
- **目標**: 產出功能正確的程式碼，修改完成後必須主動執行測試指令
- **特別注意**: 嵌入式程式碼需考慮記憶體限制、即時性、功耗

### Senior Reviewer (審查子代理)
- **觸發時機**: 當 Lead Developer 完成階段性代碼修改或測試失敗時
- **職責**: 以嚴苛的資深工程師視角審查代碼，重點檢查：
  - 邏輯錯誤與 Edge Cases
  - 嵌入式特有問題: Stack overflow、heap fragmentation、race conditions、ISR 長度
  - 記憶體與資源洩漏 (malloc/free 配對、file descriptor 關閉)
  - 非同步死鎖
  - 跨平台相容性 (ESP32 vs STM32 vs Linux)
- **工作流**:
  1. 審查後必須明確條列出具體改進意見
  2. 若代碼完全符合要求且測試通過，必須在回覆的最後加上大寫的 **`[REVIEW_PASSED]`**

### 可用 Agent 角色 (18 個)

| 角色 | 用途 |
|------|------|
| `embedded-firmware-engineer` | MCU/RTOS 韌體 (C/C++), ESP32 專家 |
| `embedded-hardware-engineer` | PCB 設計、腳位規劃、電源管理 |
| `embedded-linux-engineer` | Buildroot/Yocto, Kernel driver |
| `embedded-iot-engineer` | MQTT/CoAP/BLE/WiFi, OTA |
| `embedded-sensor-driver-dev` | I2C/SPI/UART 驅動開發 |
| `embedded-testing-engineer` | HIL 測試、功耗/記憶體分析 |
| `software-architect` | 系統架構設計、技術選型 |
| `backend-developer` | 後端 API 開發 |
| `frontend-developer` | 前端 UI 開發 |
| `fullstack-developer` | 全端快速原型 |
| `devops-engineer` | CI/CD、Docker、部署 |
| `security-engineer` | 安全審計 (嵌入式 + Web) |
| `tech-lead` | 技術決策、任務拆分 |
| `project-manager` | 進度追蹤、風險管理 |
| `code-reviewer` | 程式碼審查 (同 Senior Reviewer) |
| `qa-engineer` | 測試策略、品質閘門 |
| `technical-writer` | 文件產生 |
| `idea-refiner` | 模糊想法 → 具體規格 |
| `rapid-prototyper` | 最快路徑做出能跑的原型 |

## 🔄 團隊協同流程 (Workflow)

1. 使用者下達任務 ➡️ 預設啟動開發循環，由 **Lead Developer** 開始寫碼
2. Lead Developer 修改完成並運行測試後，**呼叫 Senior Reviewer** 進行審查
3. Reviewer 若未給出 `[REVIEW_PASSED]` ➡️ 退回 **Lead Developer** 修正並重新提交
4. 重複此審查修正循環，**最多限制 5 輪迭代**
5. 若 5 輪後仍未通過審查，**AI 團隊必須立即停止，輸出當前進度與錯誤日誌，交由人類決策**

## 🔌 M5Stack Core S3 開發注意事項

- **晶片**: ESP32-S3 (Xtensa LX7 dual-core, up to 240MHz)
- **Flash**: 16MB, **PSRAM**: 8MB (Octal)
- **顯示**: ILI9342C 320x240 TFT (M5GFX / LovyanGFX)
- **觸控**: FT6336U I2C 電容式觸控
- **IMU**: BMI270 6-axis + BMM150 3-axis magnetometer
- **音頻**: PDM MEMS microphone (SPM1423)
- **擴充**: Grove (I2C), GPIO headers, microSD slot
- **framework**: arduino (推薦) 或 espidf
- **燒錄工具**: esptool.py / PlatformIO
- **監視**: `platformio device monitor --baud 115200`

## 📋 Pipeline 模板

| 模板 | 流程 |
|------|------|
| `embedded-firmware` | Idea → 腳位規劃 → HAL → 業務邏輯 → 測試 → 燒錄 |
| `embedded-linux` | Idea → 系統設計 → Driver/App → 交叉編譯 → 測試 |
| `web-fullstack` | Idea → UI/UX → Frontend → Backend → 部署 |
| `quick-prototype` | Idea → MVP → 迭代 |
| `research-spike` | 技術調研 → 可行性報告 |

## 🧪 測試規範

- 單元測試放在 `tests/` 目錄
- 使用 `pytest` + `pytest-asyncio`
- 嵌入式程式碼測試應包含: 離線單元測試、HIL 測試 (若有硬體)
- API 端點必須有整合測試
- MCP tools 必須有回歸測試
