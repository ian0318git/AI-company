#pragma once

#include <cstdint>

/**
 * @brief Servo motor abstraction for StackChan
 *
 * Controls body and head servos via PWM (50Hz, 0–180 degrees).
 */
class IServoController {
public:
    struct ServoAngles {
        uint8_t body;  // 0–180
        uint8_t head;  // 0–180
    };

    virtual ~IServoController() = default;

    virtual bool begin(uint8_t pinBody, uint8_t pinHead) = 0;

    /** @brief Set both servos atomically */
    virtual bool setAngles(const ServoAngles& angles) = 0;

    /** @brief Set a single servo by name ("body" or "head") */
    virtual bool setAngle(const char* name, uint8_t angle) = 0;

    /** @brief Read current angles from servo feedback (if supported) */
    virtual ServoAngles getCurrentAngles() = 0;

    /** @brief Gradually move to target over durationMs (ms) */
    virtual bool smoothMove(const ServoAngles& target, uint16_t durationMs) = 0;

    /** @brief Disable servos (save power) */
    virtual void detach() = 0;
};
