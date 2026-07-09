#pragma once

#include <cstdint>

/**
 * @brief BMI270 IMU + BMM150 Magnetometer abstraction
 *
 * Provides orientation (roll/pitch/yaw) via Madgwick sensor fusion
 * running on the CoreS3 at 100Hz.
 */
class IImuSensor {
public:
    struct ImuData {
        float ax, ay, az;        // Accelerometer (g)
        float gx, gy, gz;        // Gyroscope (degrees/s)
        float mx, my, mz;        // Magnetometer (uT)
        float roll, pitch, yaw;  // Euler angles (degrees)
        float temperature;       // Chip temperature (C)
    };

    virtual ~IImuSensor() = default;

    /** @brief Initialize the sensor on the given I2C bus (Wire1 for CoreS3) */
    virtual bool begin(TwoWire& wire) = 0;

    /** @brief Perform gyroscope calibration (requires stationary device) */
    virtual bool calibrate() = 0;

    /** @brief Read all sensor channels and compute orientation */
    virtual bool read(ImuData& out) = 0;

    /** @brief Check if motion exceeds threshold (g units) */
    virtual bool isMotionDetected(float threshold = 0.5f) = 0;

    /** @brief Reset the Madgwick filter to initial state */
    virtual void resetFusion() = 0;

    /** @brief Get the current quaternion (for 3D rendering) */
    virtual void getQuaternion(float& qw, float& qx, float& qy, float& qz) = 0;
};
