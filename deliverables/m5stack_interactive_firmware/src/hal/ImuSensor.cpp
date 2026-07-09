#include "ImuSensor.h"
#include <cstring>

ImuSensor::ImuSensor() {}
ImuSensor::~ImuSensor() {}

bool ImuSensor::begin(TwoWire& wire) {
    _wire = &wire;
    _wire->begin(21, 22, 400000);  // SDA=21, SCL=22, 400kHz

    return initBMI270();
}

bool ImuSensor::initBMI270() {
    // Verify chip ID
    uint8_t chipId = 0;
    if (!readRegs(BMI270_CHIP_ID, &chipId, 1)) return false;
    if (chipId != BMI270_CHIP_ID_VAL) return false;

    // Soft reset
    writeReg(BMI270_CMD, 0xB6);
    delay(50);

    // Power configuration: disable advanced power save
    writeReg(BMI270_PWR_CONF, 0x00);
    delay(10);

    // Configure accelerometer: ODR=100Hz, range=±4g, filter normal
    writeReg(BMI270_ACC_CONF, 0x19);   // 100Hz, normal
    writeReg(BMI270_ACC_RANGE, 0x02);  // ±4g
    delay(10);

    // Configure gyroscope: ODR=100Hz, range=±500°/s, filter normal
    writeReg(BMI270_GYR_CONF, 0x19);   // 100Hz, normal
    writeReg(BMI270_GYR_RANGE, 0x01);  // ±500°/s
    delay(10);

    // Enable accelerometer and gyroscope
    writeReg(BMI270_PWR_CTRL, 0x0E);
    delay(50);

    _initialized = true;
    _lastSampleUs = micros();
    return true;
}

bool ImuSensor::read(ImuData& out) {
    if (!_initialized) return false;

    uint8_t raw[12];
    if (!readRegs(BMI270_ACC_DATA, raw, 12)) return false;

    // Parse accelerometer data (little-endian, 16-bit per axis)
    int16_t ax_raw = static_cast<int16_t>(raw[1] << 8 | raw[0]);
    int16_t ay_raw = static_cast<int16_t>(raw[3] << 8 | raw[2]);
    int16_t az_raw = static_cast<int16_t>(raw[5] << 8 | raw[4]);

    // Parse gyroscope data
    int16_t gx_raw = static_cast<int16_t>(raw[7] << 8 | raw[6]);
    int16_t gy_raw = static_cast<int16_t>(raw[9] << 8 | raw[8]);
    int16_t gz_raw = static_cast<int16_t>(raw[11] << 8 | raw[10]);

    // Convert to physical units
    // ±4g → 8192 LSB/g, ±500°/s → 62.5 LSB/°/s
    out.ax = static_cast<float>(ax_raw) / 8192.0f;
    out.ay = static_cast<float>(ay_raw) / 8192.0f;
    out.az = static_cast<float>(az_raw) / 8192.0f;

    out.gx = static_cast<float>(gx_raw) / 62.5f;
    out.gy = static_cast<float>(gy_raw) / 62.5f;
    out.gz = static_cast<float>(gz_raw) / 62.5f;

    // Run Madgwick filter
    uint32_t now = micros();
    float dt = static_cast<float>(now - _lastSampleUs) / 1000000.0f;
    _lastSampleUs = now;

    if (dt > 0.001f && dt < 0.1f) {  // Sanity check: 1ms–100ms
        madgwickUpdate(out.gx, out.gy, out.gz, out.ax, out.ay, out.az, dt);
    }

    // Extract Euler angles from quaternion
    float sinr_cosp = 2.0f * (_q0 * _q1 + _q2 * _q3);
    float cosr_cosp = 1.0f - 2.0f * (_q1 * _q1 + _q2 * _q2);
    out.roll = atan2f(sinr_cosp, cosr_cosp) * 180.0f / PI;

    float sinp = 2.0f * (_q0 * _q2 - _q3 * _q1);
    if (fabsf(sinp) >= 1.0f)
        out.pitch = copysignf(90.0f, sinp);
    else
        out.pitch = asinf(sinp) * 180.0f / PI;

    float siny_cosp = 2.0f * (_q0 * _q3 + _q1 * _q2);
    float cosy_cosp = 1.0f - 2.0f * (_q2 * _q2 + _q3 * _q3);
    out.yaw = atan2f(siny_cosp, cosy_cosp) * 180.0f / PI;

    out.temperature = 25.0f;  // BMI270 lacks accurate temp in basic mode
    out.mx = out.my = out.mz = 0.0f;  // BMM150 requires separate init

    return true;
}

bool ImuSensor::isMotionDetected(float threshold) {
    ImuData d;
    if (!read(d)) return false;
    float mag = sqrtf(d.ax * d.ax + d.ay * d.ay + d.az * d.az);
    return fabsf(mag - 1.0f) > threshold;
}

bool ImuSensor::calibrate() {
    if (!_initialized) return false;
    // Zero gyro bias by averaging 100 samples while stationary
    float gxBias = 0, gyBias = 0, gzBias = 0;
    const int samples = 100;
    for (int i = 0; i < samples; i++) {
        uint8_t raw[6];
        readRegs(BMI270_GYR_DATA, raw, 6);
        gxBias += static_cast<float>(static_cast<int16_t>(raw[1] << 8 | raw[0])) / 62.5f;
        gyBias += static_cast<float>(static_cast<int16_t>(raw[3] << 8 | raw[2])) / 62.5f;
        gzBias += static_cast<float>(static_cast<int16_t>(raw[5] << 8 | raw[4])) / 62.5f;
        delay(5);
    }
    gxBias /= samples;
    gyBias /= samples;
    gzBias /= samples;
    // In a full implementation, these biases would be stored and subtracted
    // from each read. For now, we reset the Madgwick filter.
    resetFusion();
    return true;
}

void ImuSensor::resetFusion() {
    _q0 = 1.0f; _q1 = 0.0f; _q2 = 0.0f; _q3 = 0.0f;
}

void ImuSensor::getQuaternion(float& qw, float& qx, float& qy, float& qz) {
    qw = _q0; qx = _q1; qy = _q2; qz = _q3;
}

void ImuSensor::madgwickUpdate(float gx, float gy, float gz,
                                 float ax, float ay, float az, float dt) {
    // Convert gyro to rad/s
    float gxR = gx * DEG_TO_RAD;
    float gyR = gy * DEG_TO_RAD;
    float gzR = gz * DEG_TO_RAD;

    float recipNorm;
    float s0, s1, s2, s3;
    float qDot1, qDot2, qDot3, qDot4;

    // Rate of change of quaternion from gyroscope
    qDot1 = 0.5f * (-_q1 * gxR - _q2 * gyR - _q3 * gzR);
    qDot2 = 0.5f * (_q0 * gxR + _q2 * gzR - _q3 * gyR);
    qDot3 = 0.5f * (_q0 * gyR - _q1 * gzR + _q3 * gxR);
    qDot4 = 0.5f * (_q0 * gzR + _q1 * gyR - _q2 * gxR);

    // Accelerometer-based correction (if not free-fall)
    float norm = sqrtf(ax * ax + ay * ay + az * az);
    if (norm > 0.0f) {
        recipNorm = 1.0f / norm;
        ax *= recipNorm;
        ay *= recipNorm;
        az *= recipNorm;

        // Objective function and Jacobian for Madgwick filter
        float f1 = 2.0f * (_q1 * _q3 - _q0 * _q2) - ax;
        float f2 = 2.0f * (_q0 * _q1 + _q2 * _q3) - ay;
        float f3 = 2.0f * (0.5f - _q1 * _q1 - _q2 * _q2) - az;

        float j11 = 2.0f * _q2;
        float j12 = 2.0f * _q3;
        float j13 = -2.0f * _q0;
        float j14 = -2.0f * _q1;
        float j21 = -2.0f * _q1;
        float j22 = 2.0f * _q0;
        float j23 = 2.0f * _q3;
        float j24 = 2.0f * _q2;
        float j31 = 0.0f;
        float j32 = -4.0f * _q1;
        float j33 = -4.0f * _q2;
        float j34 = 0.0f;

        s0 = -(j11 * f1 + j21 * f2 + j31 * f3);
        s1 = -(j12 * f1 + j22 * f2 + j32 * f3);
        s2 = -(j13 * f1 + j23 * f2 + j33 * f3);
        s3 = -(j14 * f1 + j24 * f2 + j34 * f3);

        recipNorm = invSqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3);
        s0 *= recipNorm;
        s1 *= recipNorm;
        s2 *= recipNorm;
        s3 *= recipNorm;

        qDot1 -= _beta * s0;
        qDot2 -= _beta * s1;
        qDot3 -= _beta * s2;
        qDot4 -= _beta * s3;
    }

    // Integrate
    _q0 += qDot1 * dt;
    _q1 += qDot2 * dt;
    _q2 += qDot3 * dt;
    _q3 += qDot4 * dt;

    // Normalize
    norm = invSqrt(_q0 * _q0 + _q1 * _q1 + _q2 * _q2 + _q3 * _q3);
    _q0 *= norm;
    _q1 *= norm;
    _q2 *= norm;
    _q3 *= norm;
}

float ImuSensor::invSqrt(float x) {
    return 1.0f / sqrtf(x);
}

bool ImuSensor::writeReg(uint8_t reg, uint8_t val) {
    if (!_wire) return false;
    _wire->beginTransmission(0x68);
    _wire->write(reg);
    _wire->write(val);
    return _wire->endTransmission() == 0;
}

bool ImuSensor::readRegs(uint8_t reg, uint8_t* buf, size_t len) {
    if (!_wire) return false;
    _wire->beginTransmission(0x68);
    _wire->write(reg);
    if (_wire->endTransmission(false) != 0) return false;
    size_t read = _wire->requestFrom(0x68, static_cast<uint8_t>(len));
    if (read != len) return false;
    for (size_t i = 0; i < len; i++) {
        buf[i] = _wire->read();
    }
    return true;
}
