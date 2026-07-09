#pragma once

#include "IImuSensor.h"
#include <Wire.h>

/**
 * @brief BMI270 + BMM150 IMU implementation for M5Stack CoreS3
 *
 * BMI270 address: 0x68
 * BMM150 address: 0x10 (through BMI270 auxiliary I2C)
 * Both share Wire1 (SDA=21, SCL=22)
 */
class ImuSensor : public IImuSensor {
public:
    ImuSensor();
    ~ImuSensor();

    bool begin(TwoWire& wire) override;
    bool calibrate() override;
    bool read(ImuData& out) override;
    bool isMotionDetected(float threshold) override;
    void resetFusion() override;
    void getQuaternion(float& qw, float& qx, float& qy, float& qz) override;

    // BMI270 register map
    static constexpr uint8_t BMI270_CHIP_ID      = 0x00;
    static constexpr uint8_t BMI270_CHIP_ID_VAL   = 0x24;
    static constexpr uint8_t BMI270_PWR_CONF      = 0x7C;
    static constexpr uint8_t BMI270_PWR_CTRL      = 0x7D;
    static constexpr uint8_t BMI270_CMD           = 0x7E;
    static constexpr uint8_t BMI270_ACC_DATA      = 0x0C;
    static constexpr uint8_t BMI270_GYR_DATA      = 0x12;

    static constexpr uint8_t BMI270_ACC_CONF      = 0x40;
    static constexpr uint8_t BMI270_GYR_CONF      = 0x42;
    static constexpr uint8_t BMI270_ACC_RANGE     = 0x41;
    static constexpr uint8_t BMI270_GYR_RANGE     = 0x43;

private:
    TwoWire* _wire = nullptr;
    bool _initialized = false;

    // Madgwick filter state
    float _q0 = 1.0f, _q1 = 0.0f, _q2 = 0.0f, _q3 = 0.0f;
    float _beta = 0.1f;  // filter gain
    uint32_t _lastSampleUs = 0;

    bool writeReg(uint8_t reg, uint8_t val);
    bool readRegs(uint8_t reg, uint8_t* buf, size_t len);
    bool initBMI270();
    void madgwickUpdate(float gx, float gy, float gz, float ax, float ay, float az, float dt);
    float invSqrt(float x);
};
