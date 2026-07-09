#include "ButtonInput.h"
#include <Arduino.h>

ButtonInput::ButtonInput()
    : _debounceMs(DEBOUNCE_MS)
    , _lastScanMs(0)
{
    _pinMap[BTN_A] = PIN_BTN_A;
    _pinMap[BTN_B] = PIN_BTN_B;
    _pinMap[BTN_C] = PIN_BTN_C;
    _pinMap[BTN_CUSTOM] = -1;

    for (int i = 0; i < BTN_MAX; i++) {
        _buttons[i].lastRaw = true;       // Active low, unpressed = HIGH
        _buttons[i].lastDebounced = true;
        _buttons[i].edgeFalling = false;
        _buttons[i].lastChangeMs = 0;
        _buttons[i].pressStartMs = 0;
    }
}

bool ButtonInput::begin() {
    for (int i = 0; i < 3; i++) {
        if (_pinMap[i] >= 0) {
            pinMode(_pinMap[i], INPUT_PULLUP);
        }
    }
    return true;
}

void ButtonInput::scan() {
    uint32_t now = millis();
    if (now - _lastScanMs < 5) return;  // Rate limit to ~200Hz
    _lastScanMs = now;

    for (int i = 0; i < 3; i++) {
        if (_pinMap[i] < 0) continue;

        bool raw = (digitalRead(_pinMap[i]) == LOW);
        ButtonState& s = _buttons[i];

        // Debounce logic
        if (raw != s.lastRaw) {
            s.lastChangeMs = now;
            s.lastRaw = raw;
        }

        if ((now - s.lastChangeMs) >= _debounceMs) {
            if (raw != s.lastDebounced) {
                s.lastDebounced = raw;
                if (raw == false) {
                    // Released: check if it was a short press
                    s.edgeFalling = false;
                } else {
                    // Pressed: register edge and record start time
                    s.edgeFalling = true;
                    s.pressStartMs = now;
                }
            }
        } else {
            s.edgeFalling = false;
        }
    }
}

bool ButtonInput::isPressed(Button btn) {
    if (btn >= BTN_MAX || _pinMap[btn] < 0) return false;
    scan();
    return _buttons[btn].lastDebounced;
}

bool ButtonInput::wasPressed(Button btn) {
    if (btn >= BTN_MAX || _pinMap[btn] < 0) return false;
    scan();
    if (_buttons[btn].edgeFalling) {
        _buttons[btn].edgeFalling = false;
        return true;
    }
    return false;
}

bool ButtonInput::wasHeld(Button btn, uint32_t durationMs) {
    if (btn >= BTN_MAX || _pinMap[btn] < 0) return false;
    scan();
    if (_buttons[btn].lastDebounced) {
        if ((millis() - _buttons[btn].pressStartMs) >= durationMs) {
            // Consume the hold event (only fire once)
            if (_buttons[btn].pressStartMs != 0) {
                _buttons[btn].pressStartMs = 0;
                return true;
            }
        }
    }
    return false;
}

uint8_t ButtonInput::getPressedMask() {
    scan();
    uint8_t mask = 0;
    for (int i = 0; i < 3; i++) {
        if (_buttons[i].lastDebounced) {
            mask |= (1 << i);
        }
    }
    return mask;
}

void ButtonInput::setDebounceMs(uint32_t ms) {
    _debounceMs = ms;
}
