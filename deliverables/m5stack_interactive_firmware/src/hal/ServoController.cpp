#include "ServoController.h"
#include <cstring>

ServoController::ServoController()
    : _pinBody(0), _pinHead(0)
{
    _current.body = 90;
    _current.head = 90;
}

bool ServoController::begin(uint8_t pinBody, uint8_t pinHead) {
    _pinBody  = pinBody;
    _pinHead  = pinHead;

    // Allow allocation of PWM channels
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);

    _servoBody.setPeriodHertz(SERVO_FREQ_HZ);
    _servoHead.setPeriodHertz(SERVO_FREQ_HZ);

    bool ok = true;
    ok &= _servoBody.attach(_pinBody, SERVO_MIN_PULSE, SERVO_MAX_PULSE);
    ok &= _servoHead.attach(_pinHead, SERVO_MIN_PULSE, SERVO_MAX_PULSE);

    // Set to neutral
    _servoBody.write(90);
    _servoHead.write(90);
    _current.body = 90;
    _current.head = 90;

    return ok;
}

bool ServoController::setAngles(const ServoAngles& angles) {
    _servoBody.write(angles.body);
    _servoHead.write(angles.head);
    _current = angles;
    return true;
}

bool ServoController::setAngle(const char* name, uint8_t angle) {
    if (angle > 180) angle = 180;

    if (strcmp(name, "body") == 0) {
        _servoBody.write(angle);
        _current.body = angle;
        return true;
    } else if (strcmp(name, "head") == 0) {
        _servoHead.write(angle);
        _current.head = angle;
        return true;
    }
    return false;
}

ServoController::ServoAngles ServoController::getCurrentAngles() {
    return _current;
}

bool ServoController::smoothMove(const ServoAngles& target, uint16_t durationMs) {
    int steps = durationMs / 20;  // 50Hz step rate
    if (steps < 1) steps = 1;

    float dbStep = static_cast<float>(static_cast<int>(target.body) - _current.body) / steps;
    float dhStep = static_cast<float>(static_cast<int>(target.head) - _current.head) / steps;

    for (int i = 0; i < steps; i++) {
        _current.body = static_cast<uint8_t>(_current.body + dbStep);
        _current.head = static_cast<uint8_t>(_current.head + dhStep);
        _servoBody.write(_current.body);
        _servoHead.write(_current.head);
        delay(20);
    }

    // Ensure exact final position
    _current = target;
    _servoBody.write(target.body);
    _servoHead.write(target.head);
    return true;
}

void ServoController::detach() {
    _servoBody.detach();
    _servoHead.detach();
}
