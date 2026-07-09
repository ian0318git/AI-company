/**
 * @file main.cpp (StackChan)
 * @brief M5Stack StackChan — Interactive Receiver Firmware
 *
 * Receives UART commands from CoreS3 and renders the corresponding
 * output on the SSD1306 OLED display and servo motors.
 */

#include <M5Unified.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#include "hal/UartComm.h"
#include "hal/DisplaySSD1306.h"
#include "hal/ServoController.h"

// ============================================================
// Constants
// ============================================================
static constexpr uint32_t DISPLAY_INTERVAL_MS = 50;   // 20 FPS
static constexpr uint32_t HEARTBEAT_INTERVAL_MS = 5000;

// UART pins: RX=GPIO3, TX=GPIO1 (StackChan default Serial1)
static constexpr int UART_RX_PIN = 3;
static constexpr int UART_TX_PIN = 1;

// Servo pins
static constexpr int SERVO_BODY_PIN = 13;
static constexpr int SERVO_HEAD_PIN = 14;

// ============================================================
// Global objects
// ============================================================
UartComm       g_uart(1, UART_TX_PIN, UART_RX_PIN);
DisplaySSD1306 g_display;
ServoController g_servo;

// Application display mode (set by UART cmd)
static uint8_t g_displayMode = 0;  // 0=idle, 1=motion, 2=sensor, 3=game

// Latest received data
static volatile struct {
    int16_t roll, pitch;          // Motion control (0.01°)
    int16_t ax, ay;               // Sensor data (0.001g)
    uint8_t buttons;              // Button mask
    uint8_t gameState;            // Game state
    uint8_t batteryPercent;       // Battery level
    uint32_t lastHeartbeatMs;     // Last keepalive timestamp
} g_state = {0};

// ============================================================
// Task: UART Receiver (Core 0)
// ============================================================
void uartRxTask(void* param) {
    uint8_t rxBuf[IUartComm::MAX_PAYLOAD];

    while (true) {
        int len = g_uart.receiveFrame(rxBuf, sizeof(rxBuf), 100);
        if (len <= 0) {
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }

        uint8_t cmd = g_uart.lastCmd();

        switch (cmd) {
            case IUartComm::CMD_MOTION_CTRL:
                if (len >= 6) {
                    g_state.roll  = static_cast<int16_t>(rxBuf[0] << 8 | rxBuf[1]);
                    g_state.pitch = static_cast<int16_t>(rxBuf[2] << 8 | rxBuf[3]);
                    g_state.buttons = rxBuf[4];
                    g_displayMode = 1;

                    // Map roll/pitch to servo angles
                    IServoController::ServoAngles angles;
                    angles.body = static_cast<uint8_t>(
                        constrain(map(g_state.roll, -9000, 9000, 0, 180), 0, 180));
                    angles.head = static_cast<uint8_t>(
                        constrain(map(g_state.pitch, -9000, 9000, 0, 180), 0, 180));
                    g_servo.setAngles(angles);
                }
                break;

            case IUartComm::CMD_SENSOR_DATA:
                if (len >= 5) {
                    g_state.ax = static_cast<int16_t>(rxBuf[1] << 8 | rxBuf[2]);
                    g_state.ay = static_cast<int16_t>(rxBuf[3] << 8 | rxBuf[4]);
                    g_displayMode = 2;
                }
                break;

            case IUartComm::CMD_GAME_CTRL:
                if (len >= 2) {
                    g_state.gameState = rxBuf[1];
                    g_state.buttons = rxBuf[0];
                    g_displayMode = 3;
                }
                break;

            case IUartComm::CMD_KEEPALIVE:
                g_state.lastHeartbeatMs = millis();
                break;

            default:
                break;
        }

        vTaskDelay(pdMS_TO_TICKS(5));
    }
}

// ============================================================
// Task: Display Renderer
// ============================================================
void displayTask(void* param) {
    TickType_t lastWake = xTaskGetTickCount();
    char buf[32];

    while (true) {
        g_display.clear();

        switch (g_displayMode) {
            case 0:  // Idle/Welcome
                g_display.drawText(8, 10, "StackChan", TFT_WHITE);
                g_display.drawText(8, 30, "Ready", TFT_GREEN);
                g_display.drawText(8, 50, "Waiting for", TFT_GRAY);
                g_display.drawText(8, 65, "CoreS3...", TFT_GRAY);
                break;

            case 1: {  // Motion Controller
                int barW = map(constrain(g_state.roll, -9000, 9000),
                               -9000, 9000, 0, 120);
                g_display.fillRect(4, 20, barW, 8, TFT_CYAN);
                g_display.drawRect(4, 20, 120, 8, TFT_WHITE);

                int barH = map(constrain(g_state.pitch, -9000, 9000),
                               -9000, 9000, 0, 40);
                g_display.fillRect(55, 35, 10, 40 - barH, TFT_GREEN);

                snprintf(buf, sizeof(buf), "R:%+4d", g_state.roll / 100);
                g_display.drawText(4, 50, buf, TFT_WHITE);

                snprintf(buf, sizeof(buf), "P:%+4d", g_state.pitch / 100);
                g_display.drawText(4, 60, buf, TFT_WHITE);
                break;
            }

            case 2: {  // Sensor Visualizer
                int bx = map(constrain(g_state.ax, -4000, 4000),
                             -4000, 4000, 4, 124);
                int by = map(constrain(g_state.ay, -4000, 4000),
                             -4000, 4000, 60, 4);
                g_display.fillCircle(bx, by, 3, TFT_YELLOW);
                g_display.drawText(4, 10, "Sensor Viz", TFT_GREEN);
                break;
            }

            case 3: {  // Game
                // Simple pong-style display
                int paddleX = map(constrain(g_state.roll, -9000, 9000),
                                  -9000, 9000, 4, 100);
                g_display.fillRect(paddleX, 56, 20, 4, TFT_WHITE);
                g_display.drawText(4, 4, "GAME", TFT_YELLOW);

                // Ball (bounce based on game state)
                static int ballX = 64, ballY = 32;
                static int ballDx = 1, ballDy = 1;
                if (g_displayMode == 3) {
                    ballX += ballDx; ballY += ballDy;
                    if (ballX <= 0 || ballX >= 124) ballDx = -ballDx;
                    if (ballY <= 0 || ballY >= 56) ballDy = -ballDy;
                }
                g_display.fillCircle(ballX, ballY, 3, TFT_WHITE);
                break;
            }
        }

        g_display.update();
        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(DISPLAY_INTERVAL_MS));
    }
}

// ============================================================
// Setup
// ============================================================
void setup() {
    auto cfg = M5.unifiedConfig();
    cfg.internal_imu = false;
    M5.begin(cfg);

    g_uart.begin(115200);
    g_display.begin();
    g_servo.begin(SERVO_BODY_PIN, SERVO_HEAD_PIN);

    // Neutral position
    g_servo.setAngles({90, 90});

    xTaskCreatePinnedToCore(uartRxTask,  "uart_rx", 2048, nullptr, 3, nullptr, 0);
    xTaskCreatePinnedToCore(displayTask, "display", 2048, nullptr, 1, nullptr, 1);
}

void loop() {
    // Send heartbeat every 5 seconds
    static uint32_t lastHb = 0;
    if (millis() - lastHb > HEARTBEAT_INTERVAL_MS) {
        uint8_t payload[2] = {0x01, 85};  // status=OK, battery=85%
        g_uart.sendFrame(IUartComm::CMD_HEARTBEAT, payload, 2);
        lastHb = millis();
    }
    vTaskDelay(pdMS_TO_TICKS(1000));
}
