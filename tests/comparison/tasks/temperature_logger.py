"""Task specification and validator for the M5Stack Core S3 Temperature Logger firmware."""

TASK_SPEC = """
Write an Arduino-compatible firmware for the M5Stack Core S3 that:
1. Reads temperature from the internal BMI270 IMU (acceleration only -- simulated temperature)
2. Displays the temperature on the TFT screen (ILI9342C, 320x240)
3. Logs data to the microSD card every 10 seconds
4. Uses the button (GPIO 41) to toggle between Celsius/Fahrenheit
5. Handles errors gracefully (SD card missing, sensor init failure)
6. Prints debug info over Serial at 115200 baud

Deliverables:
- One .ino file with the full firmware
- Brief README with wiring/pinout and build instructions
"""

EXPECTED_DELIVERABLES: list[str] = [
    "Full .ino firmware file implementing all 6 requirements",
    "README with wiring/pinout and build instructions",
]


def validate(result: dict) -> tuple[bool, list[str]]:
    """Validate that the API result contains expected deliverable indicators.

    Checks the response text for presence of key structural elements that a
    correct firmware submission would include.  Returns a (passed, messages)
    tuple where ``passed`` is True only when all checks pass.

    Parameters
    ----------
    result : dict
        Must contain a ``"text"`` key with the full response text from the
        agent (typically ``raw_response["content"][0]["text"]``).

    Returns
    -------
    tuple[bool, list[str]]
        ``(True, [])`` when all checks pass, otherwise ``(False, [...]`` with
        human-readable failure messages.
    """
    messages: list[str] = []
    text: str = result.get("text", "")

    # Check 1: Must contain an .ino file (```cpp ... ``` or ```arduino ... ``` block)
    if "```cpp" not in text and "```arduino" not in text and "```c++" not in text:
        messages.append("No .ino code block found (expected ```cpp or ```arduino)")

    # Check 2: Must reference BMI270 or sensor initialization
    if "BMI270" not in text and "bmi270" not in text.lower():
        # Fallback: check for imu or sensor init keywords
        if "imu" not in text.lower() and "sensor" not in text.lower():
            messages.append("No BMI270 / IMU / sensor reference found")

    # Check 3: Must reference TFT or display
    if "TFT" not in text and "tft" not in text.lower() and "display" not in text.lower() and "ILI9342C" not in text:
        messages.append("No TFT/display reference found (expected ILI9342C or M5GFX)")

    # Check 4: Must reference microSD or SD card
    if "SD" not in text and "sd" not in text.lower() and "microSD" not in text and "micro_sd" not in text:
        messages.append("No microSD/SD card reference found")

    # Check 5: Must reference GPIO 41 or button
    if "GPIO 41" not in text and "gpio41" not in text.lower() and "button" not in text.lower() and "BTN" not in text:
        messages.append("No button / GPIO 41 reference found")

    # Check 6: Must reference Serial or 115200
    if "115200" not in text and "Serial" not in text and "serial" not in text.lower():
        messages.append("No Serial / 115200 baud reference found")

    # Check 7: Must have a README section or markdown heading
    if not any(marker in text for marker in ("# ", "## ", "README", "readme", "Build Instructions", "Wiring")):
        messages.append("No README / documentation section found")

    passed = len(messages) == 0
    return passed, messages
