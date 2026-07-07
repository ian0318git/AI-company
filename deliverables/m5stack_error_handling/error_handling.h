/**
 * @file error_handling.h
 * @brief Error handling and watchdog subsystem for M5Stack Core S3 + StackChan
 *
 * This module provides a unified error handling framework covering:
 *   - Error code taxonomy (hardware, communication, runtime, system)
 *   - Watchdog timer configuration with multi-tier timeouts
 *   - Crash recovery with persistent error logging to RTC memory
 *   - I2C communication timeout and retry with exponential backoff
 *   - Graceful degradation (component isolation, safe mode fallback)
 *   - Error event callback system for UI/display feedback
 *
 * Hardware context:
 *   - M5Stack Core S3 (ESP32-S3, 240MHz, 8MB PSRAM, 16MB Flash)
 *   - PCA9685 servo driver on Grove I2C (GPIO 1/2)
 *   - BMI270 IMU on internal I2C (GPIO 8/9)
 *   - FT6336U touch on internal I2C (GPIO 8/9)
 *   - SPM1423 PDM mic (GPIO 47 CLK, GPIO 14 DATA)
 *   - ILI9342C TFT via SPI
 *   - Two SG90 servos via PCA9685 channels 0/1
 *
 * @author AI Embedded Systems Team
 * @date 2026-07-08
 */

#ifndef M5STACK_ERROR_HANDLING_H
#define M5STACK_ERROR_HANDLING_H

#include <cstdint>
#include <cstddef>
#include <functional>

// ============================================================================
// Configuration Constants
// ============================================================================

/// Maximum number of registered error callbacks
#define EH_MAX_CALLBACKS         8

/// Maximum consecutive I2C retries before escalation
#define EH_I2C_MAX_RETRIES       5

/// Maximum consecutive app crashes before forcing safe mode
#define EH_MAX_CRASHES_BEFORE_SAFE 5

/// I2C timeout in milliseconds for PCA9685 communication
#define EH_I2C_TIMEOUT_MS        50

/// I2C timeout in milliseconds for internal sensor communication
#define EH_I2C_SENSOR_TIMEOUT_MS 100

/// Watchdog timeout tiers (milliseconds)
#define EH_WDT_NORMAL_TIMEOUT_MS     3000   ///< Normal operation (3s)
#define EH_WDT_EXTENDED_TIMEOUT_MS   8000   ///< Extended (firmware update, 8s)
#define EH_WDT_CRITICAL_TIMEOUT_MS   15000  ///< Critical recovery (15s)

/// RTC memory signature for crash persistence validation
#define EH_RTC_SIGNATURE          0xDEADBEEF

/// Maximum length of an error context description string
#define EH_CONTEXT_STR_LEN        64

// ============================================================================
// Error Code Enumeration
// ============================================================================

/**
 * @brief Unified error code taxonomy for the M5Stack + StackChan system.
 *
 * Organized by subsystem with bit-field compatible layout:
 *   Bits 31-24: Category     (0x01=HW, 0x02=COMM, 0x04=RUNTIME, 0x08=SYSTEM)
 *   Bits 23-16: Subsystem    (I2C, SPI, SERVO, IMU, TOUCH, MIC, DISPLAY, WDT)
 *   Bits 15-0:  Specific code
 */
enum class ErrorCode : uint32_t {
    // ---- Success / No Error ----
    OK                          = 0x00000000,

    // ---- Hardware Errors (Category 0x01) ----
    HW_I2C_INIT_FAILURE         = 0x01000101, ///< I2C bus initialization failed
    HW_I2C_DEVICE_NOT_FOUND     = 0x01000102, ///< Device not responding on I2C bus
    HW_I2C_NACK                 = 0x01000103, ///< I2C NACK received
    HW_I2C_ARBITRATION_LOST     = 0x01000104, ///< I2C bus arbitration lost
    HW_SPI_INIT_FAILURE         = 0x01000201, ///< SPI bus initialization failed
    HW_SPI_TRANSFER_FAILED      = 0x01000202, ///< SPI transfer error
    HW_PCA9685_WRITE_FAILED     = 0x01000301, ///< PCA9685 register write failure
    HW_PCA9685_READ_FAILED      = 0x01000302, ///< PCA9685 register read failure
    HW_PCA9685_OSC_FAILURE      = 0x01000303, ///< PCA9685 oscillator error (check EXTCLK)
    HW_SERVO_PWM_OUT_OF_RANGE   = 0x01000304, ///< Servo PWM value exceeds safe limits
    HW_SERVO_STALL_DETECTED     = 0x01000305, ///< Servo current spike / stall detected
    HW_IMU_INIT_FAILURE         = 0x01000401, ///< BMI270 initialization failed
    HW_IMU_READ_FAILURE         = 0x01000402, ///< BMI270 register read failure
    HW_IMU_FIFO_OVERFLOW        = 0x01000403, ///< BMI270 FIFO buffer overflow
    HW_TOUCH_INIT_FAILURE       = 0x01000501, ///< FT6336U touch init failed
    HW_TOUCH_READ_FAILURE       = 0x01000502, ///< FT6336U read failure
    HW_MIC_INIT_FAILURE         = 0x01000601, ///< SPM1423 PDM mic init failed
    HW_MIC_OVERFLOW             = 0x01000602, ///< Mic audio buffer overflow
    HW_DISPLAY_INIT_FAILURE     = 0x01000701, ///< ILI9342C display init failed
    HW_DISPLAY_REFRESH_FAILURE  = 0x01000702, ///< Display refresh / DMA error
    HW_RGB_LED_FAILURE          = 0x01000801, ///< SK6812 NeoPixel communication error
    HW_ADC_READ_FAILURE         = 0x01000901, ///< ADC conversion failure

    // ---- Communication Errors (Category 0x02) ----
    COMM_I2C_TIMEOUT            = 0x02000101, ///< I2C transaction timed out
    COMM_I2C_RETRY_EXCEEDED     = 0x02000102, ///< I2C max retries exceeded
    COMM_SPI_TIMEOUT            = 0x02000201, ///< SPI transaction timed out
    COMM_SERIAL_FRAMING_ERROR   = 0x02000301, ///< UART serial framing error
    COMM_SERIAL_OVERRUN         = 0x02000302, ///< UART serial buffer overrun
    COMM_SERIAL_PARITY_ERROR    = 0x02000303, ///< UART serial parity mismatch
    COMM_PROTOCOL_MISMATCH      = 0x02000401, ///< Protocol version / format mismatch
    COMM_CHECKSUM_FAILURE       = 0x02000402, ///< Data checksum verification failed

    // ---- Runtime Errors (Category 0x04) ----
    RT_SCHEDULER_OVERRUN        = 0x04000101, ///< Task exceeded scheduling deadline
    RT_STACK_OVERFLOW           = 0x04000201, ///< Task stack overflow detected
    RT_HEAP_ALLOC_FAILED        = 0x04000301, ///< Heap memory allocation failed
    RT_HEAP_CORRUPTION          = 0x04000302, ///< Heap integrity check failed
    RT_TASK_WATCHDOG_EXPIRED    = 0x04000401, ///< Task watchdog timer expired
    RT_QUEUE_FULL               = 0x04000501, ///< Message queue full (dropped message)
    RT_QUEUE_RECEIVE_TIMEOUT    = 0x04000502, ///< Message queue receive timed out
    RT_MUTEX_LOCK_FAILED        = 0x04000601, ///< Mutex lock acquisition failed
    RT_MUTEX_TIMEOUT            = 0x04000602, ///< Mutex lock timed out
    RT_ISR_VIOLATION            = 0x04000701, ///< Blocking operation in ISR context
    RT_NULL_POINTER             = 0x04000801, ///< Unexpected null pointer dereference
    RT_INVALID_PARAMETER        = 0x04000802, ///< Invalid function parameter
    RT_APP_TRANSITION_FAILURE   = 0x04000901, ///< App state transition error

    // ---- System Errors (Category 0x08) ----
    SYS_WDT_TIMEOUT             = 0x08000101, ///< Hardware watchdog timer expired
    SYS_WDT_RESET_OCCURRED      = 0x08000102, ///< System reset due to WDT (detected at boot)
    SYS_PANIC_ASSERT_FAIL       = 0x08000201, ///< Assertion failure (panic)
    SYS_CRASH_UNHANDLED_EXCEPT  = 0x08000202, ///< Unhandled CPU exception
    SYS_POWER_FAILURE           = 0x08000301, ///< Power supply voltage out of range
    SYS_THERMAL_SHUTDOWN        = 0x08000302, ///< Overtemperature shutdown
    SYS_BROWNOUT_DETECTED       = 0x08000303, ///< Brown-out condition detected
    SYS_RTC_DATA_CORRUPT        = 0x08000401, ///< RTC memory checksum mismatch
    SYS_SAFE_MODE_ACTIVE        = 0x08000501, ///< System running in safe mode
    SYS_FATAL_UNRECOVERABLE     = 0x08FF0001, ///< Unrecoverable fatal error
};

// ============================================================================
// Error Severity Levels
// ============================================================================

enum class ErrorSeverity : uint8_t {
    DEBUG       = 0,  ///< Informational, no action needed
    INFO        = 1,  ///< Notable event, system normal
    WARNING     = 2,  ///< Degraded condition, system functional
    ERROR       = 3,  ///< Component failure, recovery attempted
    CRITICAL    = 4,  ///< System may become unstable
    FATAL       = 5,  ///< System will reset or stop
};

// ============================================================================
// Recovery Action / Degradation Levels
// ============================================================================

/**
 * @brief Graceful degradation levels, from full operation to safe mode.
 */
enum class DegradationLevel : uint8_t {
    FULL_OPERATION      = 0, ///< All subsystems nominal
    DISPLAY_FALLBACK    = 1, ///< Servo failed, display-only mode (UI fallback)
    SERVO_FALLBACK      = 2, ///< Display failed, servo-only mode (blind operation)
    SENSOR_FALLBACK     = 3, ///< Some sensors offline, use last-known-good data
    COMM_FALLBACK       = 4, ///< I2C bus degraded, reduced update rate
    SAFE_MODE           = 5, ///< All non-critical subsystems disabled
    HALT                = 6, ///< System halted, requires manual reset
};

// ============================================================================
// Watchdog Timer Configuration
// ============================================================================

/**
 * @brief Watchdog timer configuration structure.
 *
 * ESP32-S3 has two watchdog timers:
 *   - TWDT (Task Watchdog Timer) — monitors individual FreeRTOS tasks
 *   - MWDT (Main Watchdog Timer) — hardware WDT, resets SoC on timeout
 *
 * This module configures both for multi-tier protection.
 */
struct WatchdogConfig {
    /// Main hardware WDT timeout in milliseconds (MWDT)
    uint32_t hw_timeout_ms = EH_WDT_NORMAL_TIMEOUT_MS;

    /// Task WDT timeout in milliseconds (TWDT)
    uint32_t task_timeout_ms = EH_WDT_NORMAL_TIMEOUT_MS;

    /// Enable panic on WDT expiry (vs. reset only)
    bool panic_on_timeout = false;

    /// Enable watchdog during deep sleep (if applicable)
    bool enable_during_sleep = false;

    /// Automatically feed the WDT from a high-priority timer
    bool auto_feed_enabled = true;

    /// Feed interval in milliseconds (must be < hw_timeout_ms/2)
    uint32_t auto_feed_interval_ms = 1000;

    /// Reset reason register snapshot at last boot
    uint32_t last_reset_reason = 0;
};

// ============================================================================
// Persistent Crash Record (stored in RTC memory)
// ===========================================================================/

/**
 * @brief Crash record stored in RTC_NOINIT memory for post-reset analysis.
 *
 * The ESP32-S3 RTC memory retains data across deep sleep and warm resets,
 * enabling crash forensics on the next boot.
 *
 * Layout: Must be word-aligned and sized to fit RTC slow memory (~8KB available).
 * We reserve a small portion at a fixed offset.
 */
struct CrashRecord {
    /// Validation signature (EH_RTC_SIGNATURE)
    uint32_t signature = 0;

    /// Number of consecutive crashes since last clean boot
    uint32_t crash_count = 0;

    /// Error code of the most recent crash
    ErrorCode last_error = ErrorCode::OK;

    /// Severity of the most recent crash
    ErrorSeverity last_severity = ErrorSeverity::DEBUG;

    /// Timestamp of last crash (milliseconds since boot or RTC tick)
    uint32_t crash_timestamp_ms = 0;

    /// Program counter at crash time
    uint32_t crash_pc = 0;

    /// Exception cause (e.g., EXCCAUSE register on Xtensa)
    uint32_t exception_cause = 0;

    /// Task name / ID where crash occurred
    char task_name[32] = {};

    /// Context description string
    char context[EH_CONTEXT_STR_LEN] = {};

    /// Checksum over this structure (XOR of all uint32_t fields)
    uint32_t checksum = 0;

    /**
     * @brief Compute checksum over the CrashRecord fields.
     * @return XOR checksum of the raw word data.
     */
    uint32_t computeChecksum() const;

    /**
     * @brief Validate the stored checksum against a recomputed one.
     * @return true if the record is intact.
     */
    bool isValid() const;

    /**
     * @brief Update the checksum field after modifying record data.
     */
    void updateChecksum();
};

// ============================================================================
// Error Event / Callback System
// ============================================================================

/**
 * @brief Structure passed to registered error callbacks.
 */
struct ErrorEvent {
    ErrorCode       code;         ///< The error code
    ErrorSeverity   severity;     ///< Severity level
    DegradationLevel degradation; ///< Current system degradation level
    uint32_t        timestamp_ms; ///< Event timestamp (milliseconds since boot)
    const char*     message;      ///< Human-readable description (may be nullptr)
    void*           context;      ///< Optional context pointer
};

/**
 * @brief Callback function type for error events.
 *
 * Called from the error handling context. Implementations should:
 *   - Be non-blocking (avoid delays > 1ms)
 *   - Not call back into the error handling system (no recursion)
 *   - Not allocate heap memory
 *
 * @param event Pointer to the error event structure (valid only during callback)
 */
using ErrorCallback = void (*)(const ErrorEvent* event);

// ============================================================================
// I2C Communication Timeout Configuration
// ============================================================================

/**
 * @brief Per-device I2C timeout and retry configuration.
 */
struct I2CDeviceConfig {
    /// I2C device address (7-bit)
    uint8_t  address;

    /// Friendly device name (for logging)
    const char* name;

    /// Timeout per transaction in milliseconds
    uint32_t timeout_ms = EH_I2C_TIMEOUT_MS;

    /// Maximum consecutive retries before escalating
    uint8_t  max_retries = 3;

    /// Exponential backoff: initial delay in milliseconds
    uint8_t  retry_delay_base_ms = 5;

    /// Backoff multiplier (2 = double each retry)
    uint8_t  retry_backoff_multiplier = 2;

    /// Number of communication failures since last success
    uint8_t  consecutive_failures = 0;

    /// Whether this device is currently marked as failed
    bool     is_failed = false;

    /// Flag to skip retries and return immediately on this device
    bool     skip_on_failure = false;
};

// ============================================================================
// Predefined I2C Device Configurations
// ============================================================================

/// PCA9685 on Grove I2C (GPIO 1/2) at 0x40
extern const I2CDeviceConfig I2C_DEV_PCA9685;

/// When using Option B (GPIO passthrough), PCA9685 on internal I2C (GPIO 8/9)
extern const I2CDeviceConfig I2C_DEV_PCA9685_INTERNAL;

/// BMI270 IMU on internal I2C (GPIO 8/9) at 0x68
extern const I2CDeviceConfig I2C_DEV_BMI270;

/// FT6336U Touch on internal I2C (GPIO 8/9) at 0x38
extern const I2CDeviceConfig I2C_DEV_FT6336U;

// ============================================================================
// Error Handling API
// ============================================================================

/**
 * @brief Initialize the error handling and watchdog subsystem.
 *
 * Must be called once at boot, before any peripheral initialization.
 * Performs the following:
 *   1. Checks RTC memory for crash record from previous boot
 *   2. Configures MWDT (main watchdog timer) with the specified timeout
 *   3. Configures TWDT (task watchdog timer)
 *   4. Sets up auto-feed timer (if enabled)
 *   5. If crash_count >= EH_MAX_CRASHES_BEFORE_SAFE, enters safe mode
 *   6. Logs boot status (normal boot vs. crash recovery vs. safe mode)
 *
 * @param config Pointer to watchdog configuration (nullptr = use defaults).
 *               Defaults: hw_timeout=3000ms, task_timeout=3000ms,
 *                         auto_feed=true, feed_interval=1000ms.
 * @return ErrorCode::OK on success, or an appropriate hardware error code.
 */
ErrorCode errorHandlingInit(const WatchdogConfig* config = nullptr);

/**
 * @brief Report an error to the error handling subsystem.
 *
 * This is the central error reporting function. It:
 *   1. Logs the error with severity, timestamp, and context
 *   2. Determines the appropriate recovery action
 *   3. If severity >= CRITICAL, adjusts degradation level
 *   4. Calls all registered error callbacks (for UI/display/alert)
 *   5. If severity == FATAL, triggers system reset with crash record
 *   6. Returns a recovery hint / suggested action code
 *
 * @param code      The error code.
 * @param severity  Severity level.
 * @param context   Optional human-readable context string (nullptr allowed).
 * @return DegradationLevel indicating the current system state after handling.
 */
DegradationLevel reportError(ErrorCode code, ErrorSeverity severity,
                             const char* context = nullptr);

/**
 * @brief Report an error with additional formatting (printf-style).
 *
 * Wrapper around reportError that formats a context string via vsnprintf.
 * The formatted string is truncated to EH_CONTEXT_STR_LEN - 1 characters.
 *
 * @param code      The error code.
 * @param severity  Severity level.
 * @param fmt       printf-style format string.
 * @param ...       Variadic arguments for the format string.
 * @return DegradationLevel.
 */
DegradationLevel reportErrorF(ErrorCode code, ErrorSeverity severity,
                              const char* fmt, ...) __attribute__((format(printf, 3, 4)));

/**
 * @brief Register an error callback.
 *
 * Callbacks are invoked synchronously from reportError(). They must be
 * non-blocking and must not re-enter the error handling system.
 *
 * @param callback  Function pointer to register.
 * @return ErrorCode::OK on success, ErrorCode::RT_INVALID_PARAMETER if
 *         callback is null, or ErrorCode::RT_QUEUE_FULL if max callbacks
 *         already registered.
 */
ErrorCode registerErrorCallback(ErrorCallback callback);

/**
 * @brief Unregister a previously registered error callback.
 *
 * @param callback  Function pointer to unregister.
 * @return ErrorCode::OK on success, ErrorCode::RT_NULL_POINTER if not found.
 */
ErrorCode unregisterErrorCallback(ErrorCallback callback);

/**
 * @brief Get the current system degradation level.
 * @return Current DegradationLevel.
 */
DegradationLevel getDegradationLevel();

/**
 * @brief Check if the system is in safe mode.
 * @return true if in safe mode, false otherwise.
 */
bool isInSafeMode();

/**
 * @brief Recover a failed I2C device by re-initializing it.
 *
 * Performs a full re-initialization sequence for the given device:
 *   1. Attempts to re-detect the device on the I2C bus
 *   2. Re-sends the initialization sequence
 *   3. If successful, resets consecutive_failures to 0 and is_failed to false
 *
 * @param dev   Pointer to the I2C device configuration.
 * @return ErrorCode::OK on successful recovery, or the error that occurred.
 */
ErrorCode recoverI2CDevice(I2CDeviceConfig* dev);

/**
 * @brief Manually feed (reset) the watchdog timer.
 *
 * Called periodically by the main loop to indicate the system is alive.
 * If auto_feed is enabled (default), this is handled automatically.
 * Disable auto_feed for fine-grained control in time-critical sections.
 */
void feedWatchdog();

/**
 * @brief Extend the watchdog timeout for long-running operations.
 *
 * Used during firmware updates, calibration, or lengthy I2C scans.
 * Must be followed by restoreWatchdogTimeout() to return to normal.
 *
 * @param timeout_ms  New timeout in milliseconds.
 * @return ErrorCode::OK on success.
 */
ErrorCode extendWatchdogTimeout(uint32_t timeout_ms);

/**
 * @brief Restore the watchdog timeout to the normal configured value.
 */
void restoreWatchdogTimeout();

/**
 * @brief Reset the system and record a crash entry in RTC memory.
 *
 * Called automatically on FATAL errors. Can also be called manually.
 * The function writes the crash record, flushes caches, then triggers
 * a CPU reset via esp_restart().
 *
 * @param code      The fatal error code.
 * @param severity  Severity (should be FATAL).
 * @param context   Context string.
 * @note This function does not return.
 */
[[noreturn]] void fatalReset(ErrorCode code, ErrorSeverity severity,
                             const char* context);

/**
 * @brief Retrieve the crash record from the previous boot.
 *
 * Call at startup to check if the previous boot ended in a crash.
 * The record is valid only if isValid() returns true.
 *
 * @return Pointer to the CrashRecord, or nullptr if no valid record exists.
 */
const CrashRecord* getLastCrashRecord();

/**
 * @brief Clear the crash record and reset the crash counter.
 *
 * Called after a successful recovery or on intentional clean boot.
 * Resets crash_count to 0 and invalidates the RTC record.
 */
void clearCrashRecord();

// ============================================================================
// I2C Communication Helpers (with timeout and retry)
// ============================================================================

/**
 * @brief Perform an I2C write with timeout and automatic retry.
 *
 * Attempts a write to the specified device. On failure, retries with
 * exponential backoff up to max_retries times. Updates consecutive_failures
 * and is_failed on the device config.
 *
 * @param dev       Pointer to the I2C device configuration.
 * @param reg       Register address to write to.
 * @param data      Pointer to data buffer.
 * @param len       Length of data in bytes.
 * @return ErrorCode::OK on success, or COMM_I2C_TIMEOUT / COMM_I2C_RETRY_EXCEEDED.
 */
ErrorCode i2cWriteWithRetry(I2CDeviceConfig* dev, uint8_t reg,
                            const uint8_t* data, size_t len);

/**
 * @brief Perform an I2C read with timeout and automatic retry.
 *
 * Same retry logic as i2cWriteWithRetry, for read operations.
 *
 * @param dev       Pointer to the I2C device configuration.
 * @param reg       Register address to read from.
 * @param data      Pointer to receive buffer.
 * @param len       Number of bytes to read.
 * @return ErrorCode::OK on success, or COMM_I2C_TIMEOUT / COMM_I2C_RETRY_EXCEEDED.
 */
ErrorCode i2cReadWithRetry(I2CDeviceConfig* dev, uint8_t reg,
                           uint8_t* data, size_t len);

/**
 * @brief Perform a full I2C bus reset (clear bus, re-init controller).
 *
 * Used when the I2C bus is in a stuck state (SCL/SDA held low).
 * Toggles SCL up to 9 times to release stuck slaves, then re-initializes
 * the I2C controller. Updates degradation level on failure.
 *
 * @return ErrorCode::OK on success.
 */
ErrorCode i2cBusReset();

// ============================================================================
// Graceful Degradation API
// ============================================================================

/**
 * @brief Transition the system to a new degradation level.
 *
 * When transitioning to a higher (worse) level, the function:
 *   1. Disables the failing subsystem(s)
 *   2. Adjusts update rates / power modes
 *   3. Updates the TFT status bar (if display is still functional)
 *   4. Logs the degradation event
 *
 * When transitioning to a lower (better) level (recovery):
 *   1. Re-initializes the previously failed subsystem(s)
 *   2. Validates they are operational
 *   3. Restores normal operation
 *
 * @param level     Target degradation level.
 * @return ErrorCode::OK on success.
 */
ErrorCode setDegradationLevel(DegradationLevel level);

/**
 * @brief Initialize the safe mode fallback configuration.
 *
 * Safe mode:
 *   - Disables all servos (PCA9685 outputs disabled)
 *   - Disables RGB LED
 *   - Reduces TFT brightness to minimum
 *   - Stops non-critical sensor polling (microphone, IMU gesture detection)
 *   - Keeps touch input active for user interaction
 *   - Displays "SAFE MODE" on screen
 *   - Feeds WDT but at reduced interval
 *   - Waits for user reset or recovery command
 *
 * @return ErrorCode::OK on success.
 */
ErrorCode enterSafeMode();

/**
 * @brief Exit safe mode and attempt full recovery.
 *
 * Re-initializes all peripherals in order:
 *   1. I2C buses (Grove + internal)
 *   2. PCA9685 servo driver
 *   3. Servos (move to neutral position)
 *   4. BMI270 IMU
 *   5. FT6336U touch
 *   6. SPM1423 microphone
 *   7. ILI9342C display
 *   8. RGB LED
 *   9. Clear crash record
 *
 * @return ErrorCode::OK on success, or first error encountered (partial recovery).
 */
ErrorCode exitSafeMode();

// ============================================================================
// Diagnostics / Status Reporting
// ============================================================================

/**
 * @brief Get a human-readable string for an error code.
 *
 * @param code  The error code.
 * @return Pointer to a static string (do not free).
 */
const char* errorCodeToString(ErrorCode code);

/**
 * @brief Get a human-readable string for a severity level.
 *
 * @param severity  The severity level.
 * @return Pointer to a static string.
 */
const char* severityToString(ErrorSeverity severity);

/**
 * @brief Get a human-readable string for a degradation level.
 *
 * @param level  The degradation level.
 * @return Pointer to a static string.
 */
const char* degradationToString(DegradationLevel level);

/**
 * @brief Print the current system status to the serial console.
 *
 * Outputs:
 *   - Current degradation level
 *   - Safe mode status
 *   - Last error code and context
 *   - I2C device failure status for all devices
 *   - WDT configuration and remaining time
 *   - Free heap and minimum free heap
 *   - Uptime in milliseconds
 */
void printSystemStatus();

/**
 * @brief Dump the last N error events to the serial console for debugging.
 *
 * @param max_events  Maximum number of events to dump (0 = all stored).
 */
void dumpErrorLog(size_t max_events = 20);

#endif // M5STACK_ERROR_HANDLING_H
