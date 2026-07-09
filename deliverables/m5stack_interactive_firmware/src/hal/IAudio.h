#pragma once

#include <cstdint>

/**
 * @brief PDM microphone abstraction for CoreS3
 *
 * SPM1423 PDM mic on DATA: GPIO 34, CLK: GPIO 35.
 * Provides audio level metering and optional sample capture.
 */
class IAudioInput {
public:
    virtual ~IAudioInput() = default;

    virtual bool begin(int dataPin, int clkPin) = 0;

    /** @brief Read raw PCM samples into buffer */
    virtual bool readSamples(int16_t* buf, size_t count) = 0;

    /** @brief Get current audio level (0.0–1.0) for VU meter */
    virtual float getLevel() = 0;

    /** @brief Start continuous sampling (DMA-based if supported) */
    virtual bool startContinuous() = 0;

    /** @brief Stop continuous sampling */
    virtual void stopContinuous() = 0;

    /** @brief Check if audio clip is detected (level > threshold) */
    virtual bool isClipping(float threshold = 0.95f) = 0;
};

/**
 * @brief I2S DAC / Speaker abstraction for CoreS3
 */
class IAudioOutput {
public:
    virtual ~IAudioOutput() = default;

    virtual bool begin(int dacPin) = 0;

    /** @brief Play a tone at frequency for duration */
    virtual bool playTone(uint16_t freq, uint16_t durationMs) = 0;

    /** @brief Play PCM samples through speaker */
    virtual bool playSamples(const int16_t* buf, size_t count) = 0;

    /** @brief Set volume (0–255) */
    virtual void setVolume(uint8_t vol) = 0;

    /** @brief Stop playback immediately */
    virtual void stop() = 0;
};
