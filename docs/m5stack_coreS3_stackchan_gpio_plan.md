# M5Stack CoreS3 + StackChan GPIO Pin Assignment Plan

**Project:** M5Stack两个产品互动 — 3 Interactive Apps
**Date:** 2026-07-08
**Version:** 2.0

---

## 1. System Overview

Two devices collaborate to create three interactive experiences.

| Device | MCU | Role | Key Hardware |
|--------|-----|------|-------------|
| **M5Stack Core S3** | ESP32-S3 (240MHz, 8MB PSRAM, 16MB Flash) | Controller | BMI270 IMU, FT6336U Touch, ILI9342C TFT, SPM1423 PDM Mic, AW88298 I2S Audio |
| **StackChan** | ESP32-WROOM-32 (240MHz, 4MB Flash) | Robot Avatar | 2x SG90 servos (pan/tilt), speaker (DAC/I2S), WS2812 LED mouth |

### 1.1 Recommended Architecture: Wired (UART) + Optional BLE

This plan presents a **dual-communication** approach:

| Protocol | Use Case | Why |
|----------|----------|-----|
| **UART (primary)** | CoreS3 GPIO header UART ↔ StackChan base UART | Deterministic low-latency (<1ms), no pairing, zero-config, shared ground |
| **BLE 5.0 (optional secondary)** | Wireless mode for untethered operation | Range ~10m, no wiring, but ~5-15ms variable latency |

For the three interactive apps, UART is the **recommended default** because servo control demands predictable timing. BLE is a documented fallback for scenarios where tethering is impractical.

---

## 2. M5Stack Core S3 — Complete Pin Mapping

### 2.1 Internal Peripherals (Fixed Allocation)

These pins are consumed by onboard hardware and **cannot be reassigned** without breaking core functionality.

| GPIO | Signal | Direction | Connected To | Notes |
|------|--------|-----------|-------------|-------|
| 0 | BOOT_BTN | IN (PU) | Boot button | Strapping pin — LOW at reset enters flash mode |
| 3 | TOUCH_INT | IN (IRQ) | FT6336U touch controller | Interrupt line, active low |
| 4 | TFT_CS | OUT | ILI9342C display | SPI chip select |
| 5 | SD_CS | OUT | microSD card slot | SPI chip select |
| 6 | AUDIO_EN | OUT | AW88298 audio amplifier | Enable pin (HIGH = on) |
| 7 | BUZZER | OUT (PWM) | Passive piezo buzzer | Can be repurposed if buzzer unused |
| 8 | I2C_SDA | I/O | Shared internal I2C bus | Touch, IMU, RTC, PMIC all on this bus |
| 9 | I2C_SCL | I/O | Shared internal I2C bus | — |
| 10 | I2S_DOUT | OUT | AW88298 I2S data | Audio DAC output |
| 11 | TOUCH_RST | OUT | FT6336U reset | — |
| 12 | LCD_BL | OUT (PWM) | TFT backlight boost | PWM dimming supported |
| 13 | TFT_RST | OUT | ILI9342C reset | Display reset — do not reassign |
| 14 | MIC_DATA | IN (PDM) | SPM1423 PDM microphone | Digital PDM data stream |
| 15 | TFT_DC | OUT | ILI9342C data/command | — |
| 16 | I2S_LRCK | OUT | AW88298 I2S left/right clock | — |
| 17 | I2S_BCLK | OUT | AW88298 I2S bit clock | — |
| 18 | SPI_SCLK | OUT | Shared SPI clock | Display + SD card |
| 19 | SD_MISO | IN | microSD card MISO | **Conflicts with USB D-** |
| 20 | USB_DP | I/O | USB D+ | **Do not use as GPIO** |
| 21 | RGB_LED | OUT | SK6812 NeoPixel | Addressable RGB LED |
| 23 | SPI_MOSI | OUT | Shared SPI MOSI | Display + SD card |
| 43 | UART_TX | OUT | USB Serial converter | Debug serial output |
| 44 | UART_RX | IN | USB Serial converter | Debug serial input |
| 46 | STRAP | — | Strapping pin | **Do not use** — determines boot mode |
| 47 | MIC_CLK | OUT (PDM) | SPM1423 PDM microphone | PDM clock output |

### 2.2 I2C Bus Map (Internal Bus: GPIO 8/9)

The Core S3 has five devices on a single I2C bus (addresses confirmed):

| Device | I2C Address | Function | Bus Speed |
|--------|-------------|----------|-----------|
| FT6336U Touch | 0x38 | Capacitive touch panel | 100kHz |
| BMI270 IMU | 0x68 | 6-axis accelerometer + gyroscope | 400kHz |
| BMM150 Magnetometer | 0x10 | 3-axis magnetometer (sub-address of BMI270) | 400kHz |
| BM8563 RTC | 0x51 | Real-time clock | 100kHz |
| AXP2101 PMIC | 0x34 | Power management IC | 100kHz |

**Note:** All five devices share GPIO 8 (SDA) and GPIO 9 (SCL). Built-in 4.7k pull-up resistors are populated on the PCB. No external pull-ups needed.

### 2.3 SPI Bus Map

| Signal | GPIO | Display (ILI9342C) | SD Card | Notes |
|--------|------|--------------------|---------|-------|
| MOSI | 23 | DIN | MOSI | Shared |
| SCLK | 18 | CLK | CLK | Shared |
| MISO | 19 | — | MISO | SD only (display MISO is NC) |
| CS | 4 | CS | — | Display chip select |
| CS | 5 | — | CS | SD card chip select |
| DC | 15 | DC | — | Display only |
| RST | 13 | RST | — | Display only |

### 2.4 Available External Pins for StackChan Connection

The Core S3 exposes limited external connectivity. These are the viable options for wiring to StackChan:

| Connector | Pins Available | Best For |
|-----------|---------------|----------|
| **Grove Port (HY2.0-4P)** | GPIO 1 (SDA), GPIO 2 (SCL), 5V, GND | I2C peripherals or UART on GPIO 1/2 |
| **GPIO Header (bottom edge)** | G1=GPIO1, G2=GPIO2, G3=GPIO3, G4=GPIO4, G5=GPIO5, G6=GPIO6, G7=GPIO7, G8=GPIO8 | Custom wiring — note conflicts with internal peripherals |

#### Recommended External Pin Allocation (UART Mode)

| Core S3 Pin | Direction | StackChan Pin | Signal | Notes |
|-------------|-----------|---------------|--------|-------|
| **GPIO 1 (Grove SDA)** | TX -> | UART RX (GPIO 3) | CoreS3 TX → StackChan RX | UART transmit to StackChan |
| **GPIO 2 (Grove SCL)** | RX <- | UART TX (GPIO 1) | CoreS3 RX ← StackChan TX | UART receive from StackChan |
| **Grove 5V** | Power out | VIN (5V) | 5V power | Up to 500mA via AXP2101 |
| **Grove GND** | Ground | GND | Common ground | Mandatory for UART |

**Alternative (if Grove port is used for I2C):**

| Core S3 GPIO Header | Direction | StackChan | Signal |
|---------------------|-----------|-----------|--------|
| GPIO 3 | TX -> | UART RX (GPIO 3) | CoreS3 TX |
| GPIO 6 | RX <- | UART TX (GPIO 1) | CoreS3 RX |
| GPIO 7 (buzzer PWM) | OUT | Servo signal | Single servo control (if buzzer unused) |

#### BLE Mode (No Wired Pins Required)

In BLE mode, **no GPIO pins** are consumed for inter-device communication. All Core S3 GPIOs remain available for sensors or peripherals. This is the cleanest option electrically but introduces ~5-15ms latency.

---

## 3. Communication Protocol: UART (Primary) + BLE (Optional)

### 3.1 UART Protocol (Recommended Default)

| Parameter | Value |
|-----------|-------|
| Baud rate | 115200 (or 921600 for high-speed) |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |
| Buffer size | 256 bytes (CoreS3), 128 bytes (StackChan) |

#### Packet Format

Each command is a fixed-length 8-byte packet:

```
Byte 0:     START byte (0xAA)
Byte 1:     Command ID
Byte 2-4:   Payload (3 bytes, command-specific)
Byte 5:     Flags/mode
Byte 6:     Checksum (XOR of bytes 0-5)
Byte 7:     END byte (0x55)
```

#### Command IDs

| ID | Command | Payload (3 bytes) | Direction |
|----|---------|-------------------|-----------|
| 0x01 | Servo Position | [servo_id, angle (0-180), speed (0-255)] | CoreS3 → StackChan |
| 0x02 | Servo Both | [pan_angle, tilt_angle, speed] | CoreS3 → StackChan |
| 0x03 | Play Sound | [sample_id (0-15), volume (0-100), loop (0/1)] | CoreS3 → StackChan |
| 0x04 | Expression | [expr_id (0-15), duration_x10ms, flags] | CoreS3 → StackChan |
| 0x05 | LED Mouth | [led_mask, r, g, b] | CoreS3 → StackChan |
| 0x06 | Status Request | [0, 0, 0] | CoreS3 → StackChan |
| 0x07 | Status Response | [battery_pct, mode, servo_state] | StackChan → CoreS3 |
| 0x08 | Heartbeat | [seq_num, 0, 0] | Bidirectional |
| 0xFF | Reset | [0, 0, 0] | CoreS3 → StackChan |

#### Expression IDs (for App 2)

| ID | Expression | Servo Pan | Servo Tilt | LED Color | Duration |
|----|------------|-----------|------------|-----------|----------|
| 0 | Neutral | 90 | 90 | White | Continuous |
| 1 | Happy | 90 | 70 | Yellow | 1.5s |
| 2 | Sad | 90 | 110 | Blue | 1.5s |
| 3 | Surprise | 90 | 60 | Red | 1.0s |
| 4 | Angry | 90 | 80 | Red (flash) | 1.5s |
| 5 | Blink | 90 | 90 → 140 → 90 | White | 300ms |
| 6 | Look Left | 50 | 90 | Cyan | Continuous |
| 7 | Look Right | 130 | 90 | Cyan | Continuous |
| 8 | Look Up | 90 | 60 | Magenta | Continuous |
| 9 | Look Down | 90 | 120 | Magenta | Continuous |
| 10 | Sleep | 90 | 90 | Dim blue (pulse) | Continuous |
| 11 | Wake | 90 | 90 | Bright white | 1.0s |

### 3.2 BLE Protocol (Optional Wireless Alternative)

| Parameter | Value |
|-----------|-------|
| Standard | Bluetooth 5.0 LE |
| CoreS3 Role | Central (client) |
| StackChan Role | Peripheral (server) |
| PHY | LE 1Mbps (default) |
| Connection Interval | 15ms (minimum for low-latency servo) |
| MTU Size | 128 bytes |

#### GATT Service

**Service UUID:** `AB01-0001-ABCD-EF01-123456789ABC`

| Characteristic | UUID | Size | Direction | Description |
|---------------|------|------|-----------|-------------|
| Servo Control | AB01-0002 | 6B | CoreS3 → StackChan | Servo angles + speed |
| Audio Playback | AB01-0003 | 3B | CoreS3 → StackChan | Sample ID + volume + loop |
| Expression Trigger | AB01-0004 | 1B | CoreS3 → StackChan | Pre-defined expression ID |
| StackChan State | AB01-0005 | 4B | StackChan → CoreS3 | Status + animation ID |
| Game Data | AB01-0006 | 8B | Bidirectional | Axis + buttons + game state |

---

## 4. StackChan GPIO Mapping

### 4.1 Standard StackChan Pinout (ESP32-WROOM-32)

The typical StackChan base uses these pins:

| GPIO | Function | Direction | Notes |
|------|----------|-----------|-------|
| 0 | BOOT | IN (PU) | Boot button (strapping) |
| 1 | UART_TX | OUT | Debug serial / external comms |
| 2 | SERVO_PAN | OUT (PWM) | SG90 head pan (horizontal) |
| 3 | UART_RX | IN | Debug serial / external comms |
| 4 | SERVO_TILT | OUT (PWM) | SG90 head tilt (vertical) |
| 5 | LED_MOUTH | OUT (Neo) | WS2812B LED strip for mouth |
| 25 | SPEAKER | OUT (DAC) | Built-in DAC audio output |
| 32 | BATT_ADC | IN (ADC1) | Battery voltage divider |
| 33 | BUTTON | IN (PU) | User button on StackChan |

**Conflict Note for UART Mode:** StackChan GPIO 1 (UART_TX) and GPIO 3 (UART_RX) are the natural UART interface. In the default StackChan design, these are used for USB debug. When connecting to CoreS3 via UART, these should be rewired as the inter-device UART link and a separate USB-serial adapter can be used for debugging if needed.

### 4.2 Conflict Analysis: StackChan Default vs Core S3 Pins

| StackChan Pin | Core S3 Equivalent Pin | Conflict? | Resolution |
|---------------|----------------------|-----------|------------|
| SERVO_PAN (GPIO 2) | Grove SCL (GPIO 2) | **YES** | Use StackChan GPIO 15 instead, or use I2C servo driver |
| SERVO_TILT (GPIO 4) | TFT_CS (GPIO 4) | **YES** | Use StackChan GPIO 16/17 instead |
| GPIO 1 (UART TX) | Grove SDA (GPIO 1) | **YES** | CoreS3 uses GPIO 1/2 for Grove, not available if wiring UART |
| GPIO 3 (UART RX) | Touch IRQ (GPIO 3) | **YES** | CoreS3 GPIO 3 is touch IRQ — avoid |

**Recommended Resolution:** Repurpose StackChan servo controls to non-conflicting pins when connecting to CoreS3:

| StackChan Pin | Function | PWM Capable | Rationale |
|---------------|----------|-------------|-----------|
| **GPIO 13** | SERVO_PAN | Yes (LEDC) | No conflict with Core S3 external pins |
| **GPIO 14** | SERVO_TILT | Yes (LEDC) | No conflict with Core S3 external pins |
| **GPIO 15** | LED_MOUTH | Yes (RMT) | WS2812-compatible, no conflict |
| **GPIO 25** | Speaker | DAC output | CoreS3 reads mic, StackChan plays audio |

### 4.3 Recommended StackChan Pin Assignment (for CoreS3 Interop)

| StackChan GPIO | Function | Connected To | Notes |
|----------------|----------|-------------|-------|
| **13** | **SERVO_PAN** | SG90 pan signal | PWM 50Hz, 0.5-2.5ms pulse |
| **14** | **SERVO_TILT** | SG90 tilt signal | PWM 50Hz, 0.5-2.5ms pulse |
| **15** | **LED_MOUTH** | WS2812B DIN | NeoPixel protocol, 800kHz |
| **25** | **SPEAKER** | Built-in speaker | DAC or I2S output |
| **1** | **UART_RX** | CoreS3 TX (GPIO 1) | Receive commands from CoreS3 |
| **3** | **UART_TX** | CoreS3 RX (GPIO 2) | Send status to CoreS3 |
| 32 | BATT_ADC | Battery divider | Read battery level |
| 33 | BUTTON | User button | Local input on StackChan |

#### SG90 Servo Wiring Details

| Servo Wire | Connection | Notes |
|------------|-----------|-------|
| **Brown (GND)** | StackChan GND | Common ground with CoreS3 |
| **Red (VCC)** | External 5V rail | **Never from ESP32 3.3V regulator** |
| **Orange (Signal)** | StackChan GPIO 13 or 14 | PWM signal from ESP32 GPIO |

#### PWM Configuration (ESP32 LEDC)

| Parameter | Value |
|-----------|-------|
| Frequency | 50 Hz |
| Resolution | 12-bit (0-4095) |
| Timer | LEDC_TIMER_0 (shared for both servos) |
| CH0 (SERVO_PAN) | LEDC_CHANNEL_0, GPIO 13 |
| CH1 (SERVO_TILT) | LEDC_CHANNEL_1, GPIO 14 |

#### Servo Angle ↔ PWM Duty Cycle

| Angle | Pulse Width | Duty Cycle (12-bit) |
|-------|-------------|---------------------|
| 0° | 0.5ms | 102 |
| 45° | 1.0ms | 205 |
| 90° (center) | 1.5ms | 307 |
| 135° | 2.0ms | 410 |
| 180° | 2.5ms | 512 |

Formula: `pulse_width_us = 500 + (angle / 180.0) * 2000`, then `duty = (pulse_width_us * 4096) / 20000`

---

## 5. Power Considerations

### 5.1 Core S3 Power Budget

| Component | Active Current | Idle/Sleep Current | Notes |
|-----------|---------------|-------------------|-------|
| ESP32-S3 (240MHz, active) | 60-80mA | ~10mA (modem sleep) | With caches enabled |
| ILI9342C TFT + Backlight | 40-60mA | ~0.5mA (sleep) | Backlight dimmable via PWM |
| BMI270 IMU | 0.8mA | 0.003mA | Accelerometer-only mode |
| FT6336U Touch | 5mA | 2mA | — |
| SPM1423 PDM Mic | 0.5mA | 0.001mA | — |
| AW88298 Audio Amp | 20-50mA | 0.001mA | Only when audio active |
| **Total (all active)** | **~200mA** | **~15mA** | Display dimmed |

**Typical USB supply:** 5V @ 500mA from USB-C is sufficient for Core S3 + Grove 5V output.

### 5.2 StackChan Power Budget

| Component | Active Current | Idle Current | Notes |
|-----------|---------------|-------------|-------|
| ESP32 (240MHz) | 40-60mA | 10mA | Lower clock (80MHz) sufficient for servo control |
| SG90 Servo × 2 (moving) | 200-300mA | ~50mA (holding) | **750mA stall each** |
| SG90 Servo × 2 (stall) | 1.5A | — | **Peak worst case** |
| Speaker (DAC) | 5-15mA | 0mA | At moderate volume |
| WS2812 × 8 LEDs | 1-15mA | 0mA | Brightness-dependent |
| **Total (typical)** | **~350mA** | **~60mA** | Servos moving |
| **Total (peak stall)** | **~1.6A** | — | Both servos stalled |

### 5.3 Critical Power Rules

**Rule 1: Separate Servo Power Supply Required**
- SG90 stall current (750mA × 2 = 1.5A) exceeds what the ESP32 3.3V regulator can supply
- **Must use an external 5V regulator** (e.g., AMS1117-5.0, buck converter, or dedicated 5V battery)
- Recommended: 5V 2A+ regulator with input from a 2-cell LiPo or USB power bank

**Rule 2: Common Ground**
- Servo GND, ESP32 GND, and CoreS3 GND must all be connected
- This provides a stable reference for UART and PWM signals

**Rule 3: Bulk Decoupling**

| Component | Value | Placement |
|-----------|-------|-----------|
| Electrolytic capacitor | 470µF / 16V | Across servo power rail |
| Ceramic bypass (each servo) | 100nF | Near each servo connector |
| Schottky diode | 1N5819 | On servo VCC (prevents back-powering) |

**Rule 4: CoreS3 Grove 5V Output Limits**
- AXP2101 PMIC provides 5V on the Grove port
- **Maximum output: ~500mA** — enough for one SG90 at a time
- For both servos: use external 5V supply, not CoreS3 Grove 5V

### 5.4 Power Architecture Diagram

```
USB-C (5V) ──┬── CoreS3 AXP2101 ── 3.3V ── ESP32-S3 + Sensors
              │                   └── 5V ── Grove (limited to 500mA)
              │
              └── External 5V Regulator ── 5V rail ──┬── SG90 Servo 1
                                                      ├── SG90 Servo 2
                                                      └── WS2812 LEDs
                                   
All grounds connected together (CoreS3 GND = StackChan ESP32 GND = Servo GND)
```

---

## 6. Three Interactive Modes — Pin Requirements

### Mode 1: Motion Controller (CoreS3 IMU → StackChan)

**Description:** CoreS3 reads BMI270 IMU orientation data and maps it to StackChan servo positions in real-time. Pan/tilt head tracking.

| Component | CoreS3 Interface | Pins Used | Notes |
|-----------|-----------------|-----------|-------|
| BMI270 IMU | I2C (internal bus) | GPIO 8 (SDA), 9 (SCL) | Read at 50-100Hz |
| UART TX | GPIO 1 (Grove SDA) | GPIO 1 | Sends servo commands to StackChan |
| UART RX | GPIO 2 (Grove SCL) | GPIO 2 | Receives status from StackChan |
| TFT Display | SPI | GPIO 4, 13, 15, 18, 23 | Show IMU data + status |
| RGB LED | GPIO | GPIO 21 | Status indicator |

**Data flow:**
```
BMI270 (I2C) → CoreS3 ESP32-S3 → UART (GPIO 1/2) → StackChan ESP32 → PWM (GPIO 13/14) → SG90 servos
```

**IMU mapping:**
- Roll (X-axis tilt) → SERVO_PAN (horizontal eye movement)
- Pitch (Y-axis tilt) → SERVO_TILT (vertical eye movement)
- Smoothing: moving average over 3 samples + exponential filter (alpha=0.7)
- Send rate: 50Hz (every 20ms), or on-change threshold > 2 degrees

**StackChan processing:**
- Receive UART command 0x02 (Servo Both) with [pan_angle, tilt_angle, speed]
- Apply trapezoidal speed profile for smooth motion
- Update PWM duty on GPIO 13 and GPIO 14

---

### Mode 2: Touch UI Controller (CoreS3 Touch → StackChan Expressions)

**Description:** CoreS3 touch panel gestures trigger pre-defined StackChan expressions combining servo positions, LED mouth patterns, and optional sound effects.

| Component | CoreS3 Interface | Pins Used | Notes |
|-----------|-----------------|-----------|-------|
| FT6336U Touch | I2C (internal bus) | GPIO 8 (SDA), 9 (SCL) | Read gesture ID + coordinates |
| UART TX | GPIO 1 (Grove SDA) | GPIO 1 | Sends expression commands |
| UART RX | GPIO 2 (Grove SCL) | GPIO 2 | Receives ack/status |
| TFT Display | SPI | GPIO 4, 13, 15, 18, 23 | Render touch UI buttons |
| RGB LED | GPIO | GPIO 21 | Feedback indicator |

**Gesture → Expression mapping:**

| Gesture | Detection Method | Expression Triggered |
|---------|-----------------|---------------------|
| Single tap | Touch register 0x02 = 0x01 | Neutral (reset) |
| Double tap | Touch register 0x02 = 0x0C | Surprise → Happy |
| Swipe up | Coordinate delta Y < -30px | Happy |
| Swipe down | Coordinate delta Y > 30px | Sad |
| Swipe left | Coordinate delta X < -30px | Look Left |
| Swipe right | Coordinate delta X > 30px | Look Right |
| Long press (>1s) | Touch held > 1000ms | Sleep |
| Pinch (2-finger) | Two touch points detected | Surprise |

**UI layout on CoreS3 TFT (320×240):**

```
┌──────────────────────────────────┐
│  [😊]  [😢]  [😮]  [😠]  [😴]   │  Top row: expression buttons
│  [←]   [→]   [↑]   [↓]   [⊙]   │  Middle row: direction buttons
│  [🔊] Volume: ████████░░ 80%   │  Volume slider
│  [🔁] Mode: Touch → Servo       │  Status bar
└──────────────────────────────────┘
```

---

### Mode 3: Voice-Controlled Reactions (CoreS3 PDM Mic → StackChan)

**Description:** CoreS3 SPM1423 PDM microphone detects ambient sound level and voice commands. StackChan reacts with servo movements, LED patterns, and sound effects.

| Component | CoreS3 Interface | Pins Used | Notes |
|-----------|-----------------|-----------|-------|
| SPM1423 Mic | PDM (I2S) | GPIO 47 (CLK), GPIO 14 (DATA) | PDM sample rate ~1MHz |
| UART TX | GPIO 1 (Grove SDA) | GPIO 1 | Sends reaction commands |
| UART RX | GPIO 2 (Grove SCL) | GPIO 2 | Receives status |
| TFT Display | SPI | GPIO 4, 13, 15, 18, 23 | Visualize audio level |
| RGB LED | GPIO | GPIO 21 | Audio level indicator |
| I2S Audio Amp | I2S | GPIO 10, 16, 17 | Optional sound feedback |

**Audio processing pipeline:**

```
SPM1423 PDM ─→ I2S (PDM mode) ─→ 16-bit samples @ 16kHz ─→ RMS calculation ─→ 
    ┌→ Threshold detection → UART command → StackChan servo/LED reaction
    └→ FFT (optional) → frequency band detection → tonal reactions
```

**Sound level → Reaction mapping:**

| Sound Level | Threshold (RMS) | StackChan Reaction | Duration |
|-------------|-----------------|--------------------|----------|
| Silence | < 10% | Idle (gentle breathing animation on servos) | Continuous |
| Quiet talking | 10-30% | Curious tilt (SERVO_TILT = 80°, curious LED pulse) | 2s |
| Normal speech | 30-50% | Attentive (eyes center, white LED, nod once) | 1.5s |
| Loud talking | 50-70% | Surprised (eyes wide, red LED flash) | 1.0s |
| Clap (>80% threshold spike) | > 80% | Startle (rapid blink + jump) | 500ms |
| Sustained noise | > 60% for 5s | Annoyed (shake head, angry LED) | 3.0s |

**Optional voice command recognition (advanced):**
- Use simple energy threshold + zero-crossing rate for clap detection
- For word recognition: integrate with offline TinyML (TensorFlow Lite Micro) on CoreS3
- Limited to 2-3 commands due to ESP32-S3 inference constraints

---

## 7. Mode Switching & Concurrent Operation

### 7.1 Mode Selection

Modes can be switched at runtime via:

1. **CoreS3 touch button** on TFT UI (always available)
2. **BLE command** from a connected mobile app (if BLE enabled)
3. **Hardware button** on StackChan (GPIO 33)

### 7.2 Mode State Machine

```
                    ┌────────────────┐
                    │   IDLE/SLEEP   │
                    └───────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌──────────┐ ┌────────────┐ ┌──────────────┐
       │  Mode 1  │ │  Mode 2    │ │   Mode 3     │
       │  Motion  │ │  Touch UI  │ │  Voice Ctrl  │
       └──────────┘ └────────────┘ └──────────────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                    ┌───────▼────────┐
                    │  RETURN TO IDLE│
                    └────────────────┘
```

### 7.3 Pin Utilization Summary (All Modes)

| CoreS3 Pin | Mode 1 | Mode 2 | Mode 3 | Always Used? |
|------------|--------|--------|--------|-------------|
| GPIO 1 (TX to StackChan) | UART TX | UART TX | UART TX | **Yes** |
| GPIO 2 (RX from StackChan) | UART RX | UART RX | UART RX | **Yes** |
| GPIO 8 (I2C SDA) | Touch + IMU | Touch | Touch | **Yes** |
| GPIO 9 (I2C SCL) | Touch + IMU | Touch | Touch | **Yes** |
| GPIO 4 (TFT CS) | TFT | TFT | TFT | **Yes** |
| GPIO 18 (SPI SCLK) | TFT + SD | TFT + SD | TFT + SD | **Yes** |
| GPIO 23 (SPI MOSI) | TFT + SD | TFT + SD | TFT + SD | **Yes** |
| GPIO 13 (TFT RST) | TFT | TFT | TFT | **Yes** |
| GPIO 15 (TFT DC) | TFT | TFT | TFT | **Yes** |
| GPIO 21 (RGB LED) | Status | Status | VU meter | **Yes** |
| GPIO 47 (PDM CLK) | — | — | Mic clock | Mode 3 only |
| GPIO 14 (PDM DATA) | — | — | Mic data | Mode 3 only |
| BMI270 I2C (0x68) | Accelerometer | — | — | Mode 1 only |
| FT6336U I2C (0x38) | — | Touch | — | Mode 2 only |

**Key insight:** UART (GPIO 1/2) and TFT display (SPI) are shared across all three modes. Each mode adds one additional sensor interface without changing the basic wiring.

---

## 8. Pin Conflict Checklist

| Conflict | Status | Mitigation |
|----------|--------|------------|
| GPIO 1 (Grove SDA) used for UART TX | **Resolved** | UART on GPIO 1/2 — not available for I2C Grove devices |
| GPIO 2 (Grove SCL) used for UART RX | **Resolved** | Same as above |
| GPIO 19 (SD_MISO / USB_DM) | **Warning** | Cannot use SD card while USB serial connected |
| GPIO 20 (USB DP) | **Not used** | Avoid |
| GPIO 46 (strapping) | **Not used** | Avoid |
| StackChan GPIO 13 → CoreS3 GPIO 13 (TFT RST) | **Independent** | Separate devices, no conflict |
| StackChan GPIO 14 → CoreS3 GPIO 14 (Mic DATA) | **Independent** | Separate devices, no conflict |
| ADC2 + WiFi (if WiFi enabled) | **Not applicable** | Apps don't use WiFi. No conflict. |
| Shared SPI bus (display + SD) | **Managed** | Different CS pins. Never activate both simultaneously. |

---

## 9. Required External Components

| Component | Quantity | Purpose | Approx Cost |
|-----------|----------|---------|-------------|
| HY2.0-4P Grove cable | 1 | CoreS3 ↔ StackChan UART connection | $1 |
| 5V 2A regulator (e.g., AMS1117-5.0) | 1 | Dedicated servo power supply | $2 |
| 470µF 16V electrolytic capacitor | 1 | Servo power rail decoupling | $0.50 |
| 100nF ceramic capacitor | 2 | Local bypass near each servo | $0.10 |
| 1N5819 Schottky diode | 1 | Back-powering protection | $0.20 |
| Jumper wires (female-to-female) | 4-6 | CoreS3 header → StackChan connections | $1 |
| USB power bank or 2-cell LiPo | 1 | Separate servo power source (if not using USB) | $10-15 |

**Total BOM: ~$5-20** (depending on whether servo power supply is already available)

---

## 10. Wiring Diagram

```
M5Stack Core S3                         M5Stack StackChan
┌──────────────────┐                    ┌──────────────────────┐
│                  │                    │                      │
│  Grove Port      │                    │  GPIO 1 ─── UART RX  │
│  (HY2.0-4P)      │                    │  GPIO 3 ─── UART TX  │
│                  │                    │                      │
│  Pin 1 (SDA) ────┼────────────────────── GPIO 1 (UART RX)   │
│  Pin 2 (SCL) ────┼────────────────────── GPIO 3 (UART TX)   │
│  Pin 3 (5V)  ────┼───── 5V ───────────── VIN (optional)     │
│  Pin 4 (GND) ────┼────────────────────── GND                 │
│                  │                    │                      │
│                  │                    │  GPIO 13 ─── SG90 Pan │
│                  │                    │  GPIO 14 ─── SG90 Tilt│
│                  │                    │  GPIO 15 ─── WS2812   │
│                  │                    │  GPIO 25 ─── Speaker  │
│                  │                    │                      │
│  Internal:       │                    │  External:           │
│  I2C: IMU/Touch  │                    │  5V Regulator ──┐    │
│  SPI: TFT        │                    │                 │    │
│  PDM: Mic        │                    │  SG90 VCC ◄────┘    │
└──────────────────┘                    └──────────────────────┘
```

---

## 11. Firmware Bring-Up Sequence

### Step 1: UART Loopback Test
```
CoreS3: Send 0xAA 0x08 0x01 0x00 0x00 0x00 0xA3 0x55 (heartbeat with seq=1)
StackChan: Should receive and respond with 0xAA 0x08 0x01 0x00 0x00 0x00 <CS> 0x55
```

### Step 2: Servo Sweep Test
```
CoreS3 → StackChan: 0xAA 0x02 [pan_angle=0] [tilt_angle=90] [speed=50] <CS> 0x55
CoreS3 → StackChan: 0xAA 0x02 [pan_angle=180] [tilt_angle=90] [speed=50] <CS> 0x55
Observe: SERVO_PAN should sweep from 0° to 180°
```

### Step 3: Mode 1 IMU Integration
```
Read BMI270 at 50Hz → map roll/pitch to 0-180° → send UART command 0x02
TFT displays: "Mode 1: Motion Control" + angle readout
```

### Step 4: Mode 2 Touch Integration
```
Read FT6336U gesture register
On tap → send expression command 0x04 with expression_id
TFT renders UI buttons
```

### Step 5: Mode 3 Audio Integration
```
Initialize I2S in PDM mode → read samples → calculate RMS
On threshold exceed → send expression command 0x04
TFT shows audio level bar
```

---

## 12. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| UART data corruption | Medium | Low | Checksum byte + retry on failure. StackChan ignores invalid packets. |
| Servo power brownout | High | Medium | External 5V supply + 470µF bulk capacitor. Test under load. |
| I2C bus capacitance (5 devices) | Medium | Low | All onboard, short traces. Fine at 100-400kHz. |
| GPIO 19 USB conflict | Medium | Medium | Document clearly. Use battery power when SD card needed. |
| StackChan ESP32 GPIO conflict with original StackChan firmware | Medium | Low | Custom firmware for StackChan. Pin assignments documented. |
| PDM mic noise on UART lines | Low | Low | UART is differential enough. Keep servo cables away from Grove cable. |

---

## 13. Conclusion

This GPIO plan defines a complete hardware wiring specification for the M5Stack CoreS3 + StackChan interactive project.

**Key design decisions:**

1. **UART (GPIO 1/2 via Grove port)** as the primary inter-device protocol — deterministic, low-latency, zero pairing
2. **BLE 5.0** as optional wireless fallback — no additional pins needed, but introduces ~5-15ms latency
3. **StackChan servos moved to GPIO 13/14** to avoid conflicts with CoreS3's fixed pin allocation
4. **External 5V regulator** for servo power — prevents brownout and protects ESP32 regulators
5. **All three modes share the same basic wiring (UART + power)** — mode switching is purely a firmware concern
6. **Legacy StackChan pin conflicts resolved** by shifting servo control to unused GPIO pins

**Next steps (firmware):**
- Implement CoreS3 UART TX/RX using HardwareSerial on GPIO 1/2
- Implement StackChan UART receiver with checksum validation
- Implement servo PWM on StackChan GPIO 13/14 using ESP32 LEDC peripheral
- Develop each mode incrementally: UART loopback → servo sweep → IMU integration → touch → audio
