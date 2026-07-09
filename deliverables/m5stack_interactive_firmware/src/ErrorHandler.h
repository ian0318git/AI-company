#pragma once

#include <cstdint>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

/**
 * @brief System-wide error handler with watchdog, retry, and logging
 *
 * Features:
 * - Software watchdog per FreeRTOS task (1s timeout)
 * - Configurable retry with exponential backoff
 * - Error code display on screen
 * - Crash recovery via panic reset
 */
class ErrorHandler {
public:
    enum ErrorCode : uint8_t {
        ERR_NONE          = 0x00,
        ERR_IMU_INIT      = 0x10,
        ERR_IMU_READ      = 0x11,
        ERR_UART_TIMEOUT  = 0x20,
        ERR_UART_CRC      = 0x21,
        ERR_SERVO_INIT    = 0x30,
        ERR_DISPLAY_INIT  = 0x40,
        ERR_TASK_HANG     = 0x50,
        ERR_LOW_BATTERY   = 0x60,
        ERR_UNKNOWN       = 0xFF,
    };

    struct RetryConfig {
        uint8_t maxRetries;
        uint32_t baseDelayMs;
        uint32_t maxDelayMs;
    };

    static constexpr RetryConfig DEFAULT_RETRY = {3, 100, 1000};

    /** @brief Report an error and attempt recovery */
    static bool report(ErrorCode code, const char* component, const RetryConfig& retry = DEFAULT_RETRY);

    /** @brief Feed the software watchdog for a task */
    static void feedWatchdog();

    /** @brief Get the last error code */
    static ErrorCode lastError() { return s_lastError; }

    /** @brief Get error count for a specific code */
    static uint32_t errorCount(ErrorCode code);

    /** @brief Reset all error counters */
    static void resetCounters();

    /** @brief Display error code on screen (blocking, 5s) */
    static void displayError(ErrorCode code, const char* msg);

private:
    static ErrorCode s_lastError;
    static uint32_t  s_errorCounts[256];
    static uint32_t  s_lastFeedMs;

    static bool retryWithBackoff(bool (*operation)(), const RetryConfig& config);
};
