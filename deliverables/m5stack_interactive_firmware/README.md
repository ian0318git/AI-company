# M5Stack Interactive Firmware

Three interactive applications for M5Stack CoreS3 and StackChan, demonstrating inter-device communication over UART with sensor fusion, real-time visualization, and a cooperative game.

## Hardware

| Device | MCU | Display | Sensors | Connectivity |
|--------|-----|---------|---------|--------------|
| **CoreS3** (Controller) | ESP32-S3 | ILI9342C 320×240 TFT | BMI270 IMU, BMM150 Mag, PDM Mic, Touch | UART TX=13/RX=14 |
| **StackChan** (Receiver) | ESP32-S3 | SSD1306 128×64 OLED | — | UART RX=3/TX=1, Servos (13/14) |

## Applications

### 1. Motion Controller
CoreS3 reads BMI270 at 100Hz → Madgwick filter → maps roll/pitch to StackChan servo angles → sent via UART frame `0x01`

### 2. Sensor Data Visualizer
CoreS3 streams IMU data → StackChan renders real-time waveform/gauge on OLED via UART frame `0x02`

### 3. Interactive Game
CoreS3 as tilt-based game controller → StackChan renders pong-style game via UART frame `0x03` (latency <50ms target)

## Protocol

Binary frame format: `[0xAA] [len] [cmd] [payload...] [xor_checksum]`

| Cmd | Direction | Purpose |
|-----|-----------|---------|
| 0x01 | CoreS3→StackChan | Motion: roll(2B) + pitch(2B) + buttons(1B) |
| 0x02 | CoreS3→StackChan | Sensor: type(1B) + value(4B) |
| 0x03 | Bidirectional | Game: state(1B) + buttons(1B) |
| 0x10 | StackChan→CoreS3 | Heartbeat: status(1B) + battery(1B) |
| 0xFF | Either | Keepalive ping |

## Architecture

### CoreS3 (FreeRTOS, 4 tasks)
| Task | Core | Stack | Pri | Rate |
|------|------|-------|-----|------|
| Sensor | 1 | 2048 | 2 | 100Hz |
| UI | 1 | 4096 | 1 | 30 FPS |
| App Logic | 1 | 4096 | 2 | 50Hz |
| UART Comm | 0 | 2048 | 3 | 50Hz |

### Error Handling
- UART timeout: 500ms → 3 retries → standalone fallback
- IMU init failure: 3 retries × 100ms → error code on screen
- Frame CRC error: drop + request retransmit
- Task watchdog: 1s SW watchdog → panic reset on hang

## Building

```bash
# CoreS3 firmware
pio run -e m5stack-core-s3

# StackChan firmware
pio run -e m5stack-stackchan

# Flash CoreS3
pio run -e m5stack-core-s3 -t upload

# Monitor
pio device monitor --baud 115200
```

## Deliverables

| File | Description |
|------|-------------|
| `src/main.cpp` | CoreS3 main firmware with FreeRTOS tasks |
| `src/stackchan/main.cpp` | StackChan receiver firmware |
| `src/hal/UartComm.h/cpp` | UART framed protocol implementation |
| `src/hal/ImuSensor.h/cpp` | BMI270 driver with Madgwick filter |
| `src/hal/ButtonInput.h/cpp` | Debounced button driver |
| `src/hal/DisplayCoreS3.h` | M5GFX CoreS3 display driver |
| `src/hal/DisplaySSD1306.h` | M5GFX SSD1306 display driver |
| `src/hal/ServoController.h/cpp` | PWM servo driver |
| `src/hal/IAudio.h` | Audio input/output abstractions |
| `src/ErrorHandler.h/cpp` | Watchdog + error recovery |
| `test/test_uart_comm.cpp` | Unit tests for UART protocol |
| `test/test_madgwick.cpp` | Unit tests for Madgwick filter |
