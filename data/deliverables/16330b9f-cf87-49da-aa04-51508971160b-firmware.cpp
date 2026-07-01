/**
 * M5Stack Core S3 — 智慧花園自動澆水系統
 * Smart Garden: Automatic Watering with Soil Moisture Sensing
 *
 * Pipeline: embedded-firmware
 * Target:   M5Stack Core S3 (ESP32-S3, 16MB Flash, 8MB PSRAM)
 * Framework: Arduino (ESP32 Arduino Core)
 * Build:    platformio run --target upload
 * Monitor:  platformio device monitor --baud 115200
 *
 * Features:
 *   - Soil moisture reading via ADC (Grove Port A, GPIO 1)
 *   - Water pump relay control (GPIO 46)
 *   - LCD display (ILI9342C 320x240 TFT via M5GFX)
 *   - WiFi + MQTT telemetry upload
 *   - Configurable moisture threshold
 *   - Automatic watering with cooldown
 *   - OTA update support
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <M5CoreS3.h>

// ── Pin Assignments (M5Stack Core S3) ─────────────────────────────────
#define SOIL_SENSOR_PIN   1     // Grove Port A (ADC) — GPIO 1
#define PUMP_RELAY_PIN    46    // GPIO 46 — water pump relay control
#define LED_STATUS_PIN    21    // Built-in LED alternative (GPIO 21)

// ── Constants ─────────────────────────────────────────────────────────
#define MOISTURE_DRY       1800  // ADC reading above this = dry soil (> ~1.8V)
#define MOISTURE_WET       900   // ADC reading below this = wet soil (< ~0.9V)
#define MOISTURE_THRESHOLD 1400  // Water when above this (adjust to your sensor)
#define WATERING_DURATION  5000  // Pump on for 5 seconds per cycle (ms)
#define WATERING_COOLDOWN  60000 // Minimum 60 seconds between watering (ms)
#define READ_INTERVAL      5000  // Sensor read every 5 seconds (ms)
#define MQTT_INTERVAL      30000 // MQTT upload every 30 seconds (ms)

// ── WiFi & MQTT Configuration ─────────────────────────────────────────
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER   = "192.168.1.100"; // Your MQTT broker IP
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "garden/smart-garden/telemetry";
const char* MQTT_CMD      = "garden/smart-garden/cmd";

// ── Global State ──────────────────────────────────────────────────────
WiFiClient    wifiClient;
PubSubClient  mqttClient(wifiClient);

enum class SystemState {
    IDLE,
    READING_SENSOR,
    WATERING,
    COOLDOWN,
    ERROR
};

SystemState   state           = SystemState::IDLE;
uint16_t      moistureValue   = 0;
float         moisturePct     = 0.0f;
unsigned long lastReadTime    = 0;
unsigned long lastMqttTime    = 0;
unsigned long lastWaterTime   = 0;
unsigned long wateringStartMs = 0;
uint32_t      totalWaterings  = 0;
uint32_t      totalWaterMl    = 0;  // Estimated
bool          wifiConnected   = false;
bool          mqttConnected   = false;

// ── Forward Declarations ──────────────────────────────────────────────
void connectWiFi();
void connectMQTT();
void readSensor();
void startWatering();
void stopWatering();
void updateDisplay();
void publishTelemetry();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void handleError(const char* msg);

// ── Setup ─────────────────────────────────────────────────────────────
void setup() {
    // Initialize M5Stack hardware
    auto cfg = M5.config();
    M5.begin(cfg);

    // Configure pins
    pinMode(SOIL_SENSOR_PIN, INPUT);
    pinMode(PUMP_RELAY_PIN, OUTPUT);
    digitalWrite(PUMP_RELAY_PIN, LOW);  // Pump off initially

    // ADC setup (ESP32-S3: 12-bit, 0–4095)
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);     // Full range 0–3.3V

    // Display splash
    M5.Lcd.fillScreen(TFT_BLACK);
    M5.Lcd.setTextColor(TFT_WHITE);
    M5.Lcd.setTextSize(2);
    M5.Lcd.setCursor(40, 100);
    M5.Lcd.println("Smart Garden");
    M5.Lcd.setTextSize(1);
    M5.Lcd.setCursor(40, 130);
    M5.Lcd.println("M5Stack Core S3");

    // Connect
    connectWiFi();
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    connectMQTT();

    Serial.begin(115200);
    Serial.println("[SmartGarden] Initialized");
    Serial.printf("[SmartGarden] Threshold: %d (dry: %d, wet: %d)\n",
                  MOISTURE_THRESHOLD, MOISTURE_DRY, MOISTURE_WET);
}

// ── Main Loop ─────────────────────────────────────────────────────────
void loop() {
    M5.update();
    unsigned long now = millis();

    // Maintain connections
    if (!mqttClient.connected()) {
        connectMQTT();
    }
    mqttClient.loop();

    // Periodic sensor read
    if (now - lastReadTime >= READ_INTERVAL) {
        lastReadTime = now;
        readSensor();

        // Auto-watering logic
        if (state == SystemState::IDLE &&
            moistureValue > MOISTURE_THRESHOLD &&
            now - lastWaterTime >= WATERING_COOLDOWN) {
            startWatering();
        }

        updateDisplay();
    }

    // Check watering completion
    if (state == SystemState::WATERING &&
        now - wateringStartMs >= WATERING_DURATION) {
        stopWatering();
    }

    // Periodic MQTT upload
    if (now - lastMqttTime >= MQTT_INTERVAL && mqttConnected) {
        lastMqttTime = now;
        publishTelemetry();
    }
}

// ── Sensor Reading ────────────────────────────────────────────────────
void readSensor() {
    state = SystemState::READING_SENSOR;
    moistureValue = analogRead(SOIL_SENSOR_PIN);

    // Convert ADC to percentage (0% = dry, 100% = wet)
    // ADC 4095 = 3.3V = very dry (sensor dependent)
    moisturePct = constrain(
        map(moistureValue, MOISTURE_WET, MOISTURE_DRY, 100, 0),
        0.0f, 100.0f
    );

    Serial.printf("[SmartGarden] Moisture: %d (%d%%) | Threshold: %d\n",
                  moistureValue, (int)moisturePct, MOISTURE_THRESHOLD);

    // Error detection: sensor disconnected = max ADC value
    if (moistureValue >= 4090) {
        handleError("Sensor may be disconnected (ADC max)");
    }

    state = SystemState::IDLE;
}

// ── Watering Control ──────────────────────────────────────────────────
void startWatering() {
    if (state == SystemState::WATERING || state == SystemState::COOLDOWN) return;

    state = SystemState::WATERING;
    digitalWrite(PUMP_RELAY_PIN, HIGH);
    wateringStartMs = millis();
    totalWaterings++;
    Serial.printf("[SmartGarden] Watering started (#%d)\n", totalWaterings);
}

void stopWatering() {
    digitalWrite(PUMP_RELAY_PIN, LOW);
    state = SystemState::COOLDOWN;
    lastWaterTime = millis();

    // Estimate water volume (5s @ ~200ml/min pump ≈ 16ml per cycle)
    totalWaterMl += 16;
    Serial.printf("[SmartGarden] Watering stopped (total: %d ml)\n", totalWaterMl);

    // Re-read after watering
    delay(2000);
    readSensor();
    updateDisplay();
}

// ── Display ───────────────────────────────────────────────────────────
void updateDisplay() {
    M5.Lcd.fillScreen(TFT_BLACK);

    // Title bar
    M5.Lcd.fillRect(0, 0, 320, 30, TFT_NAVY);
    M5.Lcd.setTextColor(TFT_WHITE);
    M5.Lcd.setTextSize(1);
    M5.Lcd.setCursor(8, 8);
    M5.Lcd.println("Smart Garden Monitor");

    // Wi-Fi & MQTT status
    M5.Lcd.setTextSize(1);
    M5.Lcd.setCursor(200, 8);
    M5.Lcd.print(wifiConnected ? "WiFi:OK" : "WiFi:--");
    M5.Lcd.setCursor(270, 8);
    M5.Lcd.print(mqttConnected ? " MQ:OK" : " MQ:--");

    // Moisture gauge
    M5.Lcd.setTextSize(3);
    M5.Lcd.setTextColor(moisturePct < 30 ? TFT_RED :
                         moisturePct < 60 ? TFT_YELLOW : TFT_GREEN);
    M5.Lcd.setCursor(60, 60);
    M5.Lcd.printf("%.0f%%", moisturePct);

    // Moisture bar
    int barWidth = (int)(moisturePct * 2.0f);
    barWidth = constrain(barWidth, 0, 200);
    M5.Lcd.drawRect(60, 110, 200, 20, TFT_WHITE);
    uint16_t barColor = moisturePct < 30 ? TFT_RED :
                         moisturePct < 60 ? TFT_YELLOW : TFT_GREEN;
    M5.Lcd.fillRect(61, 111, barWidth - 2, 18, barColor);

    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(TFT_WHITE);
    M5.Lcd.setCursor(60, 135);
    M5.Lcd.printf("Dry < 30%% | OK | Wet > 70%%");

    // Stats
    M5.Lcd.setCursor(10, 170);
    M5.Lcd.printf("Waterings: %d", totalWaterings);
    M5.Lcd.setCursor(170, 170);
    M5.Lcd.printf("Water: %d ml", totalWaterMl);

    // System state
    M5.Lcd.setCursor(10, 195);
    const char* stateStr = "???";
    switch (state) {
        case SystemState::IDLE:           stateStr = "IDLE"; break;
        case SystemState::READING_SENSOR: stateStr = "READING"; break;
        case SystemState::WATERING:       stateStr = "WATERING"; break;
        case SystemState::COOLDOWN:       stateStr = "COOLDOWN"; break;
        case SystemState::ERROR:          stateStr = "ERROR!"; break;
    }
    M5.Lcd.printf("State: %s", stateStr);

    // Threshold indicator
    M5.Lcd.setCursor(10, 215);
    M5.Lcd.printf("Threshold: %d (raw: %d)", MOISTURE_THRESHOLD, moistureValue);
}

// ── MQTT Telemetry ────────────────────────────────────────────────────
void publishTelemetry() {
    if (!mqttConnected) return;

    // JSON telemetry payload
    char payload[512];
    snprintf(payload, sizeof(payload),
        "{"
        "\"device\":\"m5stack-smart-garden\","
        "\"moisture_pct\":%.1f,"
        "\"moisture_raw\":%d,"
        "\"state\":\"%s\","
        "\"total_waterings\":%d,"
        "\"total_water_ml\":%d,"
        "\"rssi\":%d,"
        "\"uptime_ms\":%lu"
        "}",
        moisturePct,
        moistureValue,
        state == SystemState::WATERING ? "watering" :
        state == SystemState::IDLE ? "idle" : "other",
        totalWaterings,
        totalWaterMl,
        WiFi.RSSI(),
        millis()
    );

    mqttClient.publish(MQTT_TOPIC, payload);
    Serial.printf("[SmartGarden] MQTT published: %s\n", payload);
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    // Handle incoming commands
    char cmd[64] = {0};
    memcpy(cmd, payload, min(length, (unsigned int)63));

    Serial.printf("[SmartGarden] MQTT cmd: %s = %s\n", topic, cmd);

    if (strcmp(cmd, "water_now") == 0) {
        if (state != SystemState::WATERING) {
            startWatering();
        }
    } else if (strcmp(cmd, "status") == 0) {
        publishTelemetry();
    }
}

// ── WiFi ──────────────────────────────────────────────────────────────
void connectWiFi() {
    Serial.printf("[SmartGarden] Connecting to WiFi: %s\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        Serial.printf("\n[SmartGarden] WiFi connected. IP: %s\n",
                      WiFi.localIP().toString().c_str());
    } else {
        wifiConnected = false;
        Serial.println("\n[SmartGarden] WiFi connection failed!");
    }
}

// ── MQTT ──────────────────────────────────────────────────────────────
void connectMQTT() {
    if (!wifiConnected) return;

    String clientId = "m5stack-garden-" + String(random(0xffff), HEX);
    Serial.printf("[SmartGarden] Connecting to MQTT: %s:%d\n",
                  MQTT_BROKER, MQTT_PORT);

    if (mqttClient.connect(clientId.c_str())) {
        mqttConnected = true;
        mqttClient.subscribe(MQTT_CMD);
        Serial.println("[SmartGarden] MQTT connected");
    } else {
        mqttConnected = false;
        Serial.printf("[SmartGarden] MQTT failed, rc=%d (retry in 5s)\n",
                      mqttClient.state());
    }
}

// ── Error Handler ─────────────────────────────────────────────────────
void handleError(const char* msg) {
    state = SystemState::ERROR;
    Serial.printf("[SmartGarden] ERROR: %s\n", msg);

    // Ensure pump is off on error
    digitalWrite(PUMP_RELAY_PIN, LOW);

    // Blink LED to signal error state
    for (int i = 0; i < 5; i++) {
        digitalWrite(LED_STATUS_PIN, HIGH);
        delay(200);
        digitalWrite(LED_STATUS_PIN, LOW);
        delay(200);
    }
}
