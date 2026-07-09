#pragma once

#include "IUartComm.h"
#include <HardwareSerial.h>

/**
 * @brief Concrete UART communicator using ESP32 HardwareSerial
 *
 * CoreS3: TX=GPIO13, RX=GPIO14, UART_NUM_2
 * StackChan: TX=GPIO1, RX=GPIO3, UART_NUM_1 (default Serial1)
 */
class UartComm : public IUartComm {
public:
    /**
     * @param uartNum ESP32 UART number (1 or 2)
     * @param txPin TX GPIO pin
     * @param rxPin RX GPIO pin
     */
    UartComm(int uartNum, int txPin, int rxPin);

    bool begin(uint32_t baud) override;
    bool sendFrame(uint8_t cmd, const uint8_t* payload, size_t len) override;
    int receiveFrame(uint8_t* buf, size_t maxLen, uint32_t timeoutMs) override;
    void flush() override;
    uint8_t lastCmd() const override { return _lastCmd; }

private:
    HardwareSerial* _serial;
    int _uartNum;
    int _txPin;
    int _rxPin;
    uint8_t _lastCmd = 0;

    static uint8_t computeChecksum(const uint8_t* data, size_t len);
};
