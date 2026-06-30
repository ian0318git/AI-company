#!/usr/bin/env python3
"""SubagentStart hook — inject embedded domain rules + hardware constraints.

When a subagent is spawned, this hook injects context about the active project,
target hardware constraints, and relevant safety rules.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

API_BASE = os.environ.get("AI_EMBEDDED_API_URL", "http://127.0.0.1:8765")


def _get(path: str) -> dict | None:
    try:
        req = urllib.request.Request(
            f"{API_BASE}{path}",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def main():
    """Inject embedded domain context into the subagent."""
    subagent_type = os.environ.get("CLAUDE_SUBAGENT_TYPE", "")

    lines = ["[AI Embedded Company — Subagent Context]", ""]

    # Domain-specific rules based on agent type
    if "embedded" in subagent_type.lower():
        lines.append("## Embedded Development Rules")
        lines.append("1. **Memory**: Prefer static allocation. ISR must be short (<50 lines).")
        lines.append("2. **Error Handling**: Check ALL HAL/ESP-IDF return codes.")
        lines.append("3. **ESP32-S3 Gotchas**: ADC2 unavailable when WiFi active. GPIO 46 is strapping pin.")
        lines.append("4. **Power**: Budget <500mA. Use deep sleep for battery devices.")
        lines.append("5. **Testing**: Mock HAL calls for off-target tests. Verify on hardware before 'done'.")
        lines.append("")
        lines.append("## M5Stack Core S3 Quick Reference")
        lines.append("- I2C: SDA=GPIO 8, SCL=GPIO 9 (shared bus with touch, IMU, RTC, PMIC)")
        lines.append("- Display SPI: CS=4, DC=15, MOSI=23, SCLK=18")
        lines.append("- SD SPI: CS=5 (shared MOSI=23, SCLK=18)")
        lines.append("- Grove I2C: SDA=GPIO 1, SCL=GPIO 2")
        lines.append("- Boot button: GPIO 0 (LOW = download mode)")
        lines.append("")

    elif "web" in subagent_type.lower() or "frontend" in subagent_type.lower() or "backend" in subagent_type.lower():
        lines.append("## Web Development Rules")
        lines.append("1. Validate ALL input at API boundary (Pydantic/Zod).")
        lines.append("2. Use parameterized queries — never string-concatenate SQL.")
        lines.append("3. Handle loading, empty, and error states in every component.")
        lines.append("4. API errors: return `{\"error\": \"code\", \"detail\": \"message\"}`.")
        lines.append("")

    # Try to inject active project info
    projects = _get("/api/projects/?status=active")
    if projects and isinstance(projects, list) and len(projects) > 0:
        p = projects[0]
        lines.append(f"## Active Project: {p['name']}")
        if p.get("board_model"):
            lines.append(f"Target Hardware: {p['board_model']} ({p.get('board_family', 'unknown')})")
        lines.append(f"Project ID: {p['id']}")
        lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
