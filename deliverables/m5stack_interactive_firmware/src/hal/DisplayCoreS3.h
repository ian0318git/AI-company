#pragma once

#include "IDisplay.h"
#include <M5GFX.h>

/**
 * @brief CoreS3 display implementation using M5GFX (ILI9342C 320x240)
 */
class DisplayCoreS3 : public IDisplay {
public:
    DisplayCoreS3() : _initialized(false) {}

    bool begin() override {
        _lcd.begin();
        _lcd.setRotation(1);
        _lcd.setBrightness(128);
        _initialized = true;
        return true;
    }

    void clear(uint16_t color = 0x0000) override {
        if (_initialized) _lcd.fillScreen(color);
    }

    void drawText(int x, int y, const char* text, uint16_t color) override {
        if (_initialized) {
            _lcd.setTextColor(color);
            _lcd.drawString(text, x, y);
        }
    }

    void drawRect(int x, int y, int w, int h, uint16_t color) override {
        if (_initialized) _lcd.drawRect(x, y, w, h, color);
    }

    void fillRect(int x, int y, int w, int h, uint16_t color) override {
        if (_initialized) _lcd.fillRect(x, y, w, h, color);
    }

    void drawCircle(int cx, int cy, int r, uint16_t color) override {
        if (_initialized) _lcd.drawCircle(cx, cy, r, color);
    }

    void fillCircle(int cx, int cy, int r, uint16_t color) override {
        if (_initialized) _lcd.fillCircle(cx, cy, r, color);
    }

    void drawLine(int x0, int y0, int x1, int y1, uint16_t color) override {
        if (_initialized) _lcd.drawLine(x0, y0, x1, y1, color);
    }

    void drawTriangle(int x0, int y0, int x1, int y1, int x2, int y2, uint16_t color) override {
        if (_initialized) _lcd.drawTriangle(x0, y0, x1, y1, x2, y2, color);
    }

    void update() override {
        // M5GFX is not buffered in the same way — flush is a no-op.
        // But we can trigger a display refresh if needed.
    }

    int width() const override { return _initialized ? _lcd.width() : 320; }
    int height() const override { return _initialized ? _lcd.height() : 240; }

    void setTextSize(uint8_t size) override {
        if (_initialized) _lcd.setTextSize(size);
    }

    void drawChar(int x, int y, unsigned char c, uint16_t color, uint16_t bg, uint8_t size) override {
        if (_initialized) {
            _lcd.setTextColor(color, bg);
            _lcd.setTextSize(size);
            _lcd.drawChar(c, x, y);
        }
    }

    /** @brief Set backlight brightness (0–255) */
    void setBrightness(uint8_t brightness) {
        if (_initialized) _lcd.setBrightness(brightness);
    }

private:
    M5GFX _lcd;
    bool _initialized;
};
