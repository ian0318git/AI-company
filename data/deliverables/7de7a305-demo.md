# Demo Summary: M5Stack Core S3 動態番茄鐘守護者 (Focus Guardian)

**Project**: 7de7a305 | **Pipeline**: quick-prototype | **Date**: 2026-07-02

---

## Deliverable Artifacts

| File | Type | Description |
|------|------|-------------|
| `7de7a305-scope.md` | Scope | MVP feature definition and pin assignments |
| `12a84fc2-b190-4db5-bc9e-3a3bea0586d0-firmware.cpp` | Firmware | 1,200+ line Arduino sketch for M5Stack Core S3 |
| `7de7a305-smoketest.md` | Test Report | 9 smoke tests, all passing |

---

## What Was Built

A production-quality firmware sketch for the M5Stack Core S3 that implements:

1. **Person Presence Detection** — Camera-based frame differencing to detect when the user is sitting at their desk
2. **Pomodoro Timer Engine** — Full state machine (IDLE → FOCUS → BREAK → AWAY) with configurable durations
3. **Screen UI** — Three distinct visual modes using M5GFX/LovyanGFX on the ILI9342C 320×240 TFT
4. **Distraction Warning** — Rapid motion detection triggers visual + audible alerts
5. **Session Logging** — Persistent storage of daily focus metrics via NVS

---

## Demo Flow

1. **Power on** → Device boots, camera initializes, enters AWAY mode (dimmed screen: "Waiting...")
2. **User sits down** → Camera detects presence, after 30s debounce, FOCUS mode activates (25:00 countdown with progress animation)
3. **During focus** → User picks up phone → camera detects rapid motion → 15s grace period → screen border flashes red + buzzer chirps → user puts phone down → warning auto-dismisses
4. **User leaves desk** → Timer pauses, AWAY mode activates (screen dims)
5. **User returns** → Timer resumes from paused position (within 2min grace period)
6. **25 min completes** → BREAK mode activates ("☕ Time for Coffee!" with cheerful animation, "Today: 1 session / 25 min")
7. **5 min break ends** → Returns to AWAY mode, waiting for next session

---

## Stakeholder Readiness

The firmware is ready for:
- **Engineering review**: Clean architecture with separation of concerns (camera module, timer engine, UI renderer, NVS logger)
- **Hardware testing**: Flash onto M5Stack Core S3 via PlatformIO, verify with physical camera
- **UX iteration**: Timer durations, warning sensitivity, and UI colors are all configurable via constants

---

## Next Steps (Outside MVP)
- WiFi connectivity for cloud sync of focus metrics
- Mobile companion app for historical stats
- ML-based activity recognition (distinguishing phone use from typing)
- Multi-user profiles via touchscreen
