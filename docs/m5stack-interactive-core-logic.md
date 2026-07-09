# M5Stack Interactive — Core Business Logic Design

## Application 1: Motion Controller (CoreS3 → StackChan)

**CoreS3 (Controller):**
```
[BMI270 IMU] ──100Hz──→ [Orientation Engine] ──UART cmd 0x01──→ [StackChan]
                                                                    │
[Button A] ──→ Reset head position                                  │
[Button B] ──→ Toggle mode (absolute/relative)                  [Servo Controller]
[Button C] ──→ Calibrate                                          Body + Head
```

- Read IMU at 100Hz → compute roll/pitch/yaw via Madgwick filter
- Map roll → StackChan body servo (0°–180°)
- Map pitch → StackChan head servo (0°–180°)
- Display current orientation as 3D indicator on CoreS3 TFT

## Application 2: Sensor Data Visualizer (CoreS3 → StackChan)

**CoreS3 (Gateway):**
```
[IMU 100Hz] ──┐
[PDM Mic] ────┤──→ Sensor Fusion ──UART cmd 0x02──→ [StackChan]
[Touch] ──────┘                                          │
                                                    [SSD1306 Display]
                                                    Waveform / gauge view
```

- CoreS3 reads IMU + mic level + touch gestures
- Streams selected sensor at appropriate rate over UART
- StackChan renders real-time waveform (mic) or gauge (IMU)
- Toggle sensor source via CoreS3 touch

## Application 3: Interactive Game (Two-Player)

**CoreS3 (Controller):**
```
[IMU Tilt] ──→ Directional input
[Button A] ──→ Action/Jump
[Button B] ──→ Special
[Button C] ──→ Pause
     │
     └──UART cmd 0x03──→ [StackChan]
                              │
                         [Game Engine]
                         [SSD1306 Display]
                         Player character + obstacles
```

- Pong-style or side-scroller rendered on StackChan
- CoreS3 serves as physical game controller via IMU tilt
- Score displayed on both devices
- Round-trip latency target: <50ms (UART + rendering)

## State Machine (CoreS3)

```
          ┌─────────┐
          │  IDLE   │ ←── Boot / Reset
          └────┬────┘
     ┌─────────┼──────────┐
     ▼         ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│MOTION  │ │VISUAL  │ │GAME    │
│CTRL    │ │IZER    │ │CTRL    │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────────┼──────────┘
               ▼
          ┌─────────┐
          │  SLEEP  │ ←── Inactivity timeout
          └─────────┘
```

State transitions via touch menu or button long-press.

## Error Handling & Watchdog

- **UART timeout**: 500ms → retry 3× → fallback to standalone mode
- **IMU init failure**: retry 3× with 100ms delay → display error code on screen
- **Frame CRC error**: drop frame, request retransmit via cmd 0xFF keepalive
- **Task watchdog**: 1s SW watchdog in each FreeRTOS task → panic reset on hang
- **Low battery**: CoreS3 reports via cmd 0x10 → StackChan flashes LED
