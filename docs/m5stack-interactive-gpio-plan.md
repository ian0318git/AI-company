# M5Stack CoreS3 & StackChan Interactive — GPIO Pin Assignment Plan

## 1. M5Stack CoreS3 Pin Map

| Peripheral | Interface | Pins | Notes |
|-----------|-----------|------|-------|
| BMI270 IMU | I2C | SDA: GPIO 21, SCL: GPIO 22 | Addr 0x68 |
| BMM150 Magnetometer | I2C | SDA: GPIO 21, SCL: GPIO 22 | Addr 0x10, same bus |
| FT6336U Touch | I2C | SDA: GPIO 21, SCL: GPIO 22 | Addr 0x38, same bus |
| ILI9342C Display | SPI | MOSI: GPIO 23, MISO: GPIO 38, SCK: GPIO 18, CS: GPIO 5, DC: GPIO 15, RST: GPIO 33, BL: GPIO 32 | 320×240 TFT |
| PDM Mic | PDM | DATA: GPIO 34, CLK: GPIO 35 | SPM1423 |
| Button A | GPIO | GPIO 41 | Active low |
| Button B | GPIO | GPIO 42 | Active low |
| Button C | GPIO | GPIO 0 | Active low |
| RGB LED | GPIO | GPIO 27 | SK6812 (NeoPixel) |
| Speaker | DAC | GPIO 25 | I2S DAC |
| **Inter-device UART** | **UART** | **TX: GPIO 13, RX: GPIO 14** | **To StackChan** |
| Power/3.3V | PWR | 3.3V / GND | To StackChan |

## 2. M5Stack StackChan Pin Map

| Peripheral | Interface | Pins | Notes |
|-----------|-----------|------|-------|
| SSD1306 Display | I2C | SDA: GPIO 21, SCL: GPIO 22 | 128×64 OLED |
| Servo (Body) | PWM | GPIO 13 | 50Hz PWM, 0°–180° |
| Servo (Head) | PWM | GPIO 14 | 50Hz PWM, 0°–180° |
| Button | GPIO | GPIO 0 | Active low |
| RGB LED | GPIO | GPIO 27 | SK6812 |
| **Inter-device UART** | **UART** | **RX: GPIO 3, TX: GPIO 1** | **From CoreS3** |

## 3. Inter-Device Communication

### Primary: UART (115200 baud, 8N1)
- **CoreS3 TX (GPIO 13)** → **StackChan RX (GPIO 3)**
- **CoreS3 RX (GPIO 14)** → **StackChan TX (GPIO 1)**
- Common GND required

### Protocol: Simple Binary Frame
```
[0xAA] [len] [cmd] [payload...] [checksum]
```
- `0xAA`: Frame start byte
- `len`: Payload length (1–64 bytes)
- `cmd`: Command ID (1=motion, 2=sensor, 3=game)
- `payload`: Application-specific data
- `checksum`: XOR of all bytes between start and checksum

### Command Set
| Cmd | Direction | Payload | Description |
|-----|-----------|---------|-------------|
| 0x01 | CoreS3→StackChan | [roll°] [pitch°] [yaw°] [buttons] | Motion control data |
| 0x02 | CoreS3→StackChan | [sensor_type] [value_msb] [value_lsb] | Sensor data stream |
| 0x03 | Bidirectional | [game_state] [button_bits] | Game control |
| 0x10 | StackChan→CoreS3 | [status] [battery%] | Heartbeat/status |
| 0xFF | Either | — | Keepalive ping |

## 4. Power Considerations
- CoreS3 powers StackChan via 3.3V output (max 500mA shared)
- StackChan servo power: use external 5V if driving >2 servos simultaneously
- Common GND is mandatory for UART communication
