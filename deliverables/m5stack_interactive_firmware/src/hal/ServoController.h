#pragma once

#include "IServoController.h"
#include <ESP32Servo.h>

/**
 * @brief Servo controller for StackChan using ESP32 PWM
 *
 * Body servo: GPIO 13
 * Head servo: GPIO 14
 * 50Hz PWM, 0–180 degrees
 */
class ServoController : public IServoController {
public:
    ServoController();

    bool begin(uint8_t pinBody, uint8_t pinHead) override;
    bool setAngles(const ServoAngles& angles) override;
    bool setAngle(const char* name, uint8_t angle) override;
    ServoAngles getCurrentAngles() override;
    bool smoothMove(const ServoAngles& target, uint16_t durationMs) override;
    void detach() override;

private:
    Servo _servoBody;
    Servo _servoHead;
    uint8_t _pinBody;
    uint8_t _pinHead;
    ServoAngles _current;

    static constexpr int SERVO_MIN_PULSE = 500;   // 0°
    static constexpr int SERVO_MAX_PULSE = 2500;  // 180°
    static constexpr int SERVO_FREQ_HZ   = 50;
};
