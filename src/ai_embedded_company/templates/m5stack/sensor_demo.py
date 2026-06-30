"""M5Stack Core S3 — Sensor Demo Project Template.

A complete PlatformIO project for reading sensor data and displaying on LCD.

Usage:
  - Copy this directory as a new project
  - Modify platformio.ini for your specific board
  - This template includes: I2C sensor init, LCD display, basic UI
"""

PLATFORMIO_INI = """[env:m5stack-cores3]
platform = espressif32
board = m5stack-cores3
framework = arduino
monitor_speed = 115200
upload_speed = 921600
board_build.flash_mode = qio
board_build.partitions = default_8MB.csv
build_flags =
    -D CORE_DEBUG_LEVEL=0
    -D BOARD_HAS_PSRAM
    -mfix-esp32-psram-cache-issue
lib_deps =
    m5stack/M5Unified @ ^0.2.0
    m5stack/M5GFX @ ^0.2.0
"""

MAIN_CPP = """#include <M5Unified.h>
#include <M5GFX.h>

// ============================================================
// M5Stack Core S3 — Sensor Demo
// Reads from I2C sensor (Grove port) and displays on LCD
// ============================================================

static M5GFX display;
static M5Canvas canvas(&display);

// Grove I2C port: SDA=GPIO 1, SCL=GPIO 2
// Replace with your sensor's init and read functions
float readSensorValue() {
    // TODO: Replace with actual sensor reading
    // Example for BME280:
    //   float temp = bme.readTemperature();
    //   return temp;
    return 25.0f + (millis() % 1000) / 1000.0f;  // placeholder
}

void setup() {
    auto cfg = M5.config();
    M5.begin(cfg);

    display.begin();
    display.setRotation(1);
    display.setBrightness(128);

    canvas.setColorDepth(8);
    canvas.createSprite(display.width(), display.height());

    M5.Log.println("M5Stack Core S3 — Sensor Demo Started");
}

void loop() {
    M5.update();

    float value = readSensorValue();

    canvas.clear(TFT_BLACK);

    // Title
    canvas.setTextColor(TFT_WHITE);
    canvas.setTextSize(2);
    canvas.setCursor(10, 10);
    canvas.printf("Sensor Demo");

    // Value (large)
    canvas.setTextSize(4);
    canvas.setTextColor(TFT_CYAN);
    canvas.setCursor(10, 60);
    canvas.printf("%.1f C", value);

    // Status bar
    canvas.setTextSize(1);
    canvas.setTextColor(TFT_DARKGREY);
    canvas.setCursor(10, display.height() - 20);
    canvas.printf("M5Stack Core S3 | ESP32-S3");

    canvas.pushSprite(0, 0);
    delay(1000);
}
"""

README_MD = """# M5Stack Core S3 — Sensor Demo

Reads from an I2C sensor connected to the Grove port and displays values on the LCD.

## Hardware
- **Board**: M5Stack Core S3 (ESP32-S3)
- **Sensor**: Connect any I2C sensor to Grove Port A (SDA=GPIO 1, SCL=GPIO 2)

## Build & Flash

```bash
# Install PlatformIO if not already: pip install platformio
platformio run
platformio run --target upload
platformio device monitor
```

## Modifying for Your Sensor
1. Install the sensor library: add to `lib_deps` in `platformio.ini`
2. Replace `readSensorValue()` with your sensor's read function
3. Update display layout for your specific data
"""
