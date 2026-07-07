
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <cstddef>

// Copy of the relevant parts to avoid header issues
#define EH_RTC_SIGNATURE 0xDEADBEEF
#define EH_CONTEXT_STR_LEN 64

enum class ErrorCode : uint32_t {
    OK = 0,
    HW_I2C_INIT_FAILURE = 0x01000101,
    HW_I2C_DEVICE_NOT_FOUND = 0x01000102,
};

enum class ErrorSeverity : uint8_t {
    DEBUG = 0, INFO = 1, WARNING = 2, ERROR = 3, CRITICAL = 4, FATAL = 5,
};

struct CrashRecord {
    uint32_t signature = 0;
    uint32_t crash_count = 0;
    ErrorCode last_error = ErrorCode::OK;
    ErrorSeverity last_severity = ErrorSeverity::DEBUG;
    uint32_t crash_timestamp_ms = 0;
    uint32_t crash_pc = 0;
    uint32_t exception_cause = 0;
    char task_name[32] = {};
    char context[EH_CONTEXT_STR_LEN] = {};
    uint32_t checksum = 0;

    uint32_t computeChecksum() const {
        const uint32_t* words = reinterpret_cast<const uint32_t*>(this);
        constexpr size_t word_count = sizeof(CrashRecord) / sizeof(uint32_t);
        uint32_t xor_sum = 0;
        for (size_t i = 0; i < word_count; ++i) {
            xor_sum ^= words[i];
        }
        return xor_sum;
    }

    bool isValid() const {
        if (signature != EH_RTC_SIGNATURE) return false;
        uint32_t stored_checksum = checksum;
        const_cast<CrashRecord*>(this)->checksum = 0;
        uint32_t computed = computeChecksum();
        const_cast<CrashRecord*>(this)->checksum = stored_checksum;
        return computed == stored_checksum;
    }

    void updateChecksum() {
        checksum = 0;
        checksum = computeChecksum();
    }
};

int main() {
    printf("sizeof(CrashRecord) = %zu\n", sizeof(CrashRecord));
    printf("word_count = %zu\n", sizeof(CrashRecord) / sizeof(uint32_t));

    // Test 1: value-initialized record
    CrashRecord rec1 = {};
    printf("\n=== Test 1: value-initialized ===\n");
    printf("signature=0x%08X\n", rec1.signature);
    printf("isValid() = %d\n", rec1.isValid());
    printf("computeChecksum() = 0x%08X\n", rec1.computeChecksum());

    // Test 2: with EH_RTC_SIGNATURE
    rec1.signature = EH_RTC_SIGNATURE;
    rec1.updateChecksum();
    printf("\n=== Test 2: signature set, checksum updated ===\n");
    printf("checksum = 0x%08X\n", rec1.checksum);
    printf("isValid() = %d\n", rec1.isValid());

    // Test 3: the rec2 test case
    CrashRecord rec2 = {};
    rec2.signature = EH_RTC_SIGNATURE;
    rec2.crash_count = 3;
    rec2.last_error = ErrorCode::HW_I2C_INIT_FAILURE;
    rec2.last_severity = ErrorSeverity::CRITICAL;
    rec2.crash_timestamp_ms = 5000;
    rec2.crash_pc = 0x42006900;
    rec2.exception_cause = 0xDEAD;
    std::strncpy(rec2.task_name, "main", sizeof(rec2.task_name) - 1);
    std::strncpy(rec2.context, "I2C init failed during boot", sizeof(rec2.context) - 1);
    rec2.updateChecksum();

    printf("\n=== Test 3: rec2 full test ===\n");
    printf("sizeof=%zu, checksum=0x%08X\n", sizeof(CrashRecord), rec2.checksum);
    printf("isValid() = %d\n", rec2.isValid());

    // Show all 32 words
    const uint32_t* w = reinterpret_cast<const uint32_t*>(&rec2);
    for (size_t i = 0; i < sizeof(CrashRecord)/sizeof(uint32_t); ++i) {
        printf("  word[%2zu] = 0x%08X", i, w[i]);
        if (i == 3) printf("  <-- last_severity + padding");
        if (i == 31) printf("  <-- checksum");
        printf("\n");
    }

    // Also show the word 3 value when isValid runs
    uint32_t stored_cs = rec2.checksum;
    const_cast<CrashRecord*>(&rec2)->checksum = 0;
    uint32_t recomputed = rec2.computeChecksum();
    const_cast<CrashRecord*>(&rec2)->checksum = stored_cs;

    printf("stored checksum = 0x%08X\n", stored_cs);
    printf("recomputed     = 0x%08X\n", recomputed);
    printf("match: %s\n", (stored_cs == recomputed) ? "YES" : "NO");

    // Test 4: The exact production code pattern (bare init)
    CrashRecord rec3;
    rec3.signature = EH_RTC_SIGNATURE;
    rec3.crash_count = 3;
    rec3.last_error = ErrorCode::HW_I2C_INIT_FAILURE;
    rec3.last_severity = ErrorSeverity::CRITICAL;
    rec3.crash_timestamp_ms = 5000;
    rec3.crash_pc = 0x42006900;
    rec3.exception_cause = 0xDEAD;
    std::strncpy(rec3.task_name, "main", sizeof(rec3.task_name) - 1);
    std::strncpy(rec3.context, "I2C init failed during boot", sizeof(rec3.context) - 1);
    rec3.updateChecksum();

    printf("\n=== Test 4: bare init (no ={}) ===\n");
    printf("isValid() = %d\n", rec3.isValid());

    // Show word 3
    const uint32_t* w3 = reinterpret_cast<const uint32_t*>(&rec3);
    uint32_t w3_val = w3[3];
    printf("word[3] = 0x%08X  (last_severity byte = 0x%02X)\n", w3_val, *(reinterpret_cast<const uint8_t*>(&rec3) + 12));

    return 0;
}
