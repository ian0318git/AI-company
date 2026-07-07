# MVP Scope: M5Stack Core S3 動態番茄鐘守護者 (Focus Guardian)

**Pipeline**: quick-prototype | **Board**: M5Stack Core S3 (ESP32-S3) | **Date**: 2026-07-02

---

## Core MVP Features

### 1. Person Presence Detection
- Use Core S3 built-in camera (GC0308) with basic frame capture
- Simple motion/change detection algorithm (frame diffing) — no ML required for MVP
- Detect: "person sitting at desk" vs "desk empty"
- Sampling rate: 1 frame every 2 seconds (balance between responsiveness and CPU load)

### 2. Pomodoro Timer Engine
- 25-minute focus session (configurable: 15/25/45 min)
- 5-minute short break (configurable: 3/5/10 min)
- Auto-start when presence detected for >30 seconds (debounce)
- Pause timer when person leaves desk; resume on return (with 2-min grace period)

### 3. Screen UI (M5GFX / LovyanGFX)
- **Focus mode**: Large countdown timer, minimalist design, subtle progress animation
- **Break mode**: "Time for coffee!" message with cheerful icon/animation
- **Away mode**: Dimmed screen with "Waiting..." indicator
- Screen: ILI9342C 320×240 TFT

### 4. Distraction Warning
- Detect: rapid motion (phone pickup) or person leaving frame
- Warning: screen flash + optional buzzer/vibration
- Grace period: 15 seconds before warning triggers
- Auto-dismiss when person returns to focus position

### 5. Session Logging
- Store session count and total focus minutes in NVS (non-volatile storage)
- Display "Today: 4 sessions / 100 min" on break screen

---

## MVP Out of Scope
- WiFi/cloud sync
- Mobile app companion
- Advanced AI-based activity recognition
- Multi-user profiles
- Heart rate/health sensor integration
- External display or smartwatch integration

---

## Pin Assignments (Tentative)
| Peripheral | Pin | Notes |
|-----------|-----|-------|
| TFT (SPI) | Default M5Stack SPI | Built-in, use M5GFX defaults |
| Camera | XCLK=15, PCLK=13, VSYNC=6, HREF=7, DATA=11-8 | GC0308 built-in |
| Buzzer | GPIO 2 | Optional, for audio alerts |
| Touch | I2C SDA=12, SCL=11 | FT6336U built-in |

## Success Criteria
1. Timer starts automatically within 30s of sitting at desk
2. Timer pauses within 5s of leaving desk
3. Distraction warning triggers on phone-check motion
4. Break reminder displays after 25-min session
5. Runs stably for 8+ hours without reboot
