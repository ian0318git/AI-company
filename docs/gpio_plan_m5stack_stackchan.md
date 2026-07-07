# M5Stack Core S3 + StackChan Collaboration Project
## GPIO Assignment & Hardware Integration Plan

**Role:** Embedded Firmware Engineer
**Date:** 2026-07-08
**Version:** 1.0

---

## 1. System Overview

Two devices collaborate via **BLE (Bluetooth Low Energy 5.0)**:

| Device | Role | Key Hardware |
|--------|------|-------------|
| **M5Stack Core S3** | Motion Controller | BMI270 IMU, FT6336U Touch, ILI9342C TFT, SPM1423 PDM Mic |
| **StackChan** | Robot Avatar | 2x SG90 servos (pan/tilt), Speaker (DAC/I2S), WS2812 LED mouth |

**Communication Protocol: BLE 5.0** (recommended over WiFi/MQTT or I2C)

| Criterion | BLE 5.0 | WiFi/MQTT | I2C (Grove) | Winner |
|-----------|---------|-----------|-------------|--------|
| Latency | 5-15ms | 20-50ms | <1ms | I2C |
| Range | ~10m | ~30m | <1m | WiFi |
| Infrastructure | None | Router required | Wire only | BLE/I2C |
| Power (idle) | ~1uA | ~20mA | ~0mA | BLE |
| Mobility | Free | Free | Tethered | BLE/WiFi |
| Throughput | ~1.4Mbps | ~50Mbps | ~400kbps | WiFi |
| Pairing | Simple | Network config | None | BLE |

**Rationale for BLE:** No infrastructure required, sufficiently low latency for real-time servo control (~5-15ms), significantly lower idle power than WiFi, and both ESP32-S3 and ESP32 have mature native BLE 5.0 stacks.

---

## 2. Three Interactive Scenarios

### Scenario A: Motion Mirroring (Real-time Head Tracking)
- CoreS3 reads IMU orientation (quaternion/euler angles)
- BLE sends angle data at ~50Hz
- StackChan mirrors head pan/tilt in real-time with servo interpolation
- CoreS3 displays mirrored status on TFT

### Scenario B: Gesture Commands
- CoreS3 detects gestures via IMU: shake, nod, tilt, circle, tap
- BLE sends gesture ID (compact 1-byte packet)
- StackChan executes pre-programmed animation sequence (servo + sound)
- CoreS3 provides visual feedback on gesture detected

### Scenario C: Game Controller (Interactive Play)
- CoreS3 reads tilt + touch input as game controller
- BLE sends control data bidirectionally
- StackChan responds with servo movements + sound effects
- Game state synchronized over BLE

---

## 3. M5Stack Core S3 Complete GPIO Assignment

### 3.1 Internal Peripherals (Fixed - in use)

| GPIO | Signal | Direction | Pull | Connected To |
|------|--------|-----------|------|-------------|
| 0 | BOOT | IN | UP | Boot button (strapping pin) |
| 1 | GROVE_SDA | I/O (I2C) | UP | Grove port SDA / G1 header |
| 2 | GROVE_SCL | I/O (I2C) | UP | Grove port SCL / G2 header |
| 3 | TOUCH_INT | IN (IRQ) | UP | FT6336U touch interrupt |
| 4 | TFT_CS | OUT | UP | ILI9342C SPI chip select |
| 5 | SD_CS | OUT | UP | microSD card SPI CS |
| 6 | AUDIO_EN | OUT | - | AW88298 audio amp enable |
| 7 | BUZZER | OUT (PWM) | - | Passive buzzer |
| 8 | I2C_SDA | I/O | UP | Shared I2C SDA bus (all internal I2C) |
| 9 | I2C_SCL | I/O | UP | Shared I2C SCL bus (all internal I2C) |
| 10 | I2S_DOUT | OUT | - | AW88298 I2S data out |
| 11 | TOUCH_RST | OUT | - | FT6336U touch reset |
| 12 | LCD_BL | OUT (PWM) | - | ILI9342C backlight boost |
| 13 | TFT_RST | OUT | - | ILI9342C reset |
| 14 | MIC_DATA | IN (PDM) | - | SPM1423 PDM mic data |
| 15 | TFT_DC | OUT | - | ILI9342C data/command |
| 16 | I2S_LRCK | OUT | - | AW88298 I2S left/right clock |
| 17 | I2S_BCLK | OUT | - | AW88298 I2S bit clock |
| 18 | SCLK | OUT | - | Shared SPI clock |
| 19 | SD_MISO / USB_DM | I/O | - | SD card MISO / USB D- (**conflict**) |
| 20 | USB_DP | I/O | - | USB D+ |
| 21 | RGB_LED | OUT (Neo) | - | SK6812 RGB LED (NeoPixel) |
| 23 | MOSI | OUT | - | Shared SPI MOSI |
| 43 | UART_TX | OUT | - | USB Serial TX |
| 44 | UART_RX | IN | - | USB Serial RX |
| 46 | STRAP | - | - | **DO NOT USE** (strapping pin) |
| 47 | MIC_CLK | OUT (PDM) | - | SPM1423 PDM mic clock |

**Critical note on GPIO 19:** GPIO 19 is shared between SD_MISO (SPI) and USB_DM (USB Serial/JTAG). When USB is connected for serial debug, the SD card slot is unavailable. This is a hardware limitation of the Core S3 design.

### 3.2 I2C Bus Map (SDA=8, SCL=9)

| Device | Address | Bus | Type |
|--------|---------|-----|------|
| FT6336U Touch | 0x38 | I2C-0 | Capacitive touch controller |
| BMI270 IMU | 0x68 | I2C-0 | 6-axis accel + gyro |
| BMM150 Mag | 0x10 | I2C-0 | 3-axis magnetometer (sub-addr) |
| BM8563 RTC | 0x51 | I2C-0 | Real-time clock |
| AXP2101 PMIC | 0x34 | I2C-0 | Power management IC |

All five devices share a single I2C bus on GPIO 8 (SDA) / GPIO 9 (SCL) with built-in 4.7k pull-ups. For external I2C via Grove, use GPIO 1 (SDA) / GPIO 2 (SCL), which is a separate I2C port.

### 3.3 Shared SPI Bus

| Signal | GPIO | Display | SD Card | Notes |
|--------|------|---------|---------|-------|
| MOSI | 23 | DIN | MOSI | Shared |
| SCLK | 18 | CLK | CLK | Shared |
| MISO | 19 | - | MISO | SD only (display MISO is NC) |
| CS | 4 | CS | - | Display chip select |
| CS | 5 | - | CS | SD card chip select |
| DC | 15 | DC | - | Display only |
| RST | 13 | RST | - | Display only |

### 3.4 Available GPIOs for Expansion

The Core S3 has very few free GPIOs on the external connector. Since BLE handles all inter-device communication, no additional external GPIOs are required for this project.

| GPIO | Notes |
|------|-------|
| 1, 2 | Grove I2C port - available if not using external I2C |
| 45, 48 | Not broken out on external header (silicon pad only on PCB) |

---

## 4. StackChan GPIO Assignment (Recommended)

Assumes StackChan with ESP32-WROOM-32, 2x SG90 servos, speaker, and WS2812 LED mouth.

| GPIO | Function | Direction | Notes |
|------|----------|-----------|-------|
| 0 | BOOT | IN | Boot button (strapping) |
| 1 | UART_TX | OUT | USB Serial TX (debug) |
| 3 | UART_RX | IN | USB Serial RX (debug) |
| **13** | **SERVO_PAN** | **OUT (PWM)** | **SG90 head pan (horizontal rotation)** |
| **14** | **SERVO_TILT** | **OUT (PWM)** | **SG90 head tilt (vertical)** |
| **15** | **LED_MOUTH** | **OUT (Neo)** | **WS2812B LED strip for mouth animation** |
| 25 | SPEAKER | OUT | Built-in DAC audio (alternative: I2S) |
| 32 | BATT_ADC | IN | Battery voltage divider (ADC1) |
| 33 | BUTTON | IN (PU) | User button |

**Alternative I2S DAC pinout (if using MAX98357):**
| GPIO | Function |
|------|----------|
| 25 | I2S_BCLK |
| 26 | I2S_LRCK |
| 27 | I2S_DIN |

---

## 5. BLE Communication Protocol

### 5.1 GATT Profile

| Role | Device | Mode |
|------|--------|------|
| Central (Client) | M5Stack Core S3 | Scans, connects, sends commands |
| Peripheral (Server) | StackChan | Advertises, receives commands, sends state |

### 5.2 Custom Service

**Service UUID:** `AB01-0001-ABCD-EF01-123456789ABC`

| Characteristic | UUID | Size | Direction | Description |
|---------------|------|------|-----------|-------------|
| Servo Control | AB01-0002 | 6B | CoreS3 -> StackChan | Servo angles + speed |
| Audio Playback | AB01-0003 | 3B | CoreS3 -> StackChan | Sample ID + volume + loop |
| Gesture Trigger | AB01-0004 | 1B | CoreS3 -> StackChan | Pre-defined gesture ID |
| StackChan State | AB01-0005 | 4B | StackChan -> CoreS3 | Status + animation ID |
| Game Data | AB01-0006 | 8B | Bidirectional | Axis + buttons + game state |
| Battery Level | 0x2A19 | 1B | StackChan -> CoreS3 | Standard BLE battery service |

### 5.3 Data Payloads

**Servo Control (6 bytes):**
```
[0] servo_id     (0=pan, 1=tilt, 2=both)
[1] angle_pan    (0-180 degrees)
[2] speed_pan    (0-255, higher=faster)
[3] angle_tilt   (0-180 degrees)
[4] speed_tilt   (0-255)
[5] flags        (bit0=relative mode, bit1=interpolate)
```

**Gesture Trigger (1 byte):**
```
0x01 = nod (yes)
0x02 = shake (no)
0x03 = tilt_left
0x04 = tilt_right
0x05 = circle_cw
0x06 = circle_ccw
0x07 = shake_hard (excited)
0x08 = double_tap (on CoreS3 touch)
```

---

## 6. Power Management

### 6.1 CoreS3 Power Budget (actively streaming IMU)

| Component | Active | Idle | Notes |
|-----------|--------|------|-------|
| ESP32-S3 (240MHz) | 60-80mA | 20mA | With caches enabled |
| ILI9342C + BL | 40-60mA | 0mA | Backlight PWM controllable |
| BMI270 IMU | 0.8mA | 0.003mA | Low-power mode available |
| BLE (connected) | 10-30mA | 1uA | Connected interval dependent |
| AW88298 Audio | 20-50mA | 0.001mA | Only when playing |
| **TYPICAL** | **~150mA** | **~25mA** | Display on dim |

### 6.2 StackChan Power Budget

| Component | Active | Idle | Notes |
|-----------|--------|------|-------|
| ESP32 (80MHz) | 30-50mA | 10mA | Lower clock OK for servo control |
| SG90 Servo x2 | 100-300mA | 10mA | Idle holding position (750mA stall each) |
| Speaker (DAC) | 5-15mA | 0mA | At moderate volume |
| WS2812 x8 | 1-15mA | 0mA | Color/brightness dependent |
| BLE (connected) | 10-30mA | 1uA | Peripheral mode |
| **TYPICAL** | **~200mA** | **~20mA** | Servos at rest |

### 6.3 Power Recommendations

1. **CoreS3**: Powered via USB-C (5V) during development. Use built-in AXP2101 PMIC for battery management when portable.

2. **StackChan Servo Power**:
   - Use a separate 5V regulator (e.g., AMS1117-5.0 or buck converter rated 2A+)
   - SG90 stall current = 750mA x 2 = 1.5A peak
   - **NEVER** draw servo current through ESP32's 3.3V onboard regulator
   - Connect servo GND to ESP32 GND (common ground reference)

3. **Protection Circuit**:
   - 470uF electrolytic capacitor across servo power rail
   - 100nF ceramic bypass capacitor near each servo connector
   - Schottky diode on servo VCC to prevent back-powering ESP32 during brownout

---

## 7. Signal Integrity Guidelines

### 7.1 I2C Bus
- 5 internal devices + optional Grove I2C -> bus capacitance is near limit
- Built-in pull-ups: 4.7k (factory populated on CoreS3 PCB)
- If extending I2C via Grove: add 10k external pull-up if cable exceeds 20cm
- Max cable length at 400kHz: ~30cm. Use 100kHz for longer runs.
- ESP32 I2C clock stretching issues: set I2C timeout to at least 50ms

### 7.2 SPI Bus
- Display and SD card share MOSI (23) and SCLK (18)
- Each has its own CS line (Display=4, SD=5) - never activate both simultaneously
- SD MISO (19) conflicts with USB_DM -> cannot use SD while USB serial connected

### 7.3 PDM Microphone
- PDM lines (CLK=47, DATA=14) route near I2S audio lines on PCB
- Pre-routed on CoreS3 board - no concern for this project

### 7.4 BLE Antenna
- CoreS3: built-in PCB antenna on top edge of board
- StackChan: ESP32 module with integrated PCB antenna
- Ensure no metal enclosure blocks antenna path
- Expected range: ~10m indoor (sufficient for interactive play scenarios)

---

## 8. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| GPIO 19 conflict (SD_MISO / USB_DM) | High | High | Document clearly. Use battery power when SD needed. |
| BLE connection drops during session | Medium | Medium | Auto-reconnect with 1s watchdog timeout |
| I2C bus capacitance exceeded (5 internal devices) | Medium | Medium | Keep external I2C cable <30cm, use 100kHz |
| Servo power brownout (both servos stalling) | High | Medium | External 5V regulator + bulk capacitor |
| AXP2101 5V rail overcurrent | High | Low | Don't draw >500mA from CoreS3 5V out. Use external servo supply. |

---

## 9. Firmware Architecture (High-Level)

### CoreS3 Tasks (Motion Controller)

| Task Name | Priority | Stack (bytes) | Core | Description |
|-----------|----------|--------------|------|-------------|
| imu_task | 5 (high) | 4096 | 1 | Read BMI270 at 100Hz via I2C |
| gesture_task | 4 | 4096 | 1 | IMU gesture detection pipeline |
| ble_task | 3 | 8192 | 1 | BLE NimBLE stack + data send |
| ui_task | 2 | 6144 | 0 | TFT display + touch handling |
| audio_task | 2 | 4096 | 0 | PDM mic input (voice commands) |

### StackChan Tasks (Robot Avatar)

| Task Name | Priority | Stack (bytes) | Core | Description |
|-----------|----------|--------------|------|-------------|
| ble_task | 5 (high) | 6144 | 0 | BLE server + command receive |
| servo_task | 4 | 3072 | 1 | PWM servo control + interpolation |
| animation_task | 3 | 4096 | 1 | Animation sequence engine |
| audio_task | 3 | 4096 | 1 | Sound playback via DAC/I2S |
| status_task | 1 | 2048 | 0 | Battery monitoring, BLE state broadcast |

---

## 10. Conclusion

This GPIO plan provides a complete hardware foundation for the M5Stack Core S3 + StackChan collaboration project. The key design decisions are:

1. **BLE 5.0** as the primary communication protocol - best balance of latency, power, and mobility
2. **StackChan as BLE peripheral** (server) - always advertising, CoreS3 connects on demand
3. **Compact binary protocol** (1-8 byte packets) - minimizes BLE transmission overhead
4. **External servo power supply** for StackChan - prevents brownout and protects ESP32
5. **All CoreS3 internal peripherals remain active** - touch, display, IMU, and mic all contribute to the interactive experience
6. **No external GPIO wiring needed** between the two devices - wireless BLE eliminates cabling constraints

The design is ready for firmware implementation with the next steps being:
- Implement BLE GATT service on both devices using ESP-NIMBLE
- Implement BMI270 IMU driver with gesture detection on CoreS3
- Implement servo control with smooth interpolation on StackChan
- Develop the three interactive scenarios incrementally (mirroring -> gestures -> game)
