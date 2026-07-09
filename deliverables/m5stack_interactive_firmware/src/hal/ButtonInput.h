#pragma once

#include "IButtonInput.h"
#include <cstdint>

/**
 * @brief Button implementation for M5Stack CoreS3
 *
 * Button A: GPIO 41 (active low)
 * Button B: GPIO 42 (active low)
 * Button C: GPIO 0  (active low)
 */
class ButtonInput : public IButtonInput {
public:
    static constexpr int PIN_BTN_A = 41;
    static constexpr int PIN_BTN_B = 42;
    static constexpr int PIN_BTN_C = 0;

    static constexpr uint32_t DEBOUNCE_MS = 50;
    static constexpr uint32_t HOLD_MS     = 2000;

    ButtonInput();

    bool begin() override;
    bool isPressed(Button btn) override;
    bool wasPressed(Button btn) override;
    bool wasHeld(Button btn, uint32_t durationMs) override;
    uint8_t getPressedMask() override;
    void setDebounceMs(uint32_t ms) override;

private:
    struct ButtonState {
        bool lastRaw;          // Last raw reading
        bool lastDebounced;    // Last debounced state
        bool edgeFalling;      // Falling edge detected
        uint32_t lastChangeMs; // Time of last state change
        uint32_t pressStartMs; // When press started (for hold detection)
    };

    ButtonState _buttons[BTN_MAX];
    int _pinMap[BTN_MAX];
    uint32_t _debounceMs;
    uint32_t _lastScanMs;

    void scan();
    int pinForButton(Button btn) const;
};
