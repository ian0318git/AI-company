# Atmo Biosciences — 兩天 C++ 核心概念密集惡補計劃
# Atmo Biosciences — 2-Day C++ Core Concepts Intensive Bootcamp

> **目標 (Goal):** 徹底惡補 C++ 核心知識，達到「能教別人」的程度  
> **Target:** Master C++ core concepts to the level of "being able to teach others"  
> **對象 (Audience):** Senior/Lead Embedded Software Engineer 候選人  
> **公司背景 (Context):** Atmo Biosciences — Atmo Gas Capsule (可吞食氣體感測膠囊)  
> **技術棧 (Tech Stack):** Capsule C++ Firmware → Receiver → Cloud Python  
> **語言 (Language):** 繁體中文 + English 對照

---

## 📋 學習路徑總覽 / Learning Roadmap

```
Day 1 ──────────────────────────────────────────────
  AM │ Modern C++ (11/14/17/20) · RAII · 記憶體管理
  PM │ Templates · STL · 嵌入式實戰演練

Day 2 ──────────────────────────────────────────────
  AM │ Concurrency · RTOS · Design Patterns · SOLID
  PM │ Layered Architecture · Capstone · Lead 練習
```

---

# Day 1 — C++ 核心紮根 / Core Foundations

---

## ☀️ 上午 Session 1 — Modern C++ 與 RAII (4 小時)

### 1.1 Modern C++ 演進 / Evolution of Modern C++ (45 min)

| 版本 | 關鍵新特性 | 嵌入式影響 |
|------|-----------|-----------|
| C++11 | `auto`, `nullptr`, `move semantics`, `unique_ptr`, `lambda` | 零成本抽象、避免手動 `new/delete` |
| C++14 | `auto` return type, generic lambdas, `make_unique` | 更簡潔的泛型程式碼 |
| C++17 | `if constexpr`, structured bindings, `std::variant`, `std::optional` | 編譯期分支、安全錯誤處理 |
| C++20 | Concepts, coroutines, `std::span`, `std::format` | 介面約束、非同步 I/O、無所有權視圖 |

**💡 教學要點 (Teaching Point):**
> 「教別人 C++11/14/17/20 的關鍵，不是列出新特性，而是解釋 **為什麼** 委員會要加入它——解決了什麼痛點、帶來了什麼取捨。」
> "The key to teaching Modern C++ is not listing features, but explaining **why** the committee added each one — what pain point it solves, what trade-off it brings."

**🔬 Atmo 實例:**
```cpp
// C++17: std::variant 用於感測器資料類型安全聯合
// C++17: std::variant for type-safe sensor data union
struct TemperatureReading { int32_t value; };   // °C × 1000
struct PressureReading    { uint32_t value; };    // Pa
struct GasConcentration   { float value; };       // ppm
struct CalResult          { bool success; };
struct DiagStatus         { bool passed; };

using SensorData = std::variant<
    TemperatureReading,
    PressureReading,
    GasConcentration
>;

// 使用 std::visit 處理 variant (type-safe dispatch)
// Using std::visit for variant handling (type-safe dispatch)
void process_sensor_data(const SensorData& data) {
    std::visit([](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::same_as<T, TemperatureReading>) {
            // 處理溫度資料
        } else if constexpr (std::same_as<T, GasConcentration>) {
            // 處理氣體濃度資料
        }
    }, data);
}

// C++20: Concepts 約束氣體感測器介面
// C++20: Concepts constraining gas sensor interface
template <typename T>
concept GasSensor = requires(T s) {
    { s.read() } -> std::convertible_to<SensorData>;
    { s.calibrate() } -> std::same_as<CalResult>;
    { s.self_test() } -> std::same_as<DiagStatus>;
};
```

**📝 練習題 (Exercise):** 將一個 legacy C-style sensor driver 使用 C++17 重構，加入 `std::optional` 錯誤處理和 `std::span` 緩衝區視圖。

**❓ 面試問題 (Interview Q):**
> 「C++11 的 move semantics 如何解決嵌入式中的臨時物件複製開銷？在 ISR 中能用 `std::move` 嗎？」
> "How does C++11 move semantics solve temporary object copy overhead in embedded systems? Can you use `std::move` inside an ISR?"

---

### 1.2 RAII — 資源獲取即初始化 (60 min)

**核心概念 (Core Concept):**
> RAII 是 C++ 最強大的資源管理模式——資源在構造時獲取、在析構時釋放。這是 C++ 與 Java/C# GC 最根本的差異。

**五法則 (Rule of Five):**
```
class GasCapsuleBuffer {
    // 1. Destructor  ~GasCapsuleBuffer()
    // 2. Copy constructor GasCapsuleBuffer(const GasCapsuleBuffer&)
    // 3. Copy assignment   operator=(const GasCapsuleBuffer&)
    // 4. Move constructor  GasCapsuleBuffer(GasCapsuleBuffer&&) noexcept  // ⚡ noexcept 至關重要！
    // 5. Move assignment   operator=(GasCapsuleBuffer&&) noexcept
};
```
> **為什麼 `noexcept` 對 move 如此重要？** `std::vector` 擴容時，若 move constructor 為 `noexcept`，則容器會安全地 move 元素；否則會**退回 copy**，導致效能驟降且增加 ROM/RAM 開銷。在嵌入式場景中，這直接關乎 SRAM 預算能否被滿足。MISRA C++ 建議 move operations 必須標記 `noexcept`。
> **Why is `noexcept` critical for move?** When `std::vector` reallocates, if the move constructor is `noexcept`, elements are moved safely; otherwise the container **falls back to copy**, degrading performance and increasing ROM/RAM usage. In embedded systems this directly impacts SRAM budget. MISRA C++ mandates `noexcept` on all move operations.

**🔬 Atmo 實例 — 膠囊 SPI Flash 管理器:**
```cpp
class FlashManager {
    SPI_HandleTypeDef& spi_;
    uint8_t* cache_;
    size_t page_count_;
    bool owns_flush_ = true;  // ⚡ 追蹤 flush 責任歸屬
public:
    FlashManager(SPI_HandleTypeDef& spi, size_t pages)
        : spi_(spi)
        , page_count_(pages)
        , cache_(static_cast<uint8_t*>(malloc(pages * PAGE_SIZE))) {
        if (!cache_) throw std::bad_alloc();
    }

    // Move — 允許將 Flash 所有權傳遞（例如從初始化到運行階段）
    // 同時移交 flush 責任，防止原物件解構時略過 flush 而目標物件已先解構
    FlashManager(FlashManager&& other) noexcept
        : spi_(other.spi_)
        , cache_(std::exchange(other.cache_, nullptr))
        , page_count_(other.page_count_)
        , owns_flush_(std::exchange(other.owns_flush_, false)) {}  // 責任移交

    ~FlashManager() {
        if (cache_ && owns_flush_) {
            flush_cache_to_flash();  // 確保寫回
            free(cache_);
        }
    }

    // 禁止複製——Flash 資源不可共享
    FlashManager(const FlashManager&) = delete;
    FlashManager& operator=(const FlashManager&) = delete;
};
```

**💡 教學要點:**
> 「RAII 不是『語法糖』；它是 C++ 異常安全與資源安全的**基石**。教別人時，用 `mutex_lock` / `file_handle` 這種有明確 acquire/release 的資源來展示，比抽象的記憶體範例有效得多。」
> "RAII is not 'syntax sugar'; it is the **cornerstone** of C++ exception safety and resource safety. When teaching, use resources with explicit acquire/release like `mutex_lock` / `file_handle` — far more effective than abstract memory examples."

**📝 練習題:** 為 BMM150 磁力計封裝一個 RAII wrapper，包含 I2C handle 的獲取與釋放，確保初始化失敗時不洩漏 GPIO pin。

**❓ 面試問題:**
> 「在 Atmo 膠囊的醫療安全關鍵程式碼中，RAII 如何幫助確保 IEC 62304 的資源釋放驗證？」
> "In Atmo capsule's medical safety-critical code, how does RAII help with IEC 62304 resource release verification?"

---

### 1.3 記憶體管理 — Stack vs Heap 與嵌入式限制 (60 min)

**嵌入式記憶體層級 (Embedded Memory Hierarchy):**

| 區域 | 速度 | 大小 | 用途 |
|------|------|------|------|
| SRAM (TCM) | ~1 cycle | ~64 KB | 中斷向量、RTOS task stack |
| SRAM (普通) | ~3 cycles | ~512 KB | Heap、全局變數 |
| PSRAM (ESP32-S3) | ~10 cycles | 8 MB | 大型資料緩衝 |
| Flash Cache | ~5 cycles (cache hit) | 16 MB | 程式碼、constexpr 資料 |

**🔬 Atmo 實例 — 膠囊記憶體預算:**
```cpp
// 使用者自訂字面量：KB → bytes（僅限 constexpr 上下文）
// User-defined literal: KB → bytes (constexpr context only)
constexpr size_t operator""_KB(unsigned long long v) { return static_cast<size_t>(v * 1024); }

// 膠囊記憶體預算 (Capsule Memory Budget)
// 基於典型 ARM Cortex-M4 或 RISC-V 嵌入式平台
constexpr size_t TOTAL_RAM     = 256_KB;
constexpr size_t STACK_RESERVE =  32_KB;   // 主 task + 3 個 timer task
constexpr size_t SENSOR_BUFFER =  64_KB;   // 原始感測器 FIFO
constexpr size_t COMMS_BUFFER  =  32_KB;   // BLE 封包佇列
constexpr size_t LOG_BUFFER    =  16_KB;   // 診斷日誌環形緩衝
constexpr size_t HEAP_AVAIL    = 112_KB;   // 動態分配上限

// 禁止在 ISR 中分配
// No allocation in ISR — EVER
static_assert(HEAP_AVAIL + STACK_RESERVE +
              SENSOR_BUFFER + COMMS_BUFFER + LOG_BUFFER <= TOTAL_RAM,
              "Memory budget exceeded!");
```

**💡 教學要點:**
> 「嵌入式 C++ 的記憶體管理不是『別用 new』，而是『知道每個 byte 從哪來、何時歸還、誰擁有它』。教別人時，帶他們畫一張**記憶體地圖**——heap pool 多大、每個 subsystem 配多少、誰可以 allocate。」
> "Embedded C++ memory management isn't 'don't use new'. It's 'know where every byte comes from, when it is returned, who owns it.' When teaching, have them draw a **memory map** — heap pool size, each subsystem's budget, who is allowed to allocate."

**📝 練習題:** 為 Atmo 膠囊設計一個 `PoolAllocator<SensorReading, 64>`——固定大小的物件池，避免 heap fragmentation。

**❓ 面試問題:**
> 「在醫療級嵌入式系統中，為什麼 `malloc` 通常被禁止？你如何實現一個醫療安全的動態分配策略？」
> "In medical-grade embedded systems, why is `malloc` typically banned? How would you implement a medically-safe dynamic allocation strategy?"

---

### 1.4 `constexpr` / `consteval` 與編譯期計算 (45 min)

**💡 教學要點:**
> 「`constexpr` 不是優化技巧，是**正確性工具**——把運行期錯誤變成編譯期錯誤。」

**🔬 Atmo 實例:**
```cpp
// 編譯期計算氣體校準係數表
// Compile-time gas calibration coefficient table
// C++20 前 std::exp 非 constexpr，故手動實作泰勒展開
// std::exp is not constexpr before C++23, so use manual Taylor expansion

struct CalibrationPoint { uint16_t adc; float ppm; };

consteval float exp_approx(float x) {
    // 泰勒展開 e^x = 1 + x + x²/2! + x³/3! + ... (收斂快，8 項足夠)
    // Taylor series, 8 terms sufficient for fast convergence
    float result = 1.0f, term = 1.0f;
    for (int n = 1; n <= 8; ++n) {
        term *= x / static_cast<float>(n);
        result += term;
    }
    return result;
}

consteval auto generate_lookup_table() {
    std::array<CalibrationPoint, 256> table{};
    for (int i = 0; i < 256; ++i) {
        table[i] = CalibrationPoint{
            .adc = static_cast<uint16_t>(i * 16),
            .ppm = 0.5f * exp_approx(0.02f * static_cast<float>(i))  // 自訂 consteval 近似
        };
    }
    return table;
}

static constexpr auto CAL_TABLE = generate_lookup_table();
// 零運行期開銷，保證確定性 (Zero runtime cost, deterministic)
```

**📝 練習題:** 使用 `consteval` 實現一個編譯期 CRC32 計算器（用於韌體映像驗證）。

---

## 🌤️ 下午 Session 2 — Templates 與 STL (4 小時)

### 2.1 Template 基礎與特化 (60 min)

**核心概念:**
```
// 基礎樣板 (Base template)
template <typename T>
T max_value(T a, T b) { return (a > b) ? a : b; }

// 顯式特化 for int32_t (醫療安全需要明確 overflow 行為)
template <>
int32_t max_value<int32_t>(int32_t a, int32_t b) { ... }

// 部分特化 for pointer types
template <typename T>
class SensorQueue<T*> { ... };  // 指針版本的 queue 行為不同
```

**🔬 Atmo 實例 — 安全臨界模板模式:**
```cpp
// 確保所有 SensorDriver 實作必須提供 self_test
// CRTP: 靜態多型，零虛函數開銷
template <typename Derived>
class SensorDriverBase {
public:
    void init() {
        static_cast<Derived*>(this)->hardware_init();
    }
    DiagStatus run_diagnostics() {
        // C++20: requires 可在模板實例化時給出明確錯誤訊息
        // C++20: requires provides clear error message at template instantiation
        static_assert(requires { &Derived::self_test; }, "Derived must implement self_test()");
        return static_cast<Derived*>(this)->self_test();
    }
};

class BMISensor : public SensorDriverBase<BMISensor> {
public:
    void hardware_init() { /* BMI270 specific */ }
    DiagStatus self_test() { /* BMI270 self-test */ }
};
```

**📝 練習題:** 實作一個 `RingBuffer<T, N>` template class——支援 SPSC (single producer, single consumer)、IRQ safe。

---

### 2.2 Variadic Templates 與 Fold Expressions (45 min)

```cpp
// C++17 fold expression — 可變參數感測器初始化
template <typename... Sensors>
void init_all_sensors(Sensors&... sensors) {
    (sensors.init(), ...);          // 依序初始化所有感測器
    (sensors.calibrate(), ...);
    bool all_ok = (sensors.self_test().passed && ...);  // 全部通過？
}
```

---

### 2.3 STL 嵌入式子集 (60 min)

**可以使用 (Embedded-Safe STL):**

| 元件 | 原因 |
|------|------|
| `std::array<T, N>` | Stack allocation，零開銷 |
| `std::span<T>` | 非擁有視圖，安全迭代 |
| `std::optional<T>` | 明確的「有值/無值」 |
| `std::variant<T...>` | 類型安全 union |
| `std::byte` | 原始記憶體操作 |
| `std::numeric_limits` | 平台獨立限制查詢 |

**⚠️ 謹慎使用 (Use with Caution):**

| 元件 | 風險 | 替代方案 |
|------|------|---------|
| `std::vector` | Heap allocation | `StaticVector<T, N>` |
| `std::function` | Type erasure 開銷 | Function pointer / `etl::function` |
| `std::shared_ptr` | Atomic refcount | `unique_ptr` / raw pointer |
| `std::iostream` | 巨大的 code footprint | `sprintf` / `etl::string` |

**💡 教學要點:**
> 「教別人嵌入式 STL 時，重點不是『用不用』，而是『**審計**』——建立一個允許清單 (allowlist)，每個元件都要經過 ROM/RAM 開銷審查。」

---

### 2.4 嵌入式實戰演練：Templates 實現多感測器抽象層 (75 min)

**情境:** Atmo 膠囊需要支援多種氣體感測器（CO₂、CH₄、H₂S），每個有不同的通訊協定（I²C、SPI、UART）。

```cpp
// 抽象感測器介面 (零虛函數開銷)
template <typename SensorImpl>
class GasSensorInterface {
public:
    ReadResult read() {
        return static_cast<SensorImpl*>(this)->read_impl();
    }
};

// I²C CO₂ 感測器 (SCD4x)
class CO2Sensor : public GasSensorInterface<CO2Sensor> {
    I2CDevice i2c_;
public:
    ReadResult read_impl() {
        uint16_t co2;
        i2c_.read_register(0x08, &co2, 2);
        return ReadResult{co2, Status::OK};
    }
};

// SPI CH₄ 感測器
class CH4Sensor : public GasSensorInterface<CH4Sensor> {
    SPIDevice spi_;
public:
    ReadResult read_impl() { /* SPI transaction */ }
};
```

---

# Day 2 — 系統架構與設計 / System Architecture & Design

---

## ☀️ 上午 Session 1 — Concurrency、RTOS 與 Design Patterns (4 小時)

### 1.1 C++ Concurrency 嵌入式實戰 (60 min)

**關鍵差異 (Key Differences from Desktop C++):**

| 桌面端 | 嵌入式端 |
|--------|---------|
| `std::thread` (OS thread) | RTOS task (FreeRTOS `xTaskCreate`) |
| `std::mutex` | `std::mutex` + priority inheritance |
| `std::condition_variable` | FreeRTOS `xQueue` / `xSemaphore` |
| `std::future/promise` | 手工 event flag / message queue |

**🔬 Atmo 實例 — 膠囊任務架構:**
```cpp
// FreeRTOS task 定義 (C++ wrapper)
class CapsuleTask {
    TaskHandle_t handle_;
    StaticTask_t task_buffer_;          // 靜態分配，無 heap
    StackType_t stack_[2048];           // 明確的 stack 大小
public:
    template <auto Func>
    void start(const char* name, UBaseType_t priority) {
        handle_ = xTaskCreateStatic(
            [](void* arg) { static_cast<CapsuleTask*>(arg)->run<Func>(); },
            name, std::size(stack_), this, priority,  // ⚡ 使用 std::size() 確保與陣列一致
            stack_, &task_buffer_
        );
    }

    template <auto Func>
    [[noreturn]] void run() {
        while (true) Func();
    }
};

// 膠囊任務拆分 (Task Decomposition)
CapsuleTask sensor_task;     // 250 Hz 感測器輪詢
CapsuleTask process_task;    // 50 Hz 訊號處理
CapsuleTask comms_task;      // BLE 通訊
CapsuleTask watchdog_task;   // 1 Hz 健康監控
```

**💡 教學要點:**
> 「教嵌入式 concurrency 時，關鍵是 **priority inversion** 和 **deadlock prevention**。用 FreeRTOS 的 priority inheritance 機制和 `xQueue` 取代裸 `mutex` 作為教學切入點。」

**📝 練習題:** 實作一個 **lock-free SPSC queue**（用於 ISR → task 通訊），使用 `std::atomic` 和 `memory_order`。

**❓ 面試問題:**
> 「在 Atmo 膠囊中，感測器中斷 ISR 需要將資料傳遞到 processing task。你如何安全地做到零中斷丟失？為什麼不能用 `std::mutex` 在 ISR 中？」
> "In the Atmo capsule, a sensor interrupt ISR needs to pass data to the processing task. How do you do this safely with zero data loss? Why can't you use `std::mutex` in an ISR?"

---

### 1.2 嵌入式 Design Patterns (75 min)

#### 🏭 State Pattern — 膠囊狀態機

```cpp
// Atmo 膠囊生命週期狀態機
// Atmo Capsule Lifecycle State Machine
class CapsuleStateMachine {
    enum class State {
        BOOT,           // 開機自檢
        CALIBRATE,      // 感測器校準 (30s)
        STANDBY,        // 低功耗待命
        MEASURE,        // 主動量測
        TRANSMIT,       // BLE 傳輸
        ERROR,          // 錯誤恢復
        TERMINATE       // 安全關機 (排出)
    };

    State state_ = State::BOOT;
    State previous_ = State::BOOT;

public:
    EventResult handle_event(const CapsuleEvent& event) {
        previous_ = state_;
        switch (state_) {
            case State::BOOT:
                if (event.type == EventType::DIAG_PASS)
                    transition_to(State::CALIBRATE);
                break;
            case State::MEASURE:
                if (event.type == EventType::BUFFER_FULL)
                    transition_to(State::TRANSMIT);
                break;
            // ... 醫療級：每個 transition 都要 log
        }
        return EventResult::HANDLED;
    }

private:
    void transition_to(State new_state) {
        log_transition(previous_, new_state);  // IEC 62304 追蹤
        exit_action(state_);
        entry_action(new_state);
        state_ = new_state;
    }
};
```

#### 👁️ Observer Pattern — 感測器事件匯流排

```cpp
// 簡化版 publish-subscribe (RTOS 安全)
class EventBus {
    using Subscriber = void(*)(const SensorEvent&);
    std::array<Subscriber, 8> subs_{};  // 固定大小，無動態分配
    size_t count_{0};
public:
    bool subscribe(Subscriber sub) {
        if (count_ >= subs_.size()) return false;
        subs_[count_++] = sub;
        return true;
    }

    void publish(const SensorEvent& event) {
        for (size_t i = 0; i < count_; ++i) {
            subs_[i](event);  // 在 caller context 同步呼叫
        }
    }
    // ⚠️ RTOS 注意：同步 publish 可能導致 priority inversion
    // 若低優先級 task publish → 中優先級 subscriber 暫時「繼承」低優先級
    // 解決方案：改用 deferred queue-based dispatch
    // ⚠️ RTOS note: synchronous publish can cause priority inversion.
    // Fix: use deferred queue-based dispatch instead.
};
```

#### 🏭 Factory Pattern — 感測器工廠

> **⚠️ 醫療級系統注意：** 下方第一版使用 `std::make_unique`（heap allocation），在 IEC 62304 環境中通常僅允許在**初始化階段**動態分配。第二版展示**靜態 pool** 方案，適合運行期零分配要求。

```cpp
// ── 版本 A：初始化階段動態分配（適合 boot 時一次性建立）──
// Version A: Dynamic allocation during init (boot-time only)
class SensorFactory {
    I2CBus& i2c_;
    SPIBus& spi_;
public:
    std::unique_ptr<GasSensor> create_sensor(SensorType type) {
        switch (type) {
            case SensorType::CO2_SCD4X:
                return std::make_unique<SCD4xSensor>(i2c_);
            case SensorType::CH4:
                return std::make_unique<CH4Sensor>(spi_);
            case SensorType::H2S:
                return std::make_unique<H2SSensor>(i2c_);
        }
        return nullptr;
    }
};

// ── 版本 B：靜態 pool（零運行期分配，醫療安全）──
// Version B: Static pool (zero runtime allocation, medically safe)
template <typename T, size_t N>
class StaticPool {
    std::array<std::aligned_storage_t<sizeof(T), alignof(T)>, N> storage_;
    std::bitset<N> used_;
public:
    template <typename... Args>
    T* allocate(Args&&... args) {
        for (size_t i = 0; i < N; ++i) {
            if (!used_[i]) {
                used_[i] = true;
                return new (&storage_[i]) T(std::forward<Args>(args)...);
            }
        }
        return nullptr;  // pool exhausted
    }

    void deallocate(T* ptr) {
        ptr->~T();
        // 計算 index (implementation detail)
    }
};
```

**💡 教學要點:**
> 「教嵌入式 Design Patterns 的重點不是 GoF 書本的 23 個 pattern，而是 **嵌入式最常用的 5 個**：State、Observer、Factory、Command、Strategy。Focus 在**記憶體/時間開銷**的分析。」

---

### 1.3 SOLID 原則在嵌入式中的應用 (45 min)

| 原則 | 嵌入式意義 | Atmo 範例 |
|------|-----------|-----------|
| **S**RP | 每個模組只有一個變化的理由 | Sensor driver 不分擔 protocol logic |
| **O**CP | 對擴展開放、對修改封閉 | 新增感測器不修改現有程式碼 |
| **L**SP | 子類別可替代父類別 | 所有 `GasSensor` 實作可互換 |
| **I**SP | 不強迫實作不需要的介面 | `Calibratable` 與 `SelfTestable` 分離 |
| **D**IP | 依賴抽象，不依賴具體 | `SensorDriver` 依賴 `I2CBus` 介面 |

**🔬 Atmo 實例 — DIP 反例與修正:**
```cpp
// ❌ 違反 DIP：直接依賴硬體
class OldSensor {
    I2C_TypeDef* i2c_registers_;  // 直接操作暫存器
};

// ✅ 符合 DIP：依賴抽象匯流排
class NewSensor {
    II2CBus& bus_;  // 可以 injected，可 mock，可更換
};
```

---

## 🌤️ 下午 Session 2 — 系統架構、Capstone 與 Lead 練習 (4 小時)

### 2.1 Layered Architecture — 膠囊軟體分層 (60 min)

```
┌──────────────────────────────────────────┐
│             Application Layer             │
│  Gas Sampling · Logging · State Machine   │
├──────────────────────────────────────────┤
│            Service Layer                  │
│  Scheduler · Event Bus · Power Manager    │
├──────────────────────────────────────────┤
│            HAL Abstraction Layer          │
│  Sensor API · Flash API · Comms API       │
├──────────────────────────────────────────┤
│            Hardware Driver Layer          │
│  I2C · SPI · UART · GPIO · BLE Stack     │
├──────────────────────────────────────────┤
│            MCU Hardware                   │
│  ESP32-S3 / STM32 / nRF52840              │
└──────────────────────────────────────────┘
```

**💡 教學要點:**
> 「教 Layered Architecture 的關鍵是 **dependency direction** — 上層依賴下層，但不是直接依賴實作，而是依賴抽象介面。DIP 是讓這個分層『活起來』的關鍵。」

**📝 練習題:** 為 Atmo 膠囊設計一個 **Power Manager** 層，根據當前狀態動態調整各層電源模式（Active / Sleep / Deep Sleep）。

---

### 2.2 🏆 Capstone 專案：模擬 Atmo Gas Capsule Firmware (90 min)

**情境 (Scenario):**
> 你將設計一個**簡化但完整**的 Atmo Gas Capsule 韌體系統。膠囊每 10 秒讀取氣體感測器、處理訊號、經 BLE 傳輸到 Receiver。醫療等級的**錯誤處理、安全狀態機、電源管理**是核心要求。

**需求 (Requirements):**

1. **RAII 資源管理** — I²C、SPI、Timer 全部 RAII wrapper
2. **State Machine** — BOOT → CALIBRATE → MEASURE → TRANSMIT → TERMINATE
3. **Lock-free 資料管線** — ISR → processing → transmission
4. **Power Management** — 量測間隔進入 sleep
5. **Watchdog** — 硬體 watchdog 搭配 alive heartbeat
6. **IEC 62304 準備** — 每個狀態轉換 log、錯誤計數器、safe state

**預期產出 (Expected Deliverables):**

```
src/
├── main.cpp                  // Entry point, task creation
├── drivers/
│   ├── i2c_bus.h/.cpp        // RAII I²C bus
│   ├── sensor_scd4x.h/.cpp   // CO₂ sensor driver
│   └── bmi270.h/.cpp         // IMU driver
├── hal/
│   ├── sensor_interface.h    // Abstract sensor API
│   └── flash_interface.h     // Abstract storage API
├── services/
│   ├── state_machine.h/.cpp  // Capsule lifecycle
│   ├── event_bus.h/.cpp      // Pub-sub event bus
│   ├── power_manager.h/.cpp  // Power mode control
│   └── data_pipeline.h/.cpp  // Lock-free sensor data flow
└── utils/
    ├── ring_buffer.h         // SPSC ring buffer
    ├── crc32.h               // Compile-time CRC
    └── logger.h              // Diagnostic logging
```

**實作提示 (Implementation Hints):**

```cpp
// 主循環 (Main Loop)
void measure_task(void*) {
    auto& sm = CapsuleStateMachine::instance();
    auto& pipeline = DataPipeline::instance();

    while (true) {
        switch (sm.current_state()) {
            case State::MEASURE: {
                auto data = sensor.read();       // RAII: 自動管理 SPI transaction
                pipeline.push(data);             // Lock-free: ISR safe
                sm.handle(Event::DATA_READY);
                break;
            }
            case State::TRANSMIT: {
                auto data = pipeline.pop();
                ble_service.send(data);
                sm.handle(Event::TX_COMPLETE);
                break;
            }
        }
        power_mgr.sleep_until_next_sample();     // 進入 light sleep
    }
}
```

---

### 2.3 Lead 能力練習 — Code Review 與架構講解 (60 min)

#### 🎯 練習 A：Code Review 實戰

**Review 以下程式碼片段 (Review the following snippet):**

```cpp
// 候選人提交的感測器初始化程式碼
// Candidate's submitted sensor init code
class SensorManager {
    std::vector<Sensor*> sensors_;      // 問題：heap allocation
    bool initialized_ = false;
public:
    void init() {
        for (auto s : sensors_) {       // 問題：未檢查 nullptr
            s->init();
        }
        initialized_ = true;
    }

    void calibrate() {
        for (auto s : sensors_) {
            s->calibrate();             // 問題：無錯誤處理
        }
    }

    ~SensorManager() {                  // 問題：未釋放 resources
        for (auto s : sensors_) {
            delete s;                   // 問題：誰擁有所有權不明確
        }
    }
};
```

**你必須找出 (You must find):**
1. ❌ 關鍵問題 → 修復方案
2. ⚠️ 次要問題 → 改進建議
3. 🔍 醫療安全顧慮 → 如何符合 IEC 62304

#### 🎯 練習 B：白板架構講解

**主題 (Topic):**
> 「請用白板畫出 Atmo Gas Capsule 的端到端系統架構，並解釋以下三個 cross-cutting concerns：」
> "Draw on the whiteboard the end-to-end system architecture of the Atmo Gas Capsule, and explain these three cross-cutting concerns:"

1. **時序保證 (Timing Guarantees)** — 如何確保 10 秒量測週期不被 BLE TX 阻塞？
2. **錯誤隔離 (Error Isolation)** — 當 H₂S 感測器故障時，如何不影響 CO₂ 量測？
3. **安全關機 (Safe Shutdown)** — 電池低電量時，如何確保資料不遺失？

#### 🎯 練習 C：教學演示

**模擬教學場景 (Simulated teaching):**
> 「用 5 分鐘教一位 junior engineer 為什麼 RAII 在醫療嵌入式系統中至關重要。」
> "Teach a junior engineer in 5 minutes why RAII is critical in medical embedded systems."

---

### 2.4 醫療法規與 DevOps (30 min)

**IEC 62304 對 C++ 的影響:**
```
IEC 62304 Clause │ C++ 對應措施
─────────────────┼──────────────────────────
5.2.6  │ 避免未定義行為 (UB)：限制 reinterpret_cast 於 MMIO 暫存器存取（須文件化 + code review）；禁止 union type punning
5.5.3  │ 記憶體分析：使用 RAII + pool allocator 取代 dynamic allocation
7.1    │ 單元測試覆蓋率：C++ template 程式碼需要 100% MC/DC
8.1.2  │ 靜態分析：MISRA C++ / AUTOSAR C++ 規範
```

**Azure DevOps 整合:**
```yaml
# CI/CD pipeline for medical firmware
jobs:
- job: StaticAnalysis
  steps:
  - run: cppcheck --std=c++20 --suppress=*:tests/* src/

- job: UnitTest
  steps:
  - run: pytest tests/          # Python test harness for C++ modules

- job: HIL_Test
  steps:
  - run: pytest tests/hil/       # Hardware-in-the-loop
```

---

## 📚 進階資源 / Advanced Resources

| 領域 | 資源 |
|------|------|
| Modern C++ | 《Effective Modern C++》Scott Meyers |
| Embedded C++ | 《Real-Time C++》Christopher Kormanyos |
| Design Patterns | 《Head First Design Patterns》 |
| MISRA C++ | MISRA C++ 2023 Guideline |
| FreeRTOS | 《Mastering the FreeRTOS Real Time Kernel》 |
| IEC 62304 | 《Medical Device Software》 |
| Atmo 相關 | Atmo Biosciences Gas Capsule White Papers |

---

## 🏁 結論 / Conclusion

這個兩天計劃涵蓋了從 Modern C++ 基礎到嵌入式系統架構的完整路徑，特別針對 Atmo Biosciences 的 **Atmo Gas Capsule** —— 一個典型的 **C++ 嵌入式韌體 + Python 雲端處理** 端到端系統。

**兩天後你將能:**
1. ✅ 用 Modern C++ (C++17/20) 寫出安全、高效的嵌入式程式碼
2. ✅ 設計並實現 RAII 資源管理的 sensor driver 架構
3. ✅ 應用 State/Observer/Factory Pattern 於 RTOS 環境
4. ✅ 分析並修正嵌入式 C++ 的記憶體與 concurrency 問題
5. ✅ 執行 Code Review 並以 Lead 身分指導 junior engineers
6. ✅ 將 IEC 62304 規範融入 C++ 開發流程

> **最終目標：** 不是「會用」C++，而是能**教別人**為什麼、何時、如何用 C++ 建構醫療級的嵌入式系統。

**This 2-day plan covers the complete path from Modern C++ foundations to embedded system architecture, specifically targeting Atmo Biosciences' Atmo Gas Capsule — a classic C++ embedded firmware + Python cloud processing end-to-end system.**

**After two days you will be able to:**
1. ✅ Write safe, efficient embedded code in Modern C++ (C++17/20)
2. ✅ Design and implement RAII-based sensor driver architectures
3. ✅ Apply State/Observer/Factory Patterns in RTOS environments
4. ✅ Analyze and fix memory and concurrency issues in embedded C++
5. ✅ Conduct Code Reviews and mentor junior engineers as a Lead
6. ✅ Integrate IEC 62304 requirements into C++ development workflow

> **Ultimate Goal:** Not just "using" C++, but being able to **teach others** why, when, and how to use C++ to build medical-grade embedded systems.
