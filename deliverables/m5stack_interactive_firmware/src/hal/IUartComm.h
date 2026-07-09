#pragma once

#include <cstdint>
#include <cstddef>

/**
 * @brief Abstract UART transport interface
 *
 * Defines the contract for inter-device communication between CoreS3 and StackChan.
 * Uses a framed binary protocol: [0xAA] [len] [cmd] [payload...] [xor_checksum]
 */
class IUartComm {
public:
    virtual ~IUartComm() = default;

    virtual bool begin(uint32_t baud = 115200) = 0;

    /**
     * @brief Send a framed command packet
     * @param cmd Command ID (0x01–0xFF)
     * @param payload Data bytes
     * @param len Payload length (0–64)
     * @return true on successful transmission
     */
    virtual bool sendFrame(uint8_t cmd, const uint8_t* payload, size_t len) = 0;

    /**
     * @brief Receive a framed packet with timeout
     * @param buf Output buffer for payload
     * @param maxLen Buffer capacity
     * @param timeoutMs Max wait in milliseconds
     * @return Payload length on success, -1 on timeout/error
     */
    virtual int receiveFrame(uint8_t* buf, size_t maxLen, uint32_t timeoutMs) = 0;

    /** @brief Flush any buffered data */
    virtual void flush() = 0;

    /** @brief Get the command of the last received frame */
    virtual uint8_t lastCmd() const = 0;

    // Protocol constants
    static constexpr uint8_t FRAME_START = 0xAA;
    static constexpr size_t  MAX_PAYLOAD = 64;
    static constexpr size_t  FRAME_OVERHEAD = 4;  // start + len + cmd + checksum
    static constexpr uint32_t DEFAULT_TIMEOUT = 100;

    // Well-known command IDs
    enum Command : uint8_t {
        CMD_MOTION_CTRL  = 0x01,
        CMD_SENSOR_DATA  = 0x02,
        CMD_GAME_CTRL    = 0x03,
        CMD_HEARTBEAT    = 0x10,
        CMD_BATTERY      = 0x11,
        CMD_KEEPALIVE    = 0xFF,
    };
};
