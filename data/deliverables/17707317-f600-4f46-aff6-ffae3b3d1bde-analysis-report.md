# 撰寫 Diag Function Spec 流程分析報告

**專案**: 撰寫Diag function spac | **日期**: 2026-07-07
**來源文件**: `Fugazi Hardware Functional Specification__rev4.00.docx`
**產出文件**: `Fugazi_Diags_Func_Spec_v2.0_approved.doc`

---

## 摘要

本報告分析從一份硬體功能規格書 (HFS) 撰寫診斷功能規格書 (DFS) 的完整流程，
並歸納為可重複使用的技能，讓 AI 未來能自動化完成此工作。

---

## 1. 輸入分析 (Input Parsing)

### 1.1 HFS 關鍵章節映射

| HFS 章節 | 用途 | DFS 對應 |
|----------|------|----------|
| Block Diagram / System Overview | 理解硬體拓撲 | Test Path Block Diagram |
| Memory Map / Address Tables | 定址與暫存器 | Register Test 範圍 |
| Bus Topology (PCIe/I2C/SPI) | 匯流排架構 | Bus Scan 與 Loopback 測試 |
| Clock Tree | 時脈分配 | Clock Recovery 測試 |
| Power Sequencing | 上電時序 | Power Rail 驗證 |
| Environmental Specs | 溫度/電壓範圍 | EDVT Margin 測試 |
| Connector Pinouts | 外部介面 | External Loopback 測試 |
| Programming / Firmware | 可程式元件 | Firmware Provisioning |

### 1.2 可測試節點盤點 (BOM of Testable Nodes)

從 HFS 中提取的所有需要測試的硬體節點：

- **CPU/SoC**: 核心、Cache、記憶體控制器
- **Memory**: DDR4 DIMM slots, SPI Flash, eMMC/NVMe
- **Network**: MAC/PHY chips (PCIe, SGMII, XFI), SFP cages
- **Storage**: SATA/SAS controllers, NVMe
- **Clocks**: PLL, 參考時脈, Recovered clocks
- **Power**: 電壓 rails, 電源 sequencer, PMBus
- **Management**: BMC, CPLD, FPGA, TPM
- **Sensors**: 溫度 sensor, 電壓 monitor, fan tach
- **Interfaces**: USB, UART, I2C, SPI, GPIO, JTAG

---

## 2. 流程方法論 (Methodology)

### Phase 1: HFS 解析與邊界定義
```
HFS → 提取 Block Diagram → 建立 Bus Topology Map → 
列出所有 Testable Nodes → 標註相依性
```

### Phase 2: 測試覆蓋策略分配
```
For each node:
  └─ Explicit? → Dedicated test case + Failure Analysis
  └─ Implicit? → OS boot / driver probe 驗證
  └─ Manual?   → Utility tool + Debugging Steps
```

### Phase 3: 測試案例撰寫
```
For each Explicit test:
  1. Description & Algorithm
  2. Test Path Block Diagram
  3. Preconditions
  4. Failure Analysis (物理意義)
  5. Debugging Steps (隔離流程)
```

### Phase 4: 系統整合
```
Utilities Inventory → Firmware Provisioning → Boot Environment
```

---

## 3. 關鍵模式識別 (Key Patterns)

### 3.1 分層 Loopback 模式

這是最重要的測試設計模式：

```
Layer 1: Register Test (暫存器存取) 
  → 驗證 bus interface 基本通訊
Layer 2: Internal Loopback (內部迴路)
  → MAC↔PHY 數位介面測試
Layer 3: External Loopback (外部迴路)
  → 透過 connector/SFP 的實體層測試
```

**Failure Analysis 規則**:
- Layer 1 pass + Layer 2 fail = PHY 晶片問題
- Layer 2 pass + Layer 3 fail = Connector/Trace 問題
- Layer 1 fail = Bus/CPU 問題

### 3.2 測試覆蓋矩阵 (Coverage Matrix)

決定每個節點的測試策略時，需考慮:

| 因素 | Explicit | Implicit | Manual |
|------|----------|----------|--------|
| 安全關鍵 | ✅ | ❌ | ❌ |
| 低階匯流排 | ✅ | ❌ | ❌ |
| 標準驅動可用 | ❌ | ✅ | ❌ |
| EDVT 需要 | ❌ | ❌ | ✅ |

### 3.3 Fault Isolation Tree

每個測試案例必須包含故障隔離樹：

```
Test Failed
  └─ Check Interface (cable/connector)
     └─ Loopback Lower Layer
        └─ Component Substitution
           └─ Escalate to Hardware Team
```

---

## 4. 重複使用元件 (Reusable Assets)

### 4.1 測試案例模板

每個 Explicit test 使用統一的模板結構：

```markdown
### Test: [Test Name]

**Description**: [技術描述 + 測試演算法]
**Test Path**: [Block Diagram 編號]
**Preconditions**: [前置條件]

**Failure Analysis**: [失敗的物理意義]

**Debugging Steps**:
1. [第一步驟]
2. [第二步驟]
3. [第三步驟]
```

### 4.2 Bus Scanner 工具定義

每個 bus interface 需要定義 scanner utility：

| Bus | Tool | 驗證項目 |
|-----|------|----------|
| PCIe | `lspci` / `setpci` | Device/Vendor ID, Link Status |
| I2C | `i2cdetect` / `i2cget` | Device Address, Register Read |
| SPI | `spidev_test` | Read/Write, Speed |
| MDIO | `mdiobus` / `mv88e6xxx_dump` | PHY ID, Link Status |
| SMBus | `i2cget` / `pmbus` | Voltage, Temp, Power |

### 4.3 預設測試套件層級

```
Default Test Suite (Manufacturing):
  └─ boot_test       → OS 啟動驗證
  └─ cpu_test        → CPU/Cache 測試
  └─ mem_test        → 記憶體測試 (MARCH C-)
  └─ i2c_scan        → I2C 裝置掃描
  └─ pci_scan        → PCIe 裝置掃描
  └─ net_loopback    → 網路埠 Loopback
  └─ storage_test    → 儲存裝置測試

Extended Test Suite (EDVT):
  └─ 上述全部 + margin_test + stress_test + temp_cycle
```

---

## 5. 技能封裝 (Skill Encapsulation)

本分析已封裝為 **`hfs-to-dfs-writer`** skill，位於：
- `~/.claude/skills/hfs-to-dfs-writer/`

### Skill 包含

| 元件 | 說明 |
|------|------|
| Phase 1-4 流程 | HFS 解析 → 覆蓋策略 → 測試案例 → 系統整合 |
| 文件模板 | 完整的 DFS 目錄結構 (references/document-skeleton.md) |
| 覆蓋矩陣模板 | 欄位結構與範例 (references/coverage-matrix-template.md) |
| 測試案例模板 | 含 Failure Analysis + Debugging Steps |
| 防幻覺檢查 | 確保 DFS 不超出 HFS 的範圍 |

### 使用方式

Claude Code 中直接說：
> 「幫我根據這份 HFS 撰寫 DFS」
> 或
> 「用 hfs-to-dfs-writer skill 產出診斷規格書」

---

## 附錄 A: 文件比較摘要

| 項目 | HFS (來源) | DFS (產出) |
|------|-----------|-----------|
| 檔案 | `Fugazi_HW_Spec_rev4.00.docx` | `Fugazi_Diags_Spec_v2.0.doc` |
| 大小 | 1.9 MB | 4.1 MB |
| 主要內容 | 硬體規格、Block Diagram、Pinout | 測試案例、Coverage Matrix |
| 目標讀者 | 硬體工程師 | 測試/製造/EDVT 工程師 |

## 附錄 B: 自動化建議

1. **HFS Parser**: 自動從 HFS 中提取 Block Diagram 與 BOM
2. **Coverage Generator**: 根據 BOM 自動生成覆蓋矩陣
3. **Test Stub Generator**: 根據矩陣自動生成測試案例 stub
4. **Traceability Checker**: 驗證 DFS 內容是否對應到 HFS 章節
