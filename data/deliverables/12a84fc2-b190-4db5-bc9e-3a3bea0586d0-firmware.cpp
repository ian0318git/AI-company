/**
 * Focus Guardian — M5Stack Core S3 Dynamic Pomodoro Timer
 * ========================================================
 * A production-quality Arduino/PlatformIO sketch for the M5Stack Core S3
 * (ESP32-S3) that implements a "Focus Guardian" pomodoro timer with:
 *
 *   • Person presence detection via built-in GC0308 camera (frame diffing)
 *   • Configurable pomodoro timer engine (focus / break / away states)
 *   • M5GFX / LovyanGFX UI on the 320×240 ILI9342C TFT
 *   • Distraction warning (rapid motion → screen flash + buzzer)
 *   • Session logging to NVS (non-volatile storage)
 *
 * Hardware:       M5Stack Core S3 (ESP32-S3, 16 MB Flash, 8 MB PSRAM)
 * Camera:         GC0308 (built-in, 0.3 MP)
 * Display:        ILI9342C 320×240 SPI TFT (via M5GFX)
 * Buzzer:         GPIO 2  (active-low or active-high; see schematic)
 * Touch:          FT6336U on I2C (SDA=12, SCL=11) — used for config
 *
 * Framework:      Arduino (ESP32-S3) / PlatformIO
 *
 * License:        MIT
 */

// =============================================================================
// 1. INCLUDES
// =============================================================================
#include <Arduino.h>
#include <M5CoreS3.h>              // Board init, LCD, I2C touch, power
#include <nvs_flash.h>             // NVS partition init
#include <nvs.h>                   // NVS read/write API
#include <esp_camera.h>            // ESP32 camera driver
#include <esp_timer.h>             // High-resolution timer for frame pacing
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>

// LovyanGFX / M5GFX is already available through M5CoreS3.h:
//   M5.Lcd  →  LGFX_Device derived class driving the ILI9342C

// =============================================================================
// 2. PIN ASSIGNMENTS (as specified by scope)
// =============================================================================
// Camera pins for the built-in GC0308 on Core S3
#define CAM_XCLK    15
#define CAM_PCLK    13
#define CAM_VSYNC   6
#define CAM_HREF    7
#define CAM_DATA_0  11
#define CAM_DATA_1  10
#define CAM_DATA_2  9
#define CAM_DATA_3  8
// DATA pins 4-7 are unused on GC0308 (8-bit parallel, but we only use D0-D3
// for GC0308 which is a 4-bit parallel interface; however the esp32-camera
// driver expects a contiguous pin range. The GC0308 on Core S3 is wired as
// a 8-bit parallel camera but only the lower 4 bits connect. We set pin 4-7
// to -1 to tell the driver they are unused.)
#define CAM_PWDN    -1   // No power-down pin
#define CAM_RESET   -1   // No reset pin
#define CAM_XCLK_FREQ  10000000  // 10 MHz — conservative for GC0308

// Buzzer
#define PIN_BUZZER  2

// Touch I2C (used by M5.Touch internally, defined here for documentation)
#define TOUCH_SDA   12
#define TOUCH_SCL   11

// I2C for touch (M5CoreS3 initialises it automatically; we keep these for
// reference)
#define I2C_FREQ    400000

// =============================================================================
// 3. COMPILE-TIME CONSTANTS
// =============================================================================
// Timer durations (milliseconds)
static constexpr unsigned long FOCUS_DURATION_MS      = 25UL * 60UL * 1000UL;  // 25 min
static constexpr unsigned long BREAK_DURATION_MS       = 5UL  * 60UL * 1000UL;  //  5 min
static constexpr unsigned long LONG_BREAK_DURATION_MS  = 10UL * 60UL * 1000UL;  // 10 min (optional)

// Configurable presets (users can cycle through these via touch)
// Index: 0 = short, 1 = medium, 2 = long
static constexpr unsigned long FOCUS_PRESETS_MS[3] = {
    15UL * 60UL * 1000UL,   // 15 min
    25UL * 60UL * 1000UL,   // 25 min (default)
    45UL * 60UL * 1000UL    // 45 min
};
static constexpr unsigned long BREAK_PRESETS_MS[3] = {
    3UL  * 60UL * 1000UL,   //  3 min
    5UL  * 60UL * 1000UL,   //  5 min (default)
    10UL * 60UL * 1000UL    // 10 min
};

// Presence detection
static constexpr int      PRESENCE_DEBOUNCE_MS      = 30 * 1000;  // 30 s before auto-start
static constexpr int      AWAY_GRACE_PERIOD_MS      = 2  * 60 * 1000;  // 2 min grace before pause
static constexpr int      DISTRACTION_GRACE_MS      = 15 * 1000;      // 15 s grace before warning
static constexpr int      CAMERA_INTERVAL_MS        = 2  * 1000;      // 1 frame / 2 s
static constexpr float    MOTION_THRESHOLD          = 15.0f;    // % changed pixels for motion
static constexpr float    PRESENCE_THRESHOLD        = 3.0f;     // % changed pixels = presence
static constexpr float    AWAY_THRESHOLD            = 0.8f;     // % changed = desk empty

// Frame dimensions (GC0308 VGA)
static constexpr int      FRAME_WIDTH  = 320;   // VGA
static constexpr int      FRAME_HEIGHT = 240;   // VGA
static constexpr int      FRAME_PIXELS = FRAME_WIDTH * FRAME_HEIGHT;

// Down-sampling factor for diff calculation (balance accuracy vs. speed)
// We sample every 4th pixel in each dimension → 80×60 = 4800 pixels
static constexpr int      SAMPLE_STEP = 4;
static constexpr int      SAMPLE_COLS = FRAME_WIDTH  / SAMPLE_STEP;  // 80
static constexpr int      SAMPLE_ROWS = FRAME_HEIGHT / SAMPLE_STEP;  // 60
static constexpr int      SAMPLE_PIXELS = SAMPLE_COLS * SAMPLE_ROWS;

// NVS keys
static constexpr char     NVS_NAMESPACE[]     = "focus_guard";
static constexpr char     NVS_KEY_SESSION_CNT[] = "session_cnt";
static constexpr char     NVS_KEY_TOTAL_MIN[]   = "total_min";

// UI constants
static constexpr int      SCREEN_WIDTH  = 320;
static constexpr int      SCREEN_HEIGHT = 240;
static constexpr uint16_t COLOR_BG       = 0x0000;  // Black
static constexpr uint16_t COLOR_FOCUS    = 0x2B12;  // Deep teal-green
static constexpr uint16_t COLOR_BREAK    = 0xFBE4;  // Warm coral
static constexpr uint16_t COLOR_AWAY     = 0x3186;  // Dim grey
static constexpr uint16_t COLOR_WARN     = 0xF800;  // Red
static constexpr uint16_t COLOR_WHITE    = 0xFFFF;
static constexpr uint16_t COLOR_DIM      = 0x2108;  // Dark grey for "waiting"

// Task priorities / stack
static constexpr int      CAMERA_TASK_PRIO  = 5;
static constexpr int      CAMERA_TASK_STACK = 8192;
static constexpr int      UI_TASK_PRIO      = 4;
static constexpr int      UI_TASK_STACK     = 4096;

// =============================================================================
// 4. STATE MACHINE
// =============================================================================
enum class PomodoroState : uint8_t {
    IDLE,               // No person detected, waiting
    FOCUS,              // Active focus session
    BREAK,              // Break time
    AWAY,               // Person left desk (timer paused)
    DISTRACTION_WARN    // Rapid motion detected — flashing warning
};

static const char* stateName(PomodoroState s) {
    switch (s) {
        case PomodoroState::IDLE:             return "IDLE";
        case PomodoroState::FOCUS:            return "FOCUS";
        case PomodoroState::BREAK:            return "BREAK";
        case PomodoroState::AWAY:             return "AWAY";
        case PomodoroState::DISTRACTION_WARN: return "DISTRACTION";
        default:                              return "???";
    }
}

// =============================================================================
// 5. CONFIGURATION STRUCT
// =============================================================================
struct FocusConfig {
    unsigned long focusDurationMs;
    unsigned long breakDurationMs;
    uint8_t       focusPresetIndex;   // 0, 1, 2
    uint8_t       breakPresetIndex;
    bool          buzzerEnabled;
    uint8_t       buzzerVolume;       // 0-100

    // Factory defaults
    static FocusConfig defaults() {
        return FocusConfig{
            .focusDurationMs   = FOCUS_DURATION_MS,
            .breakDurationMs   = BREAK_DURATION_MS,
            .focusPresetIndex  = 1,   // 25 min
            .breakPresetIndex  = 1,   //  5 min
            .buzzerEnabled     = true,
            .buzzerVolume      = 50
        };
    }
};

// =============================================================================
// 6. NVS MANAGER
// =============================================================================
/**
 * Thread-safe (single-threaded by FreeRTOS task isolation) wrapper around
 * the ESP-IDF NVS API for persisting session statistics.
 */
class NvsManager {
public:
    NvsManager() : handle_(nullptr), initOk_(false) {}

    ~NvsManager() {
        if (handle_) {
            nvs_close(handle_);
        }
    }

    /** Initialise the NVS handle. Must be called once before any read/write. */
    bool begin() {
        esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle_);
        if (err == ESP_ERR_NVS_NOT_FOUND) {
            // First boot: initialise the namespace
            err = nvs_flash_init_partition("nvs");
            if (err != ESP_OK) {
                // NVS flash may need to be erased if layout changed
                if (err == ESP_ERR_NVS_NO_FREE_PAGES ||
                    err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
                    esp_err_t erase = nvs_flash_erase_partition("nvs");
                    if (erase != ESP_OK) {
                        log_e("NVS erase failed: %s", esp_err_to_name(erase));
                        return false;
                    }
                    err = nvs_flash_init_partition("nvs");
                }
                if (err != ESP_OK) {
                    log_e("NVS init failed: %s", esp_err_to_name(err));
                    return false;
                }
            }
            err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle_);
        }
        if (err != ESP_OK) {
            log_e("NVS open failed: %s", esp_err_to_name(err));
            return false;
        }
        initOk_ = true;
        log_i("NVS initialised, namespace=%s", NVS_NAMESPACE);
        return true;
    }

    /** Read session count. Returns 0 on first boot or error. */
    uint32_t readSessionCount() {
        if (!initOk_ || !handle_) return 0;
        uint32_t val = 0;
        esp_err_t err = nvs_get_u32(handle_, NVS_KEY_SESSION_CNT, &val);
        if (err != ESP_OK && err != ESP_ERR_NVS_NOT_FOUND) {
            log_w("NVS read session_cnt failed: %s", esp_err_to_name(err));
        }
        return val;
    }

    /** Write session count. */
    bool writeSessionCount(uint32_t count) {
        return writeU32(NVS_KEY_SESSION_CNT, count);
    }

    /** Read total focus minutes. */
    uint32_t readTotalMinutes() {
        if (!initOk_ || !handle_) return 0;
        uint32_t val = 0;
        esp_err_t err = nvs_get_u32(handle_, NVS_KEY_TOTAL_MIN, &val);
        if (err != ESP_OK && err != ESP_ERR_NVS_NOT_FOUND) {
            log_w("NVS read total_min failed: %s", esp_err_to_name(err));
        }
        return val;
    }

    /** Write total focus minutes. */
    bool writeTotalMinutes(uint32_t minutes) {
        return writeU32(NVS_KEY_TOTAL_MIN, minutes);
    }

    /** Commit pending writes to flash. Call periodically after writes. */
    bool commit() {
        if (!initOk_ || !handle_) return false;
        esp_err_t err = nvs_commit(handle_);
        if (err != ESP_OK) {
            log_e("NVS commit failed: %s", esp_err_to_name(err));
            return false;
        }
        return true;
    }

private:
    nvs_handle_t handle_;
    bool         initOk_;

    bool writeU32(const char* key, uint32_t value) {
        if (!initOk_ || !handle_) return false;
        esp_err_t err = nvs_set_u32(handle_, key, value);
        if (err != ESP_OK) {
            log_e("NVS write %s failed: %s", key, esp_err_to_name(err));
            return false;
        }
        return true;
    }
};

// =============================================================================
// 7. CAMERA MANAGER
// =============================================================================
/**
 * Manages the GC0308 camera via the esp32-camera driver.
 *
 * Provides:
 *   - Initialisation with pin mapping
 *   - Frame capture at a controlled interval
 *   - Frame-differencing for presence / motion detection
 *
 * Thread safety: all public methods must be called from the same task
 * (or protected by a mutex if called from multiple tasks).
 */
class CameraManager {
public:
    CameraManager()
        : initOk_(false)
        , prevFrame_(nullptr)
        , prevFrameReady_(false)
        , diffRatio_(0.0f)
        , lastCaptureMs_(0)
        , frameBuf_(nullptr)
        , frameBufSize_(0) {}

    ~CameraManager() {
        deinit();
    }

    /** Initialise the camera with the GC0308 sensor. */
    bool begin() {
        if (initOk_) return true;

        // ---- pin configuration --------------------------------------------
        camera_config_t cfg{};
        cfg.ledc_channel    = LEDC_CHANNEL_0;
        cfg.ledc_timer      = LEDC_TIMER_0;
        cfg.pin_d0          = CAM_DATA_0;
        cfg.pin_d1          = CAM_DATA_1;
        cfg.pin_d2          = CAM_DATA_2;
        cfg.pin_d3          = CAM_DATA_3;
        cfg.pin_d4          = -1;
        cfg.pin_d5          = -1;
        cfg.pin_d6          = -1;
        cfg.pin_d7          = -1;
        cfg.pin_xclk        = CAM_XCLK;
        cfg.pin_pclk        = CAM_PCLK;
        cfg.pin_vsync       = CAM_VSYNC;
        cfg.pin_href        = CAM_HREF;
        cfg.pin_sscb_sda    = -1;   // Use M5 I2C internally managed
        cfg.pin_sscb_scl    = -1;
        cfg.pin_pwdn        = CAM_PWDN;
        cfg.pin_reset       = CAM_RESET;
        cfg.xclk_freq_hz    = CAM_XCLK_FREQ;
        cfg.ledc_timer      = LEDC_TIMER_0;
        cfg.ledc_channel    = LEDC_CHANNEL_0;
        cfg.pixel_format    = PIXFORMAT_GRAYSCALE;  // 8-bit, single byte/pixel
        cfg.frame_size      = FRAMESIZE_VGA;         // 320 × 240
        cfg.jpeg_quality    = 12;                    // ignored for grayscale
        cfg.fb_count        = 1;                     // single buffer

        esp_err_t err = esp_camera_init(&cfg);
        if (err != ESP_OK) {
            log_e("Camera init failed: %s (0x%x)", esp_err_to_name(err), err);
            return false;
        }

        // GC0308-specific sensor tweaks
        sensor_t* sensor = esp_camera_sensor_get();
        if (sensor) {
            // GC0308: s→set_gain_ctrl(s, 1);   // Auto gain
            // GC0308: s→set_exposure_ctrl(s, 1); // Auto exposure
            sensor->set_gain_ctrl(sensor, 1);
            sensor->set_exposure_ctrl(sensor, 1);
            sensor->set_hmirror(sensor, 0);
            sensor->set_vflip(sensor, 0);
            // Reduce resolution to save bandwidth (we only need grayscale VGA)
            sensor->set_framesize(sensor, FRAMESIZE_VGA);
            log_i("Camera sensor initialised: GC0308");
        } else {
            log_w("Camera sensor get failed — continuing without sensor tweaks");
        }

        // Allocate the previous-frame buffer in PSRAM if available
        size_t needed = static_cast<size_t>(FRAME_PIXELS);
        if (psramFound()) {
            prevFrame_ = (uint8_t*)ps_malloc(needed);
            frameBuf_  = (uint8_t*)ps_malloc(needed);
        } else {
            prevFrame_ = (uint8_t*)malloc(needed);
            frameBuf_  = (uint8_t*)malloc(needed);
        }
        if (!prevFrame_ || !frameBuf_) {
            log_e("Failed to allocate frame buffers (%u bytes each)", needed);
            if (prevFrame_) { free(prevFrame_); prevFrame_ = nullptr; }
            if (frameBuf_)  { free(frameBuf_);  frameBuf_  = nullptr; }
            esp_camera_deinit();
            return false;
        }
        frameBufSize_ = needed;
        memset(prevFrame_, 0, needed);
        memset(frameBuf_,  0, needed);

        initOk_ = true;
        log_i("CameraManager initialised (VGA, grayscale, %d bytes/frame)", needed);
        return true;
    }

    /** Release all camera resources. */
    void deinit() {
        if (prevFrame_) { free(prevFrame_); prevFrame_ = nullptr; }
        if (frameBuf_)  { free(frameBuf_);  frameBuf_  = nullptr; }
        frameBufSize_ = 0;
        if (initOk_) {
            esp_camera_deinit();
            initOk_ = false;
        }
        prevFrameReady_ = false;
        diffRatio_ = 0.0f;
        log_i("CameraManager de-initialised");
    }

    /** Check whether initialisation succeeded. */
    bool isInitialised() const { return initOk_; }

    /**
     * Attempt to capture a frame and compute the diff ratio vs. the previous
     * frame. On the very first capture no diff is computed (diffRatio = 0).
     *
     * Call this at CAMERA_INTERVAL_MS intervals.
     *
     * @return true if a new frame was captured and processed.
     */
    bool captureAndDiff() {
        if (!initOk_) return false;

        // Grab frame from camera driver
        camera_fb_t* fb = esp_camera_fb_get();
        if (!fb) {
            log_w("Camera frame capture failed (null frame)");
            return false;
        }

        // Validate frame dimensions
        if (fb->width != FRAME_WIDTH || fb->height != FRAME_HEIGHT) {
            log_w("Unexpected frame size: %dx%d (expected %dx%d)",
                  fb->width, fb->height, FRAME_WIDTH, FRAME_HEIGHT);
            esp_camera_fb_return(fb);
            return false;
        }

        // For grayscale, fb->len = width × height
        // For JPEG (shouldn't happen with PIXFORMAT_GRAYSCALE) handle gracefully
        size_t dataLen = fb->len;
        if (dataLen > frameBufSize_) {
            dataLen = frameBufSize_;
        }
        memcpy(frameBuf_, fb->buf, dataLen);
        esp_camera_fb_return(fb);

        lastCaptureMs_ = millis();

        // Compute diff with previous frame
        if (prevFrameReady_) {
            diffRatio_ = computeDiffRatio(frameBuf_, prevFrame_, dataLen);
        } else {
            diffRatio_ = 0.0f;
        }

        // Rotate buffers: current → prev
        uint8_t* tmp = prevFrame_;
        prevFrame_   = frameBuf_;
        frameBuf_    = tmp;
        prevFrameReady_ = true;

        return true;
    }

    /** Return the most recent frame diff ratio (0.0 – 100.0). */
    float diffRatio() const { return diffRatio_; }

    /** Time (ms since boot) of the last successful capture. */
    unsigned long lastCaptureMs() const { return lastCaptureMs_; }

private:
    bool        initOk_;
    uint8_t*    prevFrame_;         // Previous grayscale frame (full res)
    uint8_t*    frameBuf_;          // Current frame storage
    size_t      frameBufSize_;      // Allocated size
    bool        prevFrameReady_;    // true after at least one capture
    float       diffRatio_;         // Latest diff ratio [0, 100]
    unsigned long lastCaptureMs_;

    /**
     * Compute the percentage of down-sampled pixels that differ by more than
     * a luminance threshold. Uses a stepped grid to reduce CPU load.
     *
     * @param current  Pointer to current frame data.
     * @param previous Pointer to previous frame data.
     * @param len      Number of bytes in each buffer.
     * @return Percentage of changed sampled pixels (0.0 – 100.0).
     */
    static float computeDiffRatio(const uint8_t* current,
                                  const uint8_t* previous,
                                  size_t len) {
        // Safety: ensure we have at least enough data for the sample grid
        size_t needed = static_cast<size_t>(SAMPLE_PIXELS * SAMPLE_STEP);
        if (len < needed) {
            return 0.0f;
        }

        constexpr int THRESHOLD = 40;  // Luminance difference to count as "changed"
        int changed = 0;
        int total   = 0;

        // Down-sampled grid scan
        for (int y = 0; y < SAMPLE_ROWS; ++y) {
            size_t rowBase = static_cast<size_t>(y * SAMPLE_STEP) * FRAME_WIDTH;
            for (int x = 0; x < SAMPLE_COLS; ++x) {
                size_t idx = rowBase + static_cast<size_t>(x * SAMPLE_STEP);
                if (idx + 1 > len) break;  // Bounds check (belt and braces)

                int diff = abs((int)current[idx] - (int)previous[idx]);
                if (diff > THRESHOLD) {
                    ++changed;
                }
                ++total;
            }
        }

        if (total == 0) return 0.0f;
        return (static_cast<float>(changed) / static_cast<float>(total)) * 100.0f;
    }
};

// =============================================================================
// 8. BUZZER MANAGER
// =============================================================================
/**
 * Simple buzzer control via LEDC PWM.
 * Active-high (assumes a transistor driver; adjust if active-low).
 */
class BuzzerManager {
public:
    BuzzerManager() : initOk_(false), enabled_(true), volume_(50) {}

    /** Set up LEDC PWM channel on PIN_BUZZER. */
    bool begin() {
        pinMode(PIN_BUZZER, OUTPUT);
        digitalWrite(PIN_BUZZER, LOW);

        ledcSetup(0, 2000, 8);       // Channel 0, 2 kHz, 8-bit resolution
        ledcAttachPin(PIN_BUZZER, 0);
        ledcWrite(0, 0);

        initOk_ = true;
        log_i("Buzzer initialised (GPIO %d)", PIN_BUZZER);
        return true;
    }

    /** Enable/disable all buzzer sound. */
    void setEnabled(bool en) { enabled_ = en; if (!en) ledcWrite(0, 0); }
    bool isEnabled() const { return enabled_; }

    /** Set volume 0 (off) … 100 (max). */
    void setVolume(uint8_t vol) { volume_ = (vol > 100) ? 100 : vol; }

    /** Play a tone at `freq` Hz for `durationMs` milliseconds (blocking). */
    void tone(unsigned int freq, unsigned long durationMs) {
        if (!initOk_ || !enabled_ || volume_ == 0) return;
        uint32_t duty = (volume_ * 255UL) / 100UL;
        ledcWrite(0, duty);
        ledcChangeFrequency(0, freq);
        delay(durationMs);
        ledcWrite(0, 0);
    }

    /** Short chirp for distraction warning. */
    void warnChirp() {
        tone(1200, 80);
        delay(40);
        tone(800, 60);
    }

    /** Start-of-focus jingle. */
    void focusChime() {
        tone(880, 100);
        delay(60);
        tone(1100, 100);
    }

    /** Break-start chime. */
    void breakChime() {
        tone(660, 80);
        delay(50);
        tone(880, 80);
        delay(50);
        tone(1100, 100);
    }

private:
    bool  initOk_;
    bool  enabled_;
    uint8_t volume_;
};

// =============================================================================
// 9. POMODORO ENGINE
// =============================================================================
/**
 * Core state machine logic for the pomodoro timer.
 *
 * This class owns the timer accounting and communicates with the rest of the
 * system via its public accessors. It does **not** directly touch hardware;
 * the App class bridges engine → display / buzzer / camera.
 */
class PomodoroEngine {
public:
    PomodoroEngine()
        : state_(PomodoroState::IDLE)
        , config_(FocusConfig::defaults())
        , elapsedMs_(0)
        , remainingMs_(0)
        , lastTickMs_(0)
        , sessionCount_(0)
        , totalMinutes_(0)
        , currentFocusMinutes_(0)
        , presenceConfirmed_(false)
        , presenceStartMs_(0)
        , awayStartMs_(0)
        , distractionStartMs_(0)
        , distracting_(false) {}

    // ---- Accessors ---------------------------------------------------------

    PomodoroState state() const { return state_; }
    unsigned long elapsedMs() const { return elapsedMs_; }
    unsigned long remainingMs() const { return remainingMs_; }
    unsigned long focusDurationMs() const { return config_.focusDurationMs; }
    unsigned long breakDurationMs() const { return config_.breakDurationMs; }
    uint32_t      sessionCount() const { return sessionCount_; }
    uint32_t      totalMinutes() const { return totalMinutes_; }
    bool          isDistracting() const { return distracting_; }

    void setSessionCount(uint32_t c) { sessionCount_ = c; }
    void setTotalMinutes(uint32_t m) { totalMinutes_ = m; }

    /** Cycle focus duration preset: 15 → 25 → 45 → 15 … */
    void cycleFocusPreset() {
        uint8_t next = (config_.focusPresetIndex + 1) % 3;
        config_.focusPresetIndex = next;
        config_.focusDurationMs  = FOCUS_PRESETS_MS[next];
        log_i("Focus preset changed to %u min", config_.focusDurationMs / 60000);
    }

    /** Cycle break duration preset: 3 → 5 → 10 → 3 … */
    void cycleBreakPreset() {
        uint8_t next = (config_.breakPresetIndex + 1) % 3;
        config_.breakPresetIndex = next;
        config_.breakDurationMs  = BREAK_PRESETS_MS[next];
        log_i("Break preset changed to %u min", config_.breakDurationMs / 60000);
    }

    unsigned long focusPresetMin() const {
        return config_.focusDurationMs / 60000UL;
    }

    unsigned long breakPresetMin() const {
        return config_.breakDurationMs / 60000UL;
    }

    // ---- Engine update (called ~every 100 ms from loop) --------------------

    /**
     * Main tick. Call periodically (target 50-100 Hz) to advance the state
     * machine.  The `diffRatio` comes from the camera manager.
     */
    void tick(float diffRatio, unsigned long nowMs) {
        // Guard against time running backwards (edge case: overflow/correction)
        if (lastTickMs_ > nowMs) {
            lastTickMs_ = nowMs;
            return;
        }

        unsigned long delta = (lastTickMs_ == 0) ? 0 : (nowMs - lastTickMs_);
        lastTickMs_ = nowMs;

        // Clamp delta to prevent spiral on overflow or long stalls
        if (delta > 5000) delta = 100;  // Max 5 s jump → clamp to 100 ms

        switch (state_) {
            // ----------------------------------------------------------------
            case PomodoroState::IDLE:
                handleIdle(diffRatio, nowMs);
                break;

            // ----------------------------------------------------------------
            case PomodoroState::FOCUS:
                handleFocus(delta, diffRatio, nowMs);
                break;

            // ----------------------------------------------------------------
            case PomodoroState::BREAK:
                handleBreak(delta, diffRatio, nowMs);
                break;

            // ----------------------------------------------------------------
            case PomodoroState::AWAY:
                handleAway(diffRatio, nowMs);
                break;

            // ----------------------------------------------------------------
            case PomodoroState::DISTRACTION_WARN:
                handleDistraction(delta, diffRatio, nowMs);
                break;
        }
    }

    /** Force a state transition (used by UI config changes or touch). */
    void forceState(PomodoroState newState) {
        if (state_ == newState) return;
        // Notify observers via state change flag
        stateChanged_ = true;
        state_ = newState;
        log_i("State forced: %s", stateName(state_));
        resetTimersForState();
    }

    /** True if the state just changed (poll and clear). */
    bool stateJustChanged() {
        bool v = stateChanged_;
        stateChanged_ = false;
        return v;
    }

    /** Reset the entire engine back to IDLE. */
    void reset() {
        state_ = PomodoroState::IDLE;
        elapsedMs_ = 0;
        remainingMs_ = 0;
        currentFocusMinutes_ = 0;
        presenceConfirmed_ = false;
        presenceStartMs_ = 0;
        awayStartMs_ = 0;
        distractionStartMs_ = 0;
        distracting_ = false;
        stateChanged_ = true;
        lastTickMs_ = millis();
        log_i("Engine reset to IDLE");
    }

    // Distraction acknowledgement (user tapped screen → dismiss)
    void dismissDistraction() {
        if (state_ == PomodoroState::DISTRACTION_WARN) {
            distracting_ = false;
            // Return to focus (time was not ticking during warning)
            forceState(PomodoroState::FOCUS);
            log_i("Distraction dismissed by user");
        }
    }

private:
    PomodoroState state_;
    FocusConfig   config_;
    unsigned long elapsedMs_;          // How long current timer has run
    unsigned long remainingMs_;        // Remaining time in current phase
    unsigned long lastTickMs_;
    uint32_t      sessionCount_;
    uint32_t      totalMinutes_;
    uint32_t      currentFocusMinutes_;

    // Presence tracking
    bool          presenceConfirmed_;
    unsigned long presenceStartMs_;    // When we first saw the person
    unsigned long awayStartMs_;        // When person left (for grace period)

    // Distraction tracking
    unsigned long distractionStartMs_;
    bool          distracting_;        // Currently in warning state?

    bool stateChanged_ = true;         // Tracks transitions

    // ---- Helpers -----------------------------------------------------------

    void resetTimersForState() {
        elapsedMs_ = 0;
        lastTickMs_ = millis();
        switch (state_) {
            case PomodoroState::FOCUS:
                remainingMs_ = config_.focusDurationMs;
                break;
            case PomodoroState::BREAK:
                remainingMs_ = config_.breakDurationMs;
                break;
            case PomodoroState::AWAY:
            case PomodoroState::IDLE:
                remainingMs_ = 0;
                break;
            default:
                break;
        }
    }

    // ---- State handlers ----------------------------------------------------

    void handleIdle(float diffRatio, unsigned long nowMs) {
        // If diff shows significant change, someone might be sitting down
        // A person sitting still typically yields diff < PRESENCE_THRESHOLD
        // after the initial settling; we want to detect the *presence* of
        // someone already there when the device starts. The camera sees a
        // large diff on first frame (prevFrame all zeros), so we need a
        // different heuristic: after setup, we wait for a frame with low
        // diff (person sitting still) OR sustained presence over time.
        //
        // Simple approach: if diff is moderate-to-low consistently, assume
        // someone is present.
        if (diffRatio >= 0.0f && diffRatio < PRESENCE_THRESHOLD * 2) {
            // Low change — likely a static scene (person present or empty room)
            // Differentiate by average luminance (empty desk = bright/empty)
            // For MVP we use a simpler approach: if diff is very low (< AWAY_THRESHOLD)
            // the scene is static. If it's mid-range, assume motion = person.
            if (diffRatio < AWAY_THRESHOLD) {
                // Very static scene — could be empty desk or person sitting still
                // We rely on the first-frame diff being high; if we've had a
                // consistent static scene for a while, we're likely in an empty room.
                // For MVP: do NOT auto-start in IDLE if the scene is dead static.
                presenceConfirmed_ = false;
                presenceStartMs_ = 0;
            }
        } else if (diffRatio > PRESENCE_THRESHOLD && diffRatio < MOTION_THRESHOLD * 2) {
            // Moderate change — likely a person moving slightly at desk
            if (!presenceConfirmed_) {
                if (presenceStartMs_ == 0) {
                    presenceStartMs_ = nowMs;
                } else if ((nowMs - presenceStartMs_) >= PRESENCE_DEBOUNCE_MS) {
                    // Person present for 30+ seconds → start focus
                    presenceConfirmed_ = true;
                    log_i("Presence confirmed — starting FOCUS");
                    forceState(PomodoroState::FOCUS);
                }
            }
        } else {
            // High change (e.g., someone just sat down) — start debounce
            if (!presenceConfirmed_) {
                if (presenceStartMs_ == 0) {
                    presenceStartMs_ = nowMs;
                }
            }
        }
    }

    void handleFocus(unsigned long delta, float diffRatio, unsigned long nowMs) {
        if (diffRatio > AWAY_THRESHOLD) {
            // Scene changed — person may have left
            if (awayStartMs_ == 0) {
                awayStartMs_ = nowMs;
            } else if ((nowMs - awayStartMs_) >= AWAY_GRACE_PERIOD_MS) {
                // Person has been away for the grace period → pause
                log_i("Away grace period expired — entering AWAY state");
                forceState(PomodoroState::AWAY);
                // Track elapsed minutes for this session so far
                currentFocusMinutes_ = elapsedMs_ / 60000UL;
                return;
            }
        } else {
            // Person is back — reset away timer
            awayStartMs_ = 0;
        }

        // Distraction check: rapid motion (phone pick-up, sudden movement)
        if (diffRatio > MOTION_THRESHOLD && !distracting_) {
            if (distractionStartMs_ == 0) {
                distractionStartMs_ = nowMs;
            } else if ((nowMs - distractionStartMs_) >= DISTRACTION_GRACE_MS) {
                // 15 seconds of sustained motion → trigger warning
                distracting_ = true;
                forceState(PomodoroState::DISTRACTION_WARN);
                return;
            }
        } else {
            // Motion subsided — reset distraction timer
            distractionStartMs_ = 0;
        }

        // Advance timer
        elapsedMs_ += delta;
        if (elapsedMs_ >= config_.focusDurationMs) {
            // Session complete!
            completeSession();
        }
    }

    void handleBreak(unsigned long delta, float diffRatio, unsigned long nowMs) {
        // Advance break timer
        elapsedMs_ += delta;
        if (elapsedMs_ >= config_.breakDurationMs) {
            log_i("Break finished — returning to FOCUS");
            forceState(PomodoroState::FOCUS);
            return;
        }

        // Track away during break too
        if (diffRatio > AWAY_THRESHOLD) {
            if (awayStartMs_ == 0) awayStartMs_ = nowMs;
            // Don't pause break — breaks are short; if person leaves, just wait
        } else {
            awayStartMs_ = 0;
        }
    }

    void handleAway(float diffRatio, unsigned long nowMs) {
        // Person returned?
        if (diffRatio >= 0.0f && diffRatio < AWAY_THRESHOLD) {
            // Desk is static again — check if we were in a focus session
            if (elapsedMs_ > 0 && elapsedMs_ < config_.focusDurationMs) {
                log_i("Person returned during FOCUS — resuming");
                forceState(PomodoroState::FOCUS);
                return;
            }
        }

        // Significant motion detected — could be person returning
        if (diffRatio > PRESENCE_THRESHOLD) {
            if (presenceStartMs_ == 0) {
                presenceStartMs_ = nowMs;
            } else if ((nowMs - presenceStartMs_) >= 5000) {
                // 5 seconds of motion = person is back
                log_i("Motion detected in AWAY — resuming FOCUS");
                presenceStartMs_ = 0;
                if (elapsedMs_ > 0 && elapsedMs_ < config_.focusDurationMs) {
                    forceState(PomodoroState::FOCUS);
                } else {
                    forceState(PomodoroState::IDLE);
                }
                return;
            }
        } else {
            presenceStartMs_ = 0;
        }
    }

    void handleDistraction(unsigned long delta, float diffRatio, unsigned long nowMs) {
        // Stay in warning state until diff decreases (person returns to focus)
        // OR user taps dismiss
        if (diffRatio < MOTION_THRESHOLD / 2) {
            // Motion subsided — auto-dismiss
            log_i("Motion subsided — distraction auto-dismissed");
            distracting_ = false;
            forceState(PomodoroState::FOCUS);
        }
        // Timer does NOT advance during distraction
    }

    void completeSession() {
        ++sessionCount_;
        uint32_t thisSessionMin = config_.focusDurationMs / 60000UL;
        totalMinutes_ += thisSessionMin;
        currentFocusMinutes_ = 0;
        log_i("Session complete! Count=%u, TotalMin=%u", sessionCount_, totalMinutes_);
        forceState(PomodoroState::BREAK);
    }
};

// =============================================================================
// 10. DISPLAY / UI MANAGER
// =============================================================================
/**
 * Renders the state-appropriate UI on the ILI9342C 320×240 TFT via M5GFX.
 *
 * The M5CoreS3 library exposes the display as `M5.Lcd` (a LGFX_Device
 * subclass).  All drawing goes through M5.Lcd.
 */
class DisplayManager {
public:
    DisplayManager() : lastSecond_(0) {}

    void begin() {
        M5.Lcd.setRotation(1);           // Landscape (USB port on left)
        M5.Lcd.fillScreen(COLOR_BG);
        M5.Lcd.setTextSize(1);
        M5.Lcd.setTextColor(COLOR_WHITE);
        M5.Lcd.setBrightness(120);       // Moderate brightness
        log_i("Display initialised (%dx%d)", M5.Lcd.width(), M5.Lcd.height());
    }

    /** Render the appropriate screen for the current state. */
    void render(PomodoroState state, unsigned long remainingMs,
                unsigned long elapsedMs, unsigned long totalMs,
                uint32_t sessionCount, uint32_t totalMinutes,
                bool buzzerEnabled) {
        // Only redraw every 100 ms to avoid flicker; full-redraw at second
        // boundaries or on state change.
        unsigned long nowSec = millis() / 1000;
        bool timeSecondChanged = (nowSec != lastSecond_);
        lastSecond_ = nowSec;

        switch (state) {
            case PomodoroState::IDLE:
                renderIdle();
                break;
            case PomodoroState::FOCUS:
                if (timeSecondChanged) renderFocus(remainingMs, totalMs);
                break;
            case PomodoroState::BREAK:
                if (timeSecondChanged) renderBreak(remainingMs, totalMs,
                                                    sessionCount, totalMinutes);
                break;
            case PomodoroState::AWAY:
                renderAway();
                break;
            case PomodoroState::DISTRACTION_WARN:
                renderDistraction(nowSec);
                break;
        }
    }

    /** Flash the screen red (called from app on distraction entry). */
    void flashWarning() {
        M5.Lcd.fillScreen(COLOR_WARN);
        M5.Lcd.setTextSize(3);
        M5.Lcd.setTextColor(COLOR_WHITE);
        M5.Lcd.setCursor(40, 100);
        M5.Lcd.print("DISTRACTION!");
        delay(500);
    }

    void dimScreen() {
        M5.Lcd.setBrightness(20);
    }

    void restoreBrightness() {
        M5.Lcd.setBrightness(120);
    }

private:
    unsigned long lastSecond_;

    // ---- Rendering helpers -------------------------------------------------

    void renderIdle() {
        M5.Lcd.fillScreen(COLOR_BG);
        M5.Lcd.setTextSize(2);
        M5.Lcd.setTextColor(COLOR_DIM);
        M5.Lcd.setCursor(90, 90);
        M5.Lcd.print("Waiting...");
        M5.Lcd.setTextSize(1);
        M5.Lcd.setCursor(70, 130);
        M5.Lcd.setTextColor(0x4208);
        M5.Lcd.print("Sit at your desk to start");
    }

    void renderFocus(unsigned long remainingMs, unsigned long totalMs) {
        M5.Lcd.fillScreen(COLOR_FOCUS);

        // ---- Large countdown ----
        int totalSec  = remainingMs / 1000;
        int mins      = totalSec / 60;
        int secs      = totalSec % 60;

        M5.Lcd.setTextSize(1);
        M5.Lcd.setTextColor(COLOR_WHITE);
        M5.Lcd.setCursor(10, 10);
        M5.Lcd.print("FOCUS");

        // Progress bar (thin horizontal bar at top)
        float progress = (totalMs > 0)
            ? 1.0f - (static_cast<float>(remainingMs) / static_cast<float>(totalMs))
            : 0.0f;
        int barWidth = static_cast<int>(progress * (SCREEN_WIDTH - 20));
        M5.Lcd.drawRect(10, 30, SCREEN_WIDTH - 20, 8, COLOR_WHITE);
        if (barWidth > 0) {
            M5.Lcd.fillRect(11, 31, barWidth, 6, COLOR_WHITE);
        }

        // Timer digits
        char buf[16];
        snprintf(buf, sizeof(buf), "%02d:%02d", mins, secs);
        M5.Lcd.setTextSize(4);
        M5.Lcd.setTextColor(COLOR_WHITE);
        int32_t tw = M5.Lcd.textWidth(buf);
        M5.Lcd.setCursor((SCREEN_WIDTH - tw) / 2, 80);
        M5.Lcd.print(buf);

        // Subtle "focus" message
        M5.Lcd.setTextSize(1);
        M5.Lcd.setCursor(10, SCREEN_HEIGHT - 20);
        M5.Lcd.setTextColor(0x8C51);  // lighter teal
        M5.Lcd.print("Stay focused");
    }

    void renderBreak(unsigned long remainingMs, unsigned long totalMs,
                     uint32_t sessionCount, uint32_t totalMinutes) {
        M5.Lcd.fillScreen(COLOR_BREAK);

        // Title
        M5.Lcd.setTextSize(1);
        M5.Lcd.setTextColor(COLOR_WHITE);
        M5.Lcd.setCursor(10, 10);
        M5.Lcd.print("BREAK");

        // Cheerful icon / message
        M5.Lcd.setTextSize(2);
        M5.Lcd.setCursor(50, 50);
        M5.Lcd.print("Time for coffee!");

        // Countdown
        int totalSec = remainingMs / 1000;
        int mins = totalSec / 60;
        int secs = totalSec % 60;

        char buf[16];
        snprintf(buf, sizeof(buf), "%02d:%02d", mins, secs);
        M5.Lcd.setTextSize(3);
        M5.Lcd.setTextColor(COLOR_WHITE);
        int32_t tw = M5.Lcd.textWidth(buf);
        M5.Lcd.setCursor((SCREEN_WIDTH - tw) / 2, 100);
        M5.Lcd.print(buf);

        // Session stats
        M5.Lcd.setTextSize(1);
        M5.Lcd.setCursor(10, SCREEN_HEIGHT - 20);
        M5.Lcd.setTextColor(0x94A4);
        M5.Lcd.printf("Today: %u sessions / %u min", sessionCount, totalMinutes);
    }

    void renderAway() {
        M5.Lcd.fillScreen(COLOR_AWAY);
        M5.Lcd.setTextSize(2);
        M5.Lcd.setTextColor(COLOR_DIM);
        M5.Lcd.setCursor(90, 90);
        M5.Lcd.print("Away...");
        M5.Lcd.setTextSize(1);
        M5.Lcd.setCursor(60, 130);
        M5.Lcd.print("Timer paused. Welcome back!");
    }

    void renderDistraction(unsigned long nowSec) {
        // Rapid flashing: alternate red / dark every 500 ms
        bool phase = (nowSec % 1) == 0;  // toggle roughly every 500ms
        M5.Lcd.fillScreen(phase ? COLOR_WARN : 0x7800);
        M5.Lcd.setTextSize(2);
        M5.Lcd.setTextColor(COLOR_WHITE);
        M5.Lcd.setCursor(50, 90);
        M5.Lcd.print("STOP!");
        M5.Lcd.setCursor(30, 120);
        M5.Lcd.print("Return to your seat");
        M5.Lcd.setTextSize(1);
        M5.Lcd.setCursor(40, 160);
        M5.Lcd.print("Tap screen to dismiss");
    }
};

// =============================================================================
// 11. FOCUS GUARDIAN APPLICATION
// =============================================================================
/**
 * Top-level orchestrator that wires together the camera, engine, display,
 * buzzer, and NVS manager.
 *
 * Ownership & lifetime:
 *   - Setup: begin() → init all subsystems
 *   - Loop:  run()  → camera capture, engine tick, UI render, watchdog
 */
class FocusGuardianApp {
public:
    FocusGuardianApp()
        : lastCameraMs_(0)
        , lastNvsSaveMs_(0)
        , lastRenderMs_(0)
        , uiDirty_(true) {}

    ~FocusGuardianApp() {
        camera_.deinit();
    }

    /** Initialise all subsystems. Return true if everything is OK. */
    bool begin() {
        log_i("=== Focus Guardian v1.0 === ");
        log_i("Board: M5Stack Core S3 (ESP32-S3)");
        log_i("PSRAM: %s", psramFound() ? "8 MB" : "NOT AVAILABLE");
        log_i("Flash: %u MB", spi_flash_get_chip_size() / (1024 * 1024));

        // 1. NVS
        if (!nvs_.begin()) {
            log_w("NVS init failed — stats will not be persisted");
        } else {
            uint32_t sc = nvs_.readSessionCount();
            uint32_t tm = nvs_.readTotalMinutes();
            engine_.setSessionCount(sc);
            engine_.setTotalMinutes(tm);
            log_i("NVS: sessions=%u, totalMin=%u", sc, tm);
        }

        // 2. Display
        display_.begin();
        display_.dimScreen();

        // 3. Buzzer
        buzzer_.begin();

        // 4. Camera (requires PSRAM for frame buffers)
        if (!camera_.begin()) {
            log_e("Camera init failed — presence detection unavailable");
            showFatal("Camera init failed!\nCheck connections.");
            return false;
        }

        // Show boot screen
        M5.Lcd.fillScreen(COLOR_BG);
        M5.Lcd.setTextSize(2);
        M5.Lcd.setTextColor(COLOR_WHITE);
        M5.Lcd.setCursor(50, 100);
        M5.Lcd.print("Focus Guardian");
        M5.Lcd.setTextSize(1);
        M5.Lcd.setCursor(70, 140);
        M5.Lcd.print("Loading...");
        delay(1500);
        display_.restoreBrightness();

        lastCameraMs_ = millis();
        log_i("All subsystems initialised successfully");
        return true;
    }

    /** Main loop iteration. Call from Arduino loop() every 10-20 ms. */
    void run() {
        unsigned long nowMs = millis();

        // ---- 1. Camera capture (2 s interval) ------------------------------
        if (camera_.isInitialised() &&
            (nowMs - lastCameraMs_) >= CAMERA_INTERVAL_MS) {
            camera_.captureAndDiff();
            lastCameraMs_ = nowMs;
            log_d("Camera diff: %.1f%%", camera_.diffRatio());
        }

        // ---- 2. Engine tick ------------------------------------------------
        PomodoroState prevState = engine_.state();
        engine_.tick(camera_.diffRatio(), nowMs);

        // ---- 3. Handle state transitions -----------------------------------
        if (engine_.stateJustChanged()) {
            onStateChanged(prevState, engine_.state());
            uiDirty_ = true;
        }

        // ---- 4. Render UI (throttled to ~10 Hz) ----------------------------
        if (uiDirty_ || (nowMs - lastRenderMs_) >= 100) {
            display_.render(
                engine_.state(),
                engine_.remainingMs(),
                engine_.elapsedMs(),
                engine_.focusDurationMs(),
                engine_.sessionCount(),
                engine_.totalMinutes(),
                buzzer_.isEnabled()
            );
            lastRenderMs_ = nowMs;
            uiDirty_ = false;
        }

        // ---- 5. NVS persistence (every 60 seconds) -------------------------
        if ((nowMs - lastNvsSaveMs_) >= 60000) {
            persistStats();
            lastNvsSaveMs_ = nowMs;
        }

        // ---- 6. Touch handling (configuration) -----------------------------
        handleTouch();
    }

private:
    CameraManager   camera_;
    PomodoroEngine  engine_;
    DisplayManager  display_;
    BuzzerManager   buzzer_;
    NvsManager      nvs_;

    unsigned long   lastCameraMs_;
    unsigned long   lastNvsSaveMs_;
    unsigned long   lastRenderMs_;
    bool            uiDirty_;

    // ---- State change callbacks --------------------------------------------

    void onStateChanged(PomodoroState oldState, PomodoroState newState) {
        log_i("State: %s → %s", stateName(oldState), stateName(newState));

        switch (newState) {
            case PomodoroState::FOCUS:
                display_.restoreBrightness();
                buzzer_.focusChime();
                break;

            case PomodoroState::BREAK:
                buzzer_.breakChime();
                break;

            case PomodoroState::AWAY:
                display_.dimScreen();
                break;

            case PomodoroState::DISTRACTION_WARN:
                display_.flashWarning();
                buzzer_.warnChirp();
                break;

            case PomodoroState::IDLE:
                display_.dimScreen();
                break;
        }
    }

    /** Persist session stats to NVS. */
    void persistStats() {
        nvs_.writeSessionCount(engine_.sessionCount());
        nvs_.writeTotalMinutes(engine_.totalMinutes());
        if (!nvs_.commit()) {
            log_w("NVS commit failed — stats may not persist");
        }
    }

    /** Handle touch input for config changes and distraction dismiss. */
    void handleTouch() {
        M5.update();
        if (M5.Touch.getCount() > 0) {
            auto t = M5.Touch.getDetail();
            if (t.wasClicked()) {
                // Distraction dismiss
                if (engine_.state() == PomodoroState::DISTRACTION_WARN) {
                    engine_.dismissDistraction();
                    uiDirty_ = true;
                    return;
                }

                // Tap zones:
                //   Top-left  corner (0-80, 0-80)    → cycle focus preset
                //   Top-right corner (240-320, 0-80) → cycle break preset
                //   Bottom sections → force re-centre
                int tx = t.x;
                int ty = t.y;
                if (tx < 80 && ty < 80) {
                    engine_.cycleFocusPreset();
                    uiDirty_ = true;
                    buzzer_.tone(1000, 30);
                    showToast("Focus: %u min", engine_.focusPresetMin());
                } else if (tx > (SCREEN_WIDTH - 80) && ty < 80) {
                    engine_.cycleBreakPreset();
                    uiDirty_ = true;
                    buzzer_.tone(800, 30);
                    showToast("Break: %u min", engine_.breakPresetMin());
                } else {
                    // Tap elsewhere → reset away timer / wake
                    if (engine_.state() == PomodoroState::AWAY) {
                        // Trigger return-to-seat check
                        uiDirty_ = true;
                    }
                }
            }
        }
    }

    /** Show a brief toast message centred on screen (overlay). */
    void showToast(const char* fmt, ...) {
        char buf[64];
        va_list args;
        va_start(args, fmt);
        vsnprintf(buf, sizeof(buf), fmt, args);
        va_end(args);

        // Save area (simple approach: draw a small rect)
        M5.Lcd.fillRect(60, 200, 200, 30, COLOR_BG);
        M5.Lcd.setTextSize(1);
        M5.Lcd.setTextColor(COLOR_WHITE);
        M5.Lcd.setCursor(70, 208);
        M5.Lcd.print(buf);
        // The toast stays until next render cycle overwrites it
    }

    /** Fatal error screen — halts execution. */
    void showFatal(const char* msg) {
        M5.Lcd.fillScreen(COLOR_WARN);
        M5.Lcd.setTextSize(2);
        M5.Lcd.setTextColor(COLOR_WHITE);
        M5.Lcd.setCursor(10, 100);
        M5.Lcd.print(msg);
        log_e("FATAL: %s", msg);
        while (true) {
            delay(1000);
        }
    }
};

// =============================================================================
// 12. GLOBAL INSTANCE
// =============================================================================
FocusGuardianApp app;

// =============================================================================
// 13. ARDUINO ENTRY POINTS
// =============================================================================
void setup() {
    // Seed random (used by delay jitter, not heavily relied on)
    randomSeed(analogRead(0));

    // Initialise M5CoreS3 board (LCD, I2C, power, touch, SD)
    auto cfg = M5.config();
    M5.begin(cfg);

    // Enable USB serial for logging (115200 baud)
    Serial.begin(115200);
    delay(200);
    log_i("Focus Guardian starting...");

    // Initialise NVS flash (needed before camera, which uses PSRAM)
    esp_err_t nvsInit = nvs_flash_init();
    if (nvsInit == ESP_ERR_NVS_NO_FREE_PAGES ||
        nvsInit == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        nvsInit = nvs_flash_init();
    }
    if (nvsInit != ESP_OK) {
        log_e("NVS flash init failed: %s", esp_err_to_name(nvsInit));
    }

    // Start the application
    if (!app.begin()) {
        log_e("Application initialisation failed — halting");
        while (true) {
            delay(1000);
        }
    }

    log_i("=== Focus Guardian READY ===");
}

void loop() {
    app.run();

    // Yield to IDLE task (reduces power, lets watchdog breathe)
    delay(10);
}
