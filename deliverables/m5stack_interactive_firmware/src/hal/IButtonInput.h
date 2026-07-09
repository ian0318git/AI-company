#pragma once

#include <cstdint>

/**
 * @brief Physical button abstraction
 *
 * CoreS3 has 3 buttons (A: GPIO 41, B: GPIO 42, C: GPIO 0).
 * StackChan has 1 button (GPIO 0).
 * All are active-low with internal pull-ups.
 */
class IButtonInput {
public:
    enum Button : uint8_t {
        BTN_A = 0,
        BTN_B = 1,
        BTN_C = 2,
        BTN_CUSTOM = 3,
        BTN_MAX = 4
    };

    virtual ~IButtonInput() = default;

    virtual bool begin() = 0;

    /** @brief Is button currently held? */
    virtual bool isPressed(Button btn) = 0;

    /** @brief Was button pressed since last check? (edge-triggered) */
    virtual bool wasPressed(Button btn) = 0;

    /** @brief Was button held for durationMs? */
    virtual bool wasHeld(Button btn, uint32_t durationMs) = 0;

    /** @brief Bitmask of all currently pressed buttons */
    virtual uint8_t getPressedMask() = 0;

    /** @brief Debounce interval in ms (default 50) */
    virtual void setDebounceMs(uint32_t ms) = 0;
};
