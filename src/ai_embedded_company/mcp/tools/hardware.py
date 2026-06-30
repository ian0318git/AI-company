"""MCP tools for hardware bridge — detect, build, flash, monitor."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from ai_embedded_company.config import get_settings


# ── Known Board Database ─────────────────────────────────────────────────────

KNOWN_BOARDS = {
    # USB VID:PID pairs for common development boards
    ("303a", "1001"): {  # Espressif USB-JTAG
        "model": "ESP32-S3 (generic or M5Stack Core S3)",
        "family": "esp32-s3",
        "chip": "ESP32-S3",
        "programmer": "esptool",
    },
    ("10c4", "ea60"): {  # CP210x (common ESP32 programmer)
        "model": "ESP32 / ESP32-S3 (CP210x UART)",
        "family": "esp32",
        "chip": "ESP32 or ESP32-S3",
        "programmer": "esptool",
    },
    ("1a86", "7523"): {  # CH340 (common Arduino/ESP programmer)
        "model": "Various (CH340 UART)",
        "family": "unknown",
        "chip": "unknown",
        "programmer": "unknown",
    },
    ("2e8a", "0005"): {  # Raspberry Pi Pico (BOOTSEL)
        "model": "Raspberry Pi Pico (BOOTSEL mode)",
        "family": "rp2040",
        "chip": "RP2040",
        "programmer": "picotool",
    },
    ("0483", "3748"): {  # STM32 STLink
        "model": "STM32 (ST-Link/V2)",
        "family": "stm32",
        "chip": "STM32",
        "programmer": "st-flash",
    },
}

# Additional board info (not VID/PID-based)
BOARD_INFO = {
    "m5stack-core-s3": {
        "model": "M5Stack Core S3",
        "family": "esp32-s3",
        "chip": "ESP32-S3",
        "manufacturer": "M5Stack",
        "specs": {
            "mcu": "ESP32-S3 (Xtensa LX7 dual-core, up to 240MHz)",
            "sram": "512KB internal",
            "psram": "8MB Octal PSRAM",
            "flash": "16MB",
            "display": "ILI9342C 320x240 TFT",
            "touch": "FT6336U capacitive",
            "imu": "BMI270 (6-axis) + BMM150 (3-axis magnetometer)",
            "mic": "SPM1423 PDM MEMS",
            "audio": "AW88298 I2S amplifier + speaker",
            "sd_card": "microSD slot (SPI mode)",
            "grove": "I2C Grove port (Port A: GPIO 1/2)",
            "gpio": "GPIO headers (8 pins)",
            "power": "5V USB-C or battery (AXP2101 PMIC)",
            "wifi": "802.11 b/g/n (2.4GHz)",
            "ble": "BLE 5.0",
        },
    },
    "m5stack-cores3": {
        "model": "M5Stack CoreS3",
        "family": "esp32-s3",
        "chip": "ESP32-S3",
        "manufacturer": "M5Stack",
        "specs": {
            "mcu": "ESP32-S3 (Xtensa LX7 dual-core, up to 240MHz)",
            "sram": "512KB internal",
            "psram": "8MB Octal PSRAM",
            "flash": "16MB",
            "display": "ILI9342C 320x240 TFT (M5GFX)",
            "touch": "FT6336U capacitive I2C",
            "imu": "BMI270 + BMM150",
            "mic": "SPM1423 PDM MEMS",
            "sd_card": "microSD (SPI)",
            "grove": "I2C Grove (Port A: SDA=1, SCL=2)",
        },
    },
}


def register_tools(mcp):
    """Register hardware bridge tools with the FastMCP instance."""

    @mcp.tool()
    async def hw_detect_board() -> dict:
        """Detect connected development boards via USB.

        Scans USB/Serial devices and attempts to identify known boards
        by their VID/PID pairs. Returns a list of detected devices.
        """
        devices = []

        # Try to find serial devices
        import glob

        serial_patterns = [
            "/dev/ttyACM*",
            "/dev/ttyUSB*",
            "/dev/cu.usb*",
        ]

        for pattern in serial_patterns:
            for device in glob.glob(pattern):
                devices.append({
                    "device": device,
                    "type": "serial",
                    "identified": _identify_device(device),
                })

        # Try lsusb for VID:PID lookup
        try:
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    devices.append({
                        "device": "USB",
                        "type": "usb",
                        "info": line.strip(),
                    })
        except Exception:
            pass

        # Try PlatformIO device list
        try:
            result = subprocess.run(
                ["platformio", "device", "list", "--json"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                pio_devices = json.loads(result.stdout)
        except Exception:
            pio_devices = []

        return {
            "devices": devices,
            "default_port": get_settings().default_port,
            "platformio_devices": pio_devices if isinstance(pio_devices, list) else [],
            "message": (
                "Use these device paths with hw_build and hw_flash_firmware. "
                "If no devices found, check USB connection and drivers."
            ),
        }

    @mcp.tool()
    async def hw_pinout_get(board_model: str = "") -> dict:
        """Get pinout and hardware specs for a development board.

        Args:
            board_model: Board model name (e.g., "m5stack-core-s3", "m5stack-cores3").
                         Leave empty to list all known boards.
        """
        if not board_model:
            return {
                "known_boards": list(BOARD_INFO.keys()),
                "message": "Use hw_pinout_get with a specific board model for detailed pinout.",
            }

        board = BOARD_INFO.get(board_model.lower())
        if not board:
            return {
                "error": f"Board '{board_model}' not found in database.",
                "known_boards": list(BOARD_INFO.keys()),
            }

        # Load detailed pinout from knowledge base
        pinout = _load_pinout(board_model.lower())

        return {
            "board": board,
            "pinout": pinout,
        }

    @mcp.tool()
    async def hw_build(
        project_dir: str = ".",
        board: str = "",
        framework: str = "arduino",
    ) -> dict:
        """Build (compile) firmware for a target board using PlatformIO.

        Args:
            project_dir: Path to the PlatformIO project (default: current directory)
            board: Target board (e.g., "m5stack-core-s3"). Auto-detects if empty.
            framework: Framework to use: arduino, espidf (default: arduino)
        """
        settings = get_settings()
        board = board or settings.default_board

        project_path = Path(project_dir).resolve()
        if not (project_path / "platformio.ini").exists():
            # Generate a basic platformio.ini if not present
            return {
                "error": "No platformio.ini found.",
                "help": _generate_platformio_ini(board, framework),
                "message": (
                    f"Create a platformio.ini in {project_dir} with the content above, "
                    f"or use the provided template. Then re-run hw_build."
                ),
            }

        try:
            result = subprocess.run(
                ["platformio", "run", "-e", board],
                cwd=str(project_path),
                capture_output=True, text=True, timeout=120,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout,
                "errors": result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr,
                "board": board,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Build timed out after 120 seconds.",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "PlatformIO not found. Install it with: pip install platformio",
            }

    @mcp.tool()
    async def hw_flash_firmware(
        project_dir: str = ".",
        board: str = "",
        port: str = "",
        baud: int = 0,
    ) -> dict:
        """Flash (upload) firmware to a connected development board.

        Args:
            project_dir: Path to the PlatformIO project (default: current directory)
            board: Target board (e.g., "m5stack-core-s3")
            port: Serial port (e.g., "/dev/ttyACM0"). Auto-detects if empty.
            baud: Upload baud rate. Uses default if 0.
        """
        settings = get_settings()
        board = board or settings.default_board
        baud = baud or settings.platformio_baud

        project_path = Path(project_dir).resolve()

        # Build upload command
        cmd = ["platformio", "run", "-e", board, "--target", "upload"]

        if port:
            cmd.extend(["--upload-port", port])

        # Set monitor speed
        env = os.environ.copy()
        env["PLATFORMIO_UPLOAD_SPEED"] = str(baud)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True, text=True, timeout=120,
                env=env,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout,
                "errors": result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr,
                "board": board,
                "port": port or "auto",
                "message": "Flash complete!" if result.returncode == 0 else "Flash failed. Check errors.",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Flash timed out. Check board connection and try again.",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "PlatformIO not found. Install it with: pip install platformio",
            }

    @mcp.tool()
    async def hw_serial_monitor(
        port: str = "",
        baud: int = 0,
        duration: int = 10,
    ) -> dict:
        """Read serial output from a connected device.

        Args:
            port: Serial port (e.g., "/dev/ttyACM0")
            baud: Baud rate (default: 115200)
            duration: How many seconds to capture (default: 10, max: 60)
        """
        settings = get_settings()
        port = port or settings.default_port
        baud = baud or settings.default_baudrate
        duration = min(max(duration, 1), 60)

        try:
            result = subprocess.run(
                ["platformio", "device", "monitor", "--port", port, "--baud", str(baud)],
                capture_output=True, text=True, timeout=duration + 5,
            )
            return {
                "port": port,
                "baud": baud,
                "duration_seconds": duration,
                "output": result.stdout if result.stdout else result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "port": port,
                "baud": baud,
                "duration_seconds": duration,
                "output": "(timeout — no data or monitor still running)",
            }
        except FileNotFoundError:
            return {
                "error": "PlatformIO not found. Install it: pip install platformio",
                "alternative": f"Manual: screen {port} {baud}",
            }

    @mcp.tool()
    async def hw_device_info(board_model: str = "") -> dict:
        """Get detailed hardware information for a development board.

        Args:
            board_model: Board model (e.g., "m5stack-core-s3")
        """
        if not board_model:
            return {"known_boards": list(BOARD_INFO.keys())}

        board = BOARD_INFO.get(board_model.lower())
        if not board:
            return {"error": f"Unknown board: {board_model}", "known": list(BOARD_INFO.keys())}

        pinout = _load_pinout(board_model.lower())
        return {
            "board": board,
            "pinout": pinout,
        }


# ── Helpers ──────────────────────────────────────────────────────────────────


def _identify_device(device_path: str) -> dict:
    """Try to identify a serial device."""
    # Try udevadm for device info
    try:
        result = subprocess.run(
            ["udevadm", "info", "--query=property", "--name=" + device_path],
            capture_output=True, text=True, timeout=5,
        )
        props = {}
        for line in result.stdout.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                props[k] = v

        vid = props.get("ID_VENDOR_ID", "").lower()
        pid = props.get("ID_MODEL_ID", "").lower()

        if (vid, pid) in KNOWN_BOARDS:
            return KNOWN_BOARDS[(vid, pid)]

        return {"vendor_id": vid, "product_id": pid, "model": props.get("ID_MODEL", "unknown")}
    except Exception:
        return {}


def _load_pinout(board: str) -> dict:
    """Load pinout data from the knowledge base."""
    kb_dir = Path(__file__).parent.parent.parent / "knowledge"
    kb_file = kb_dir / f"{board}.json"

    if kb_file.exists():
        try:
            return json.loads(kb_file.read_text())
        except (json.JSONDecodeError, IOError):
            pass

    # Fallback: basic pinout for M5Stack Core S3
    if "m5stack" in board and "s3" in board:
        return {
            "description": "M5Stack Core S3 pinout (partial — full knowledge base being built)",
            "reference": "https://docs.m5stack.com/en/core/CoreS3",
            "power_pins": {
                "5V": "USB-C VBUS or battery",
                "3.3V": "Internal regulator output",
                "GND": "Common ground",
            },
            "grove_port_a": {
                "connector": "Grove (HY2.0-4P)",
                "sda": "GPIO 1",
                "scl": "GPIO 2",
                "vcc": "5V",
                "gnd": "GND",
            },
            "gpio_headers": "8-pin GPIO header (G1, G2, G3, G4, G5, G6, G7, G8)",
            "important_pins": {
                "GPIO 0": "Boot button (pull LOW to enter download mode)",
                "GPIO 46": "Strapping pin — do not use as GPIO",
                "ADC1": "Available for analog read (ADC2 conflicts with WiFi)",
            },
            "protocol_notes": {
                "I2C": "Built-in pull-ups on Grove port. For external I2C, add 4.7kΩ pull-ups to 3.3V.",
                "SPI": "Use VSPI (GPIO 36=MISO, 35=MOSI, 37=SCK) or any free GPIOs.",
                "UART": "USB-C uses built-in USB-Serial. Extra UART on GPIO 17(TX)/18(RX).",
            },
        }

    return {"description": f"Pinout for {board} — load full knowledge base for details."}


def _generate_platformio_ini(board: str, framework: str) -> str:
    """Generate a basic platformio.ini template."""
    return f"""[env:{board}]
platform = espressif32
board = {board}
framework = {framework}
monitor_speed = 115200
upload_speed = 921600
board_build.flash_mode = qio
build_flags =
    -D CORE_DEBUG_LEVEL=0
lib_deps =
    m5stack/M5Unified
    m5stack/M5GFX
"""
