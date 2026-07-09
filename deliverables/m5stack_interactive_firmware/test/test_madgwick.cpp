/**
 * @file test_madgwick.cpp
 * @brief Unit tests for Madgwick sensor fusion algorithm
 *
 * Tests quaternion math, Euler angle extraction, and filter convergence.
 * Runs on host — no hardware needed.
 */

#include <cstdio>
#include <cassert>
#include <cmath>
#include <cstdint>

// ============================================================
// Madgwick Filter Implementation (standalone for testing)
// ============================================================
class MadgwickFilter {
public:
    float q0 = 1.0f, q1 = 0.0f, q2 = 0.0f, q3 = 0.0f;
    float beta = 0.1f;

    void update(float gx, float gy, float gz, float ax, float ay, float az, float dt) {
        float gxR = gx * M_PI / 180.0f;
        float gyR = gy * M_PI / 180.0f;
        float gzR = gz * M_PI / 180.0f;

        float qDot1 = 0.5f * (-q1 * gxR - q2 * gyR - q3 * gzR);
        float qDot2 = 0.5f * (q0 * gxR + q2 * gzR - q3 * gyR);
        float qDot3 = 0.5f * (q0 * gyR - q1 * gzR + q3 * gxR);
        float qDot4 = 0.5f * (q0 * gzR + q1 * gyR - q2 * gxR);

        float norm = sqrtf(ax * ax + ay * ay + az * az);
        if (norm > 0.0f) {
            float recip = 1.0f / norm;
            ax *= recip; ay *= recip; az *= recip;

            float f1 = 2.0f * (q1 * q3 - q0 * q2) - ax;
            float f2 = 2.0f * (q0 * q1 + q2 * q3) - ay;
            float f3 = 2.0f * (0.5f - q1 * q1 - q2 * q2) - az;

            float s0 = -(2.0f * q2 * f1 + -2.0f * q1 * f2);
            float s1 = -(2.0f * q3 * f1 + 2.0f * q0 * f2 + -4.0f * q1 * f3);
            float s2 = -(-2.0f * q0 * f1 + 2.0f * q3 * f2 + -4.0f * q2 * f3);
            float s3 = -(-2.0f * q1 * f1 + 2.0f * q2 * f2);

            float sNorm = 1.0f / sqrtf(s0*s0 + s1*s1 + s2*s2 + s3*s3);
            s0 *= sNorm; s1 *= sNorm; s2 *= sNorm; s3 *= sNorm;

            qDot1 -= beta * s0;
            qDot2 -= beta * s1;
            qDot3 -= beta * s2;
            qDot4 -= beta * s3;
        }

        q0 += qDot1 * dt;
        q1 += qDot2 * dt;
        q2 += qDot3 * dt;
        q3 += qDot4 * dt;

        float qNorm = 1.0f / sqrtf(q0*q0 + q1*q1 + q2*q2 + q3*q3);
        q0 *= qNorm; q1 *= qNorm; q2 *= qNorm; q3 *= qNorm;
    }

    float roll() const {
        return atan2f(2.0f * (q0 * q1 + q2 * q3),
                      1.0f - 2.0f * (q1 * q1 + q2 * q2)) * 180.0f / M_PI;
    }

    float pitch() const {
        float sinp = 2.0f * (q0 * q2 - q3 * q1);
        if (fabsf(sinp) >= 1.0f) return copysignf(90.0f, sinp);
        return asinf(sinp) * 180.0f / M_PI;
    }

    float yaw() const {
        return atan2f(2.0f * (q0 * q3 + q1 * q2),
                      1.0f - 2.0f * (q2 * q2 + q3 * q3)) * 180.0f / M_PI;
    }
};

// ============================================================
// Test: Initial Quaternion
// ============================================================
void testInitialQuaternion() {
    printf("TEST: Initial quaternion is identity... ");
    MadgwickFilter f;
    assert(fabsf(f.q0 - 1.0f) < 0.001f);
    assert(fabsf(f.q1) < 0.001f);
    assert(fabsf(f.q2) < 0.001f);
    assert(fabsf(f.q3) < 0.001f);
    printf("PASS\n");
}

// ============================================================
// Test: Stationary Orientation (gravity only)
// ============================================================
void testStationaryOrientation() {
    printf("TEST: Stationary with gravity pointing down... ");
    MadgwickFilter f;

    // Simulate stationary: gyro = 0, accel = +1g Z
    float ax = 0.0f, ay = 0.0f, az = 1.0f;
    float gx = 0.0f, gy = 0.0f, gz = 0.0f;

    for (int i = 0; i < 100; i++) {
        f.update(gx, gy, gz, ax, ay, az, 0.01f);
    }

    // After convergence, should be near identity orientation
    // Roll/pitch should be near 0 when accel Z only
    float r = f.roll();
    float p = f.pitch();
    printf("roll=%.2f pitch=%.2f ", r, p);

    // Allow some tolerance due to filter convergence
    assert(fabsf(r) < 5.0f);
    assert(fabsf(p) < 5.0f);
    printf("PASS\n");
}

// ============================================================
// Test: 90 Degree Tilt (gravity on X axis)
// ============================================================
void testTilt90Degrees() {
    printf("TEST: 90-degree tilt (gravity on X axis)... ");
    MadgwickFilter f;

    // Simulate device tilted so gravity reads on X axis
    float ax = 1.0f, ay = 0.0f, az = 0.0f;

    for (int i = 0; i < 200; i++) {
        f.update(0, 0, 0, ax, ay, az, 0.01f);
    }

    float r = f.roll();
    printf("roll=%.2f ", r);

    // Should converge to ~90 degrees (with some tolerance)
    assert(fabsf(r - 90.0f) < 10.0f);
    printf("PASS\n");
}

// ============================================================
// Test: Quaternion Norm Remains Unit
// ============================================================
void testQuaternionNorm() {
    printf("TEST: Quaternion norm stays at 1.0 after updates... ");
    MadgwickFilter f;

    for (int i = 0; i < 1000; i++) {
        // Simulate moderate motion
        float ax = static_cast<float>(rand()) / RAND_MAX * 2 - 1;
        float ay = static_cast<float>(rand()) / RAND_MAX * 2 - 1;
        float az = static_cast<float>(rand()) / RAND_MAX * 2 - 1;
        float gx = static_cast<float>(rand()) / RAND_MAX * 100 - 50;
        float gy = static_cast<float>(rand()) / RAND_MAX * 100 - 50;
        float gz = static_cast<float>(rand()) / RAND_MAX * 100 - 50;
        f.update(gx, gy, gz, ax, ay, az, 0.01f);

        float norm = sqrtf(f.q0*f.q0 + f.q1*f.q1 + f.q2*f.q2 + f.q3*f.q3);
        assert(fabsf(norm - 1.0f) < 0.01f);
    }
    printf("PASS\n");
}

// ============================================================
// Test: Gyroscope Integration (rotation around Y)
// ============================================================
void testGyroIntegration() {
    printf("TEST: Gyroscope integration (90/s around Y)... ");
    MadgwickFilter f;

    // 90/s around Y axis for 1 second
    for (int i = 0; i < 100; i++) {
        f.update(0, 90.0f, 0, 0, 0, 1, 0.01f);
    }

    float p = f.pitch();
    printf("pitch=%.2f (expected ~90) ", p);

    // Pitch should have accumulated ~90 degrees (with drift)
    assert(fabsf(p - 90.0f) < 15.0f);
    printf("PASS\n");
}

// ============================================================
// Main
// ============================================================
int main() {
    printf("=== Madgwick Filter Unit Tests ===\n\n");

    testInitialQuaternion();
    testStationaryOrientation();
    testTilt90Degrees();
    testQuaternionNorm();
    testGyroIntegration();

    printf("\n=== All 5 tests passed! ===\n");
    return 0;
}
