#pragma once

#include <cstdint>

/**
 * @brief Abstract display interface
 *
 * Used by CoreS3 (ILI9342C 320x240 TFT) and StackChan (SSD1306 128x64 OLED).
 * Rendering is pixel-buffer based; call update() to flush to screen.
 */
class IDisplay {
public:
    virtual ~IDisplay() = default;

    virtual bool begin() = 0;

    /** @brief Fill entire screen with color (RGB565) */
    virtual void clear(uint16_t color = 0x0000) = 0;

    virtual void drawText(int x, int y, const char* text, uint16_t color = 0xFFFF) = 0;
    virtual void drawRect(int x, int y, int w, int h, uint16_t color) = 0;
    virtual void fillRect(int x, int y, int w, int h, uint16_t color) = 0;
    virtual void drawCircle(int cx, int cy, int r, uint16_t color) = 0;
    virtual void fillCircle(int cx, int cy, int r, uint16_t color) = 0;
    virtual void drawLine(int x0, int y0, int x1, int y1, uint16_t color) = 0;
    virtual void drawTriangle(int x0, int y0, int x1, int y1, int x2, int y2, uint16_t color) = 0;

    /** @brief Flush pixel buffer to display */
    virtual void update() = 0;

    /** @brief Get display dimensions */
    virtual int width() const = 0;
    virtual int height() const = 0;

    /** @brief Set text size multiplier (1 = default) */
    virtual void setTextSize(uint8_t size) = 0;

    /** @brief Draw a UTF-8 character at position */
    virtual void drawChar(int x, int y, unsigned char c, uint16_t color, uint16_t bg, uint8_t size) = 0;
};
