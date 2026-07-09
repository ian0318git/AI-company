/**
 * @file main.cpp
 * @brief M5Stack CoreS3 — Interactive Controller Firmware
 *
 * Three applications: Motion Controller, Sensor Visualizer, Interactive Game
 * Uses FreeRTOS multi-tasking on ESP32-S3 dual-core.
 *
 * Core 0: UART Communication
 * Core 1: Sensor reading, UI rendering, App state machine
 */

#include <M5Unified.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>

#include "hal/UartComm.h"
#include "hal/ImuSensor.h"
#include "hal/ButtonInput.h"
#include "hal/DisplayCoreS3.h"

// ============================================================
// Constants
// ============================================================
static constexpr uint32_t SENSOR_INTERVAL_MS = 10;    // 100Hz
static constexpr uint32_t UI_INTERVAL_MS     = 33;    // ~30 FPS
static constexpr uint32_t UART_POLL_MS       = 20;    // 50Hz

// UART pins: TX=GPIO13, RX=GPIO14
static constexpr int UART_TX_PIN = 13;
static constexpr int UART_RX_PIN = 14;

// ============================================================
// Global objects
// ============================================================
UartComm    g_uart(2, UART_TX_PIN, UART_RX_PIN);
ImuSensor   g_imu;
ButtonInput g_buttons;
DisplayCoreS3 g_display;

// Queue for inter-task communication
QueueHandle_t g_sensorQueue;
QueueHandle_t g_uartTxQueue;
QueueHandle_t g_eventQueue;

// App state
enum AppMode : uint8_t {
    MODE_IDLE      = 0,
    MODE_MOTION    = 1,
    MODE_VISUAL    = 2,
    MODE_GAME      = 3,
    MODE_SLEEP     = 4,
};

static volatile AppMode g_appMode = MODE_IDLE;
static volatile uint32_t g_lastActivityMs = 0;
static constexpr uint32_t SLEEP_TIMEOUT_MS = 300000;  // 5 min inactivity

// ============================================================
// Sensor data structure (sent via queue)
// ============================================================
struct SensorPacket {
    float roll, pitch, yaw;
    float ax, ay, az;
    float micLevel;
    uint8_t buttons;
    uint32_t timestamp;
};

struct UartTxPacket {
    uint8_t cmd;
    uint8_t payload[16];
    uint8_t len;
};

// ============================================================
// Task: Sensor Reader (Core 1, 100Hz)
// ============================================================
void sensorTask(void* param) {
    TickType_t lastWake = xTaskGetTickCount();
    IImuSensor::ImuData imuData;

    while (true) {
        if (g_imu.read(imuData)) {
            SensorPacket pkt;
            pkt.roll     = imuData.roll;
            pkt.pitch    = imuData.pitch;
            pkt.yaw      = imuData.yaw;
            pkt.ax       = imuData.ax;
            pkt.ay       = imuData.ay;
            pkt.az       = imuData.az;
            pkt.buttons  = g_buttons.getPressedMask();
            pkt.micLevel = 0.0f;  // Audio input TBD
            pkt.timestamp = millis();

            xQueueOverwrite(g_sensorQueue, &pkt);
        }

        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(SENSOR_INTERVAL_MS));
    }
}

// ============================================================
// Task: UI Renderer (Core 1, 30 FPS)
// ============================================================
void uiTask(void* param) {
    TickType_t lastWake = xTaskGetTickCount();
    SensorPacket sensor;
    char buf[64];

    while (true) {
        AppMode mode = g_appMode;

        g_display.clear();

        switch (mode) {
            case MODE_IDLE:
                g_display.drawText(10, 60, "M5Stack Interactive", TFT_WHITE);
                g_display.drawText(10, 90, "Select mode:", TFT_GRAY);
                g_display.drawText(10, 120, "A: Motion Controller", TFT_CYAN);
                g_display.drawText(10, 140, "B: Sensor Visualizer", TFT_GREEN);
                g_display.drawText(10, 160, "C: Game Controller", TFT_YELLOW);
                break;

            case MODE_MOTION:
                if (xQueuePeek(g_sensorQueue, &sensor, 0) == pdTRUE) {
                    snprintf(buf, sizeof(buf), "Roll:  %+6.1f", sensor.roll);
                    g_display.drawText(10, 40, buf, TFT_WHITE);
                    snprintf(buf, sizeof(buf), "Pitch: %+6.1f", sensor.pitch);
                    g_display.drawText(10, 65, buf, TFT_WHITE);
                    snprintf(buf, sizeof(buf), "Yaw:   %+6.1f", sensor.yaw);
                    g_display.drawText(10, 90, buf, TFT_WHITE);

                    // 3D orientation indicator
                    drawOrientationIndicator(g_display, sensor.roll, sensor.pitch);
                }
                g_display.drawText(10, 200, "Motion Controller", TFT_CYAN);
                break;

            case MODE_VISUAL: {
                const char* label = "Sensor Visualizer";
                g_display.drawText(10, 200, label, TFT_GREEN);

                if (xQueuePeek(g_sensorQueue, &sensor, 0) == pdTRUE) {
                    // Draw waveform-like bar for each axis
                    int cx = g_display.width() / 2;
                    int cy = g_display.height() / 2 - 20;

                    // X axis bar (red)
                    int hx = static_cast<int>(sensor.ax * 30);
                    g_display.fillRect(cx - 80, cy - 30 + (30 - hx), 40, abs(hx) + 1, TFT_RED);
                    // Y axis bar (green)
                    int hy = static_cast<int>(sensor.ay * 30);
                    g_display.fillRect(cx - 20, cy - 30 + (30 - hy), 40, abs(hy) + 1, TFT_GREEN);
                    // Z axis bar (blue)
                    int hz = static_cast<int>(sensor.az * 30);
                    g_display.fillRect(cx + 40, cy - 30 + (30 - hz), 40, abs(hz) + 1, TFT_BLUE);
                }
                break;
            }

            case MODE_GAME: {
                g_display.drawText(10, 200, "Game Controller", TFT_YELLOW);

                if (xQueuePeek(g_sensorQueue, &sensor, 0) == pdTRUE) {
                    // Draw tilt indicator
                    int bx = g_display.width() / 2 + static_cast<int>(sensor.roll * 2);
                    int by = g_display.height() / 2 + static_cast<int>(sensor.pitch * 2);
                    bx = constrain(bx, 10, g_display.width() - 10);
                    by = constrain(by, 10, g_display.height() - 10);
                    g_display.fillCircle(bx, by, 12, TFT_YELLOW);
                    g_display.drawCircle(bx, by, 14, TFT_WHITE);
                }
                break;
            }

            case MODE_SLEEP:
                g_display.drawText(60, 110, "Sleeping...", TFT_GRAY);
                break;
        }

        g_display.update();
        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(UI_INTERVAL_MS));
    }
}

// ============================================================
// Task: App Logic / State Machine (Core 1)
// ============================================================
void appLogicTask(void* param) {
    uint32_t now;
    SensorPacket sensor;

    while (true) {
        now = millis();
        g_lastActivityMs = now;  // Will be updated on button press

        // Check for mode switch via button events
        if (g_buttons.wasPressed(IButtonInput::BTN_A)) {
            g_appMode = MODE_MOTION;
            g_lastActivityMs = now;
        }
        if (g_buttons.wasPressed(IButtonInput::BTN_B)) {
            g_appMode = MODE_VISUAL;
            g_lastActivityMs = now;
        }
        if (g_buttons.wasPressed(IButtonInput::BTN_C)) {
            if (g_appMode == MODE_GAME) {
                g_appMode = MODE_IDLE;  // Toggle back to menu
            } else {
                g_appMode = MODE_GAME;
            }
            g_lastActivityMs = now;
        }

        // Long press C from any mode → idle
        if (g_buttons.wasHeld(IButtonInput::BTN_C, 2000)) {
            g_appMode = MODE_IDLE;
            g_lastActivityMs = now;
        }

        // Sleep timeout
        if (g_appMode != MODE_IDLE && g_appMode != MODE_SLEEP) {
            if (now - g_lastActivityMs > SLEEP_TIMEOUT_MS) {
                g_appMode = MODE_SLEEP;
            }
        }

        // Motion mode: send orientation over UART
        if (g_appMode == MODE_MOTION && xQueuePeek(g_sensorQueue, &sensor, 0) == pdTRUE) {
            int16_t roll_i  = static_cast<int16_t>(sensor.roll * 100);
            int16_t pitch_i = static_cast<int16_t>(sensor.pitch * 100);
            uint8_t payload[6];
            payload[0] = static_cast<uint8_t>(roll_i >> 8);
            payload[1] = static_cast<uint8_t>(roll_i & 0xFF);
            payload[2] = static_cast<uint8_t>(pitch_i >> 8);
            payload[3] = static_cast<uint8_t>(pitch_i & 0xFF);
            payload[4] = sensor.buttons;
            payload[5] = 0;  // reserved
            g_uart.sendFrame(IUartComm::CMD_MOTION_CTRL, payload, 6);
        }

        // Visualizer mode: send sensor data
        if (g_appMode == MODE_VISUAL && xQueuePeek(g_sensorQueue, &sensor, 0) == pdTRUE) {
            uint8_t payload[5];
            payload[0] = 0x01;  // sensor type: accelerometer
            int16_t ax_i = static_cast<int16_t>(sensor.ax * 1000);
            int16_t ay_i = static_cast<int16_t>(sensor.ay * 1000);
            payload[1] = static_cast<uint8_t>(ax_i >> 8);
            payload[2] = static_cast<uint8_t>(ax_i & 0xFF);
            payload[3] = static_cast<uint8_t>(ay_i >> 8);
            payload[4] = static_cast<uint8_t>(ay_i & 0xFF);
            g_uart.sendFrame(IUartComm::CMD_SENSOR_DATA, payload, 5);
        }

        vTaskDelay(pdMS_TO_TICKS(20));  // 50Hz state machine
    }
}

// ============================================================
// Task: UART Communication (Core 0)
// ============================================================
void uartTask(void* param) {
    uint8_t rxBuf[IUartComm::MAX_PAYLOAD];

    while (true) {
        // Send keepalive every 2 seconds
        static uint32_t lastKeepalive = 0;
        uint32_t now = millis();
        if (now - lastKeepalive > 2000) {
            g_uart.sendFrame(IUartComm::CMD_KEEPALIVE, nullptr, 0);
            lastKeepalive = now;
        }

        // Check for incoming frames
        int len = g_uart.receiveFrame(rxBuf, sizeof(rxBuf), IUartComm::DEFAULT_TIMEOUT);
        if (len > 0) {
            uint8_t cmd = g_uart.lastCmd();
            if (cmd == IUartComm::CMD_HEARTBEAT && len >= 1) {
                // StackChan battery status received
                // Could update display or trigger low-battery warning
            }
        }

        vTaskDelay(pdMS_TO_TICKS(UART_POLL_MS));
    }
}

// ============================================================
// Helper: Draw 3D orientation indicator
// ============================================================
static void drawOrientationIndicator(DisplayCoreS3& disp, float roll, float pitch) {
    int cx = disp.width() / 2;
    int cy = 140;
    int r = 40;

    // Horizon line
    float dx = sinf(pitch * DEG_TO_RAD) * r;
    float dy = sinf(roll * DEG_TO_RAD) * r;
    disp.drawLine(cx - r + static_cast<int>(dx), cy + static_cast<int>(dy),
                  cx + r + static_cast<int>(dx), cy - static_cast<int>(dy), TFT_WHITE);

    // Aircraft symbol
    disp.drawCircle(cx, cy, 6, TFT_GREEN);
    disp.drawLine(cx - 12, cy, cx + 12, cy, TFT_GREEN);
    disp.drawLine(cx, cy - 8, cx, cy + 8, TFT_GREEN);
}

// ============================================================
// Setup
// ============================================================
void setup() {
    // Initialize M5
    auto cfg = M5.unifiedConfig();
    cfg.external_rtc  = false;
    cfg.internal_imu  = false;  // We handle IMU directly
    M5.begin(cfg);

    // Initialize peripherals
    g_buttons.begin();
    g_display.begin();
    g_uart.begin(115200);

    // Initialize IMU on Wire1
    if (!g_imu.begin(Wire1)) {
        g_display.clear(TFT_RED);
        g_display.drawText(10, 100, "IMU Init Failed!", TFT_WHITE);
        g_display.update();
    }

    // Create queues
    g_sensorQueue = xQueueCreate(1, sizeof(SensorPacket));
    g_eventQueue  = xQueueCreate(10, sizeof(uint8_t));

    // Create FreeRTOS tasks
    xTaskCreatePinnedToCore(sensorTask,  "sensor",   2048, nullptr, 2, nullptr, 1);
    xTaskCreatePinnedToCore(uiTask,      "ui",       4096, nullptr, 1, nullptr, 1);
    xTaskCreatePinnedToCore(appLogicTask,"app_logic",4096, nullptr, 2, nullptr, 1);
    xTaskCreatePinnedToCore(uartTask,    "uart",     2048, nullptr, 3, nullptr, 0);

    // Initial screen
    g_appMode = MODE_IDLE;
}

void loop() {
    // FreeRTOS takes over — idle here
    vTaskDelay(pdMS_TO_TICKS(1000));
}
