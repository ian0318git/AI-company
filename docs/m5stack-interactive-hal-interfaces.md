# M5Stack Interactive — HAL Interface Definitions

## 1. UART Communication HAL

```cpp
// IUartComm.h — Abstract UART transport
class IUartComm {
public:
    virtual ~IUartComm() = default;
    virtual bool begin(uint32_t baud = 115200) = 0;
    virtual bool sendFrame(uint8_t cmd, const uint8_t* payload, size_t len) = 0;
    virtual int  receiveFrame(uint8_t* buf, size_t maxLen, uint32_t timeoutMs) = 0;
    virtual void flush() = 0;
};

// Frame format: [0xAA] [len] [cmd] [payload...] [xor_checksum]
struct Frame {
    uint8_t cmd;
    uint8_t payload[64];
    uint8_t len;
};
```

## 2. IMU Sensor HAL

```cpp
// IImuSensor.h — BMI270 abstraction
class IImuSensor {
public:
    struct ImuData {
        float ax, ay, az;    // Accelerometer (g)
        float gx, gy, gz;    // Gyroscope (°/s)
        float roll, pitch, yaw;  // Euler angles (°)
    };
    virtual ~IImuSensor() = default;
    virtual bool begin(TwoWire& wire) = 0;
    virtual bool calibrate() = 0;
    virtual bool read(ImuData& out) = 0;
    virtual bool isMotionDetected(float threshold = 0.5f) = 0;
};
```

## 3. Display HAL

```cpp
// IDisplay.h — Abstract display for both devices
class IDisplay {
public:
    virtual ~IDisplay() = default;
    virtual bool begin() = 0;
    virtual void clear(uint16_t color = 0x0000) = 0;
    virtual void drawText(int x, int y, const char* text, uint16_t color = 0xFFFF) = 0;
    virtual void drawRect(int x, int y, int w, int h, uint16_t color) = 0;
    virtual void fillRect(int x, int y, int w, int h, uint16_t color) = 0;
    virtual void drawCircle(int cx, int cy, int r, uint16_t color) = 0;
    virtual void drawLine(int x0, int y0, int x1, int y1, uint16_t color) = 0;
    virtual void update() = 0;
};
```

## 4. Servo HAL (StackChan)

```cpp
// IServoController.h — Servo motor abstraction
class IServoController {
public:
    struct ServoAngles {
        uint8_t body;  // 0–180°
        uint8_t head;  // 0–180°
    };
    virtual ~IServoController() = default;
    virtual bool begin(uint8_t pinBody, uint8_t pinHead) = 0;
    virtual bool setAngles(const ServoAngles& angles) = 0;
    virtual bool setAngle(const char* name, uint8_t angle) = 0;
    virtual ServoAngles getCurrentAngles() = 0;
};
```

## 5. Audio HAL

```cpp
// IAudioInput.h — PDM microphone abstraction (CoreS3)
class IAudioInput {
public:
    virtual ~IAudioInput() = default;
    virtual bool begin(int dataPin, int clkPin) = 0;
    virtual bool readSamples(int16_t* buf, size_t count) = 0;
    virtual float getLevel() = 0;  // 0.0–1.0
};

// IAudioOutput.h — Speaker abstraction (CoreS3)
class IAudioOutput {
public:
    virtual ~IAudioOutput() = default;
    virtual bool begin(int dacPin) = 0;
    virtual bool playTone(uint16_t freq, uint16_t durationMs) = 0;
    virtual bool playSamples(const int16_t* buf, size_t count) = 0;
};
```

## 6. Button HAL

```cpp
// IButtonInput.h — Physical button abstraction
class IButtonInput {
public:
    enum Button { A = 0, B, C, CUSTOM };
    virtual ~IButtonInput() = default;
    virtual bool begin() = 0;
    virtual bool isPressed(Button btn) = 0;
    virtual bool wasPressed(Button btn) = 0;  // Edge-triggered
    virtual uint8_t getPressedMask() = 0;     // Bitmask of all pressed
};
```

## 7. Wire / I2C Bus Mapping

| Device | Bus | CoreS3 Pins | StackChan Pins |
|--------|-----|-------------|----------------|
| BMI270 + BMM150 | Wire1 | SDA: 21, SCL: 22 | — |
| FT6336U Touch | Wire1 | SDA: 21, SCL: 22 | — |
| SSD1306 Display | Wire | — | SDA: 21, SCL: 22 |

## 8. FreeRTOS Task Structure

```
core0: ┌─────────────────────────────────────────────┐
       │ UART Comm Task  (stack: 4096, pri: 3)       │
       │   - Receive frames, dispatch to app queue    │
       └─────────────────────────────────────────────┘
core1: ┌─────────────────────────────────────────────┐
       │ Sensor Task    (stack: 2048, pri: 2)        │
       │   - Read IMU @ 100Hz, push to queue         │
       ├─────────────────────────────────────────────┤
       │ UI Task        (stack: 4096, pri: 1)        │
       │   - Update display @ 30 FPS                 │
       ├─────────────────────────────────────────────┤
       │ App Logic Task (stack: 4096, pri: 2)        │
       │   - State machine for 3 app modes           │
       └─────────────────────────────────────────────┘
```
