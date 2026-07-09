#include "ErrorHandler.h"
#include <M5Unified.h>
#include <cstdio>

ErrorCode ErrorHandler::s_lastError = ERR_NONE;
uint32_t  ErrorHandler::s_errorCounts[256] = {0};
uint32_t  ErrorHandler::s_lastFeedMs = 0;

bool ErrorHandler::report(ErrorCode code, const char* component, const RetryConfig& retry) {
    s_lastError = code;
    s_errorCounts[static_cast<uint8_t>(code)]++;

    // Log to serial
    Serial.printf("[ERROR] 0x%02X: %s (count: %u)\n",
                  static_cast<uint8_t>(code),
                  component ? component : "unknown",
                  s_errorCounts[static_cast<uint8_t>(code)]);

    // Display on screen
    displayError(code, component);

    // Panic on critical errors
    switch (code) {
        case ERR_TASK_HANG:
        case ERR_IMU_INIT:
            Serial.println("[FATAL] System reset in 1s...");
            delay(1000);
            ESP.restart();
            return false;

        default:
            return true;  // Non-critical, continue
    }
}

void ErrorHandler::feedWatchdog() {
    s_lastFeedMs = millis();
}

ErrorCode ErrorHandler::lastError() {
    return s_lastError;
}

uint32_t ErrorHandler::errorCount(ErrorCode code) {
    return s_errorCounts[static_cast<uint8_t>(code)];
}

void ErrorHandler::resetCounters() {
    for (int i = 0; i < 256; i++) {
        s_errorCounts[i] = 0;
    }
    s_lastError = ERR_NONE;
}

void ErrorHandler::displayError(ErrorCode code, const char* msg) {
    // Save current display state (minimal implementation)
    M5.Lcd.fillRect(0, 0, 320, 30, TFT_RED);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_RED);

    char buf[64];
    snprintf(buf, sizeof(buf), "ERR 0x%02X", static_cast<uint8_t>(code));
    M5.Lcd.drawString(buf, 5, 5, 1);

    if (msg) {
        M5.Lcd.drawString(msg, 5, 18, 1);
    }
}

bool ErrorHandler::retryWithBackoff(bool (*operation)(), const RetryConfig& config) {
    uint32_t delay = config.baseDelayMs;

    for (int i = 0; i < config.maxRetries; i++) {
        if (operation()) return true;
        delay = (delay * 2 < config.maxDelayMs) ? delay * 2 : config.maxDelayMs;
        vTaskDelay(pdMS_TO_TICKS(delay));
    }

    return false;
}
