#include "UartComm.h"
#include <cstring>

UartComm::UartComm(int uartNum, int txPin, int rxPin)
    : _serial(nullptr)
    , _uartNum(uartNum)
    , _txPin(txPin)
    , _rxPin(rxPin)
{
}

bool UartComm::begin(uint32_t baud) {
    if (_uartNum == 1) {
        _serial = &Serial1;
    } else if (_uartNum == 2) {
        _serial = &Serial2;
    } else {
        return false;
    }

    _serial->begin(baud, SERIAL_8N1, _rxPin, _txPin);
    _serial->setTimeout(DEFAULT_TIMEOUT);
    return true;
}

bool UartComm::sendFrame(uint8_t cmd, const uint8_t* payload, size_t len) {
    if (len > MAX_PAYLOAD) return false;

    uint8_t frame[FRAME_OVERHEAD + MAX_PAYLOAD];
    size_t idx = 0;

    frame[idx++] = FRAME_START;        // 0xAA
    frame[idx++] = static_cast<uint8_t>(len);
    frame[idx++] = cmd;

    if (payload && len > 0) {
        memcpy(&frame[idx], payload, len);
        idx += len;
    }

    // XOR checksum over len + cmd + payload
    uint8_t cs = computeChecksum(&frame[1], idx - 1);
    frame[idx++] = cs;

    size_t written = _serial->write(frame, idx);
    return written == idx;
}

int UartComm::receiveFrame(uint8_t* buf, size_t maxLen, uint32_t timeoutMs) {
    _serial->setTimeout(timeoutMs);

    // Wait for frame start
    uint8_t sync = 0;
    while (_serial->available() > 0 || _serial->readBytes(&sync, 1) == 1) {
        if (sync == FRAME_START) break;
    }
    if (sync != FRAME_START) return -1;

    // Read header: len + cmd
    uint8_t header[2];
    if (_serial->readBytes(header, 2) != 2) return -1;

    uint8_t payloadLen = header[0];
    _lastCmd = header[1];

    if (payloadLen > MAX_PAYLOAD || payloadLen > maxLen) return -1;

    // Read payload
    if (payloadLen > 0) {
        if (_serial->readBytes(buf, payloadLen) != payloadLen) return -1;
    }

    // Read checksum
    uint8_t rxCs = 0;
    if (_serial->readBytes(&rxCs, 1) != 1) return -1;

    // Verify checksum (over len + cmd + payload)
    uint8_t expectedCs = computeChecksum(header, 2);
    expectedCs ^= computeChecksum(buf, payloadLen);
    if (rxCs != expectedCs) return -1;

    return static_cast<int>(payloadLen);
}

void UartComm::flush() {
    _serial->flush();
    while (_serial->available()) _serial->read();
}

uint8_t UartComm::computeChecksum(const uint8_t* data, size_t len) {
    uint8_t cs = 0;
    for (size_t i = 0; i < len; i++) {
        cs ^= data[i];
    }
    return cs;
}
