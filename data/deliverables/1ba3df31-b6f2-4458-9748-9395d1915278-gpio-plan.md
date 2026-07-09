# M5Stack Core S3 ↔ StackChan GPIO Pin Assignment Plan

## Overview

This document defines the GPIO pin assignments for three interactive applications between M5Stack Core S3 and M5Stack StackChan. The StackChan is a robot face accessory with servo-controlled eyes and optional sensor/display interactions.

**Boards:**
- **M5Stack Core S3** (ESP32-S3, 240MHz, 8MB PSRAM, 16MB Flash)
- **M5Stack StackChan** (M5Stack Core/Core2 compatible robot face with dual servos)

---

## 1. Available GPIO Resources

### M5Stack Core S3

| Pin | Function | Notes |
|-----|----------|-------|
| GPIO 0 | BOOT button | Pull LOW to enter flash mode. Strapping pin. |
| GPIO 1 | Grove SDA | I2C data (shared with all onboard I2C devices) |
| GPIO 2 | Grove SCL | I2C clock (shared with all onboard I2C devices) |
| GPIO 3 | Touch IRQ | FT6336U interrupt. Available if touch not in use. |
| GPIO 4 | Display CS | SPI chip select for ILI9342C |
| GPIO 5 | SD Card CS | SPI chip select for microSD |
| GPIO 6 | Audio EN | AW88298 amplifier enable |
| GPIO 7 | Buzzer | Passive buzzer PWM |
| GPIO 8 | I2C SDA | Shared I2C bus (touch, IMU, RTC, PMIC) |
| GPIO 9 | I2C SCL | Shared I2C bus (touch, IMU, RTC, PMIC) |
| GPIO 10 | Audio DOUT | AW88298 I2S data out |
| GPIO 11 | Touch RST | FT6336U reset |
| GPIO 12 | Display BL | LCD backlight |
| GPIO 13 | Display RST | ILI9342C reset |
| GPIO 14 | Mic Data | SPM1423 PDM data |
| GPIO 15 | Display DC | ILI9342C data/command |
| GPIO 16 | Audio LRCK | AW88298 I2S left-right clock |
| GPIO 17 | Audio BCLK | AW88298 I2S bit clock |
| GPIO 18 | SPI SCLK | Shared SPI clock (display + SD) |
| GPIO 19 | SD MISO | SD card SPI MISO (shared with USB DP — caution) |
| GPIO 20 | USB DP | USB D+. Do NOT use; conflicts with USB. |
| GPIO 21 | RGB LED | SK6812 NeoPixel |
| GPIO 23 | SPI MOSI | Shared SPI MOSI (display + SD) |
| GPIO 43 | UART TX | Serial debug output |
| GPIO 44 | UART RX | Serial debug input |
| GPIO 46 | Strapping | Do NOT use. Boot mode selection. |
| GPIO 47 | Mic CLK | SPM1423 PDM clock |

### Grove Port (Port A - HY2.0-4P)
- **SDA**: GPIO 1
- **SCL**: GPIO 2
- **VCC**: 5V (level-shifted to 3.3V for signals)
- **GND**: Ground

These are the cleanest external access points — **recommended primary interface** for StackChan connection.

---

## 2. StackChan Pinout (Standard Configuration)

The M5Stack StackChan typically uses the following connections via the M5Stack Core bottom GPIO port:

| Function | GPIO | Notes |
|----------|------|-------|
| Left Eye Servo (PWM) | GPIO 13 | SG90 or similar micro servo |
| Right Eye Servo (PWM) | GPIO 14 | SG90 or similar micro servo |
| Mouth/Speaker | GPIO 2 | Passive buzzer or speaker (some variants) |
| PIR/Ultrasonic | GPIO 36 | Optional sensor (some variants) |

**IMPORTANT CONFLICT**: GPIO 13 and GPIO 14 on Core S3 are used for Display RST and Mic Data respectively. These pins **cannot** drive StackChan servos directly from Core S3 without modifying the StackChan harness.

---

## 3. Conflict Analysis and Resolution

### The Problem

StackChan standard design uses:
- GPIO 13 → Left servo (but Core S3 uses GPIO 13 for Display RST)
- GPIO 14 → Right servo (but Core S3 uses GPIO 14 for Microphone PDM data)

### Resolution Strategy

**Option A: Use Grove Port (Recommended)**
- Redirect servo control signals through the Grove port GPIO 1 (SDA) and GPIO 2 (SCL)
- Use the Core S3's built-in M5Unified I2C to send commands to StackChan
- Requires a firmware-level servo PWM generator on GPIO 1 and GPIO 2
- **Pros**: No soldering, clean signal, shared with existing connector
- **Cons**: GPIO 1 and 2 are I2C bus — cannot use standard I2C devices on Grove simultaneously

**Option B: GPIO Header Passthrough (Alternative)**
- Use the 8-pin GPIO header (G1-G8)
- Map: G1→Servo1, G2→Servo2 (GPIO 1 and 2 via Header)
- **Pros**: Direct PWM control
- **Cons**: Same GPIO conflict, limited to 2 pins

**Option C: I2C Servo Driver (Best for 3+ apps)**
- Add a PCA9685 PWM driver module on the Grove I2C port
- Drives up to 16 servos with I2C commands
- GPIO 1 (SDA) and GPIO 2 (SCL) are used in I2C mode
- **Pros**: No GPIO conflict, clean separation, scales to more peripherals
- **Cons**: Requires external module (PCA9685 ~$3)

### Recommendation

**Use Option C (PCA9685 via Grove I2C) for maximum compatibility and clean design.**

---

## 4. Final Pin Assignment Plan (Option C)

| Core S3 Pin | Direction | Connection | Purpose |
|-------------|-----------|-----------|---------|
| **Grove SDA** (GPIO 1) | Bidir | → PCA9685 SDA | I2C data for servo driver |
| **Grove SCL** (GPIO 2) | Bidir | → PCA9685 SCL | I2C clock for servo driver |
| **Grove 5V** | Power out | → PCA9685 VCC | 5V servo power |
| **Grove GND** | Ground | → PCA9685 GND | Common ground |
| **Internal I2C** (GPIO 8/9) | Bidir | → BMI270, FT6336U | Onboard sensor I2C (not shared with Grove) |
| **Internal IMU** (I2C 0x68) | Input | → Core S3 | Motion data for "motion controller" app |
| **Internal TFT** (SPI) | Output | → ILI9342C | Display UI for all apps |
| **Internal Mic** (PDM) | Input | → SPM1423 | Sound detection for "sound reactive" app |
| **Internal RGB LED** (GPIO 21) | Output | → SK6812 | Status indicators |

### PCA9685 Configuration

| PCA9685 Channel | Servo | Range | Notes |
|-----------------|-------|-------|-------|
| CH0 | Left Eye | 0°–180° | Neutral at 90° (center look) |
| CH1 | Right Eye | 0°–180° | Neutral at 90° (center look) |
| CH2–CH15 | (Reserved) | — | Future expansion (mouth servo, neck tilt, etc.) |

### Servo Specifications (SG90)

| Parameter | Value |
|-----------|-------|
| Operating Voltage | 4.5V–6.0V (use 5V rail) |
| PWM Frequency | 50 Hz (20ms period) |
| PWM Range | 0.5ms–2.5ms (0°–180°) |
| PWM Values (PCA9685 counts) | 102–512 (at 12-bit, 4096 counts) |
| Current per Servo | ~150mA (moving), ~10mA (holding) |
| Total Servo Current | ~300mA peak (both moving simultaneously) |

---

## 5. Three Interactive Applications — Pin Utilization

### App 1: Motion Controller (Core S3 → StackChan)

**Core S3 reads BMI270 IMU → controls StackChan eye servos via PCA9685**

| Component | Interface | Pins Used | Data Rate |
|-----------|-----------|-----------|-----------|
| BMI270 IMU | I2C (internal, GPIO 8/9) | SDA(8), SCL(9) | 100kHz |
| PCA9685 | I2C (Grove, GPIO 1/2) | SDA(1), SCL(2) | 400kHz |
| TFT Display | SPI (internal) | CS(4), DC(15), MOSI(23), SCLK(18) | 80MHz |
| RGB LED | GPIO (internal) | 21 | Single bit |

**IMU mapping**: Roll → eye X position (left/right), Pitch → eye Y position (up/down)

### App 2: Touch Controller (Core S3 Touch → StackChan Expressions)

**Core S3 touch gestures → predefined StackChan expressions (servo positions)**

| Component | Interface | Pins Used | Data Rate |
|-----------|-----------|-----------|-----------|
| FT6336U Touch | I2C (internal, GPIO 8/9) | SDA(8), SCL(9) | 100kHz |
| PCA9685 | I2C (Grove, GPIO 1/2) | SDA(1), SCL(2) | 400kHz |
| TFT Display | SPI (internal) | CS(4), DC(15), MOSI(23), SCLK(18) | 80MHz |

**Gesture mapping**:
- Swipe left → eyes look left
- Swipe right → eyes look right  
- Tap → blink (both eyes close 200ms then open)
- Double tap → happy expression (eyes go up)
- Long press → thinking expression (eyes look up-left)
- Pinch → surprise (eyes wide)

### App 3: Sound Reactive (Core S3 Microphone → StackChan)

**Core S3 PDM mic detects sound level → StackChan reacts with servo + TFT animation**

| Component | Interface | Pins Used | Data Rate |
|-----------|-----------|-----------|-----------|
| SPM1423 Mic | PDM (internal) | CLK(47), DATA(14) | ~1MHz PDM |
| PCA9685 | I2C (Grove, GPIO 1/2) | SDA(1), SCL(2) | 400kHz |
| TFT Display | SPI (internal) | CS(4), DC(15), MOSI(23), SCLK(18) | 80MHz |
| RGB LED | GPIO (internal) | 21 | Single bit |

**Sound reaction**:
- Low sound (<40dB) → idle (eyes center, green LED)
- Medium sound (40–70dB) → curious (eyes tilt, blue LED)
- Loud sound (>70dB) → surprised (eyes wide, red LED + blink)
- Clap detection → toggle between apps

---

## 6. Power Budget

| Component | Active Current | Idle Current |
|-----------|---------------|-------------|
| Core S3 (CPU active, WiFi off) | ~60mA | ~20mA |
| TFT Display (320x240, on) | ~40mA | ~0.5mA (sleep) |
| PCA9685 | ~5mA | ~0.5mA |
| SG90 Servo × 2 (moving) | ~300mA | ~20mA (holding) |
| BMI270 (accel only mode) | ~0.5mA | ~0.005mA |
| FT6336U Touch | ~5mA | ~2mA |
| SPM1423 Mic | ~0.5mA | ~0.001mA |
| **Total** | **~411mA** | **~43mA** |

**Battery life estimate** (with 500mAh LiPo):
- Continuous active use: ~1.2 hours
- Idle/standby: ~11.6 hours
- Normal mixed use: ~2–3 hours

---

## 7. Software Architecture (Pin Control Layer)

```
┌──────────────────────────────────────────────────┐
│                  App Layer                        │
│  MotionController  │  TouchController  │  Sound   │
└─────────┬──────────┴─────────┬──────────┴─────────┘
          │                    │                    │
┌─────────┴────────────────────┴────────────────────┐
│              ServoController (abstraction)         │
│  - setEyePosition(left_deg, right_deg)             │
│  - setExpression(name: happy/sad/surprise/blink)   │
│  - setEyeBrightness(brightness)                    │
└─────────┬──────────────────────────────────────────┘
          │
┌─────────┴──────────────────────────────────────────┐
│              PCA9685 Driver                        │
│  - i2c_write(channel, pwm_value)                   │
│  - setPWMFreq(freq=50)                             │
│  - writeAll()                                       │
└─────────┬──────────────────────────────────────────┘
          │
┌─────────┴──────────────────────────────────────────┐
│         I2C Bus (Grove Port, GPIO 1/2)             │
│         PCA9685 @ I2C addr 0x40 (default)          │
└────────────────────────────────────────────────────┘
```

### Key Registers (PCA9685)

| Register | Address | Function |
|----------|---------|----------|
| MODE1 | 0x00 | Configuration (sleep, restart, auto-increment) |
| PRESCALE | 0xFE | PWM frequency prescaler |
| LED0_ON_L | 0x06 | CH0: ON time (low byte) |
| LED0_ON_H | 0x07 | CH0: ON time (high byte) |
| LED0_OFF_L | 0x08 | CH0: OFF time (low byte) |
| LED0_OFF_H | 0x09 | CH0: OFF time (high byte) |
| LED1_OFF_L | 0x0A | CH1: OFF time (low byte) |
| LED1_OFF_H | 0x0B | CH1: OFF time (high byte) |

### Servo Angle to PWM Calculation

```
For PCA9685 (12-bit resolution, 4096 counts):
  PWM_period = 1 / 50Hz = 20ms
  Count_per_ms = 4096 / 20ms ≈ 204.8 counts/ms
  
  For SG90 servo:
    0°   → 0.5ms pulse  → 102 counts (ON=0, OFF=102)
    90°  → 1.5ms pulse  → 307 counts (ON=0, OFF=307)
    180° → 2.5ms pulse  → 512 counts (ON=0, OFF=512)
  
  Formula: off_count = round(102 + (angle_deg / 180) * 410)
```

---

## 8. Pin Conflict Checklist

| Potential Conflict | Status | Mitigation |
|--------------------|--------|------------|
| GPIO 1/2 used for Grove I2C + standard I2C | ✅ Clear | PCA9685 is I2C — no conflict |
| GPIO 13 (Display RST) vs StackChan servo | ✅ Clear | Servos moved to PCA9685 via Grove |
| GPIO 14 (Mic DATA) vs StackChan servo | ✅ Clear | Servos moved to PCA9685 via Grove |
| GPIO 8/9 (Internal I2C) vs Grove I2C (1/2) | ✅ Clear | Separate I2C buses |
| Display SPI vs SD SPI | ⚠️ Note | Shared SPI bus (different CS). No conflict. |
| USB DP (GPIO 20) used as GPIO | ✅ Clear | Not used |
| GPIO 46 strapping pin | ✅ Clear | Not used |
| ADC2 + WiFi (if WiFi enabled) | ⚠️ Note | Apps 1-3 don't use WiFi or ADC. No conflict. |

---

## 9. Required External Components

| Component | Quantity | Purpose | Approx Cost |
|-----------|----------|---------|-------------|
| PCA9685 module | 1 | I2C servo driver | $3 |
| SG90 micro servo | 2 | StackChan eye movement | $4 |
| Grove-to-PCA9685 cable | 1 | Connection from Grove port | $2 |
| 5V power source (shared) | — | Via Core S3 USB or battery | Included |
| **Total BOM** | | | **~$9 + StackChan kit** |

---

## 10. Test Points and Bring-Up

1. **Verify I2C bus**: `i2cdetect` on GPIO 1/2 should show PCA9685 at 0x40
2. **Verify servo range**: Send OFF=102 → should go to 0°, OFF=512 → should go to 180°
3. **Verify IMU**: BMI270 on internal I2C (0x68) should produce accel readings
4. **Verify touch**: FT6336U register 0x02 (gesture ID) should update on touch
5. **Verify PDM mic**: ADC samples should show waveform on serial plotter
6. **Power test**: Measure total current at startup and during servo movement

---

*Prepared for the "M5Stack兩個產品互動" project — 3 interactive apps between M5Stack Core S3 and M5Stack StackChan.*
