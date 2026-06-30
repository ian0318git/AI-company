#!/usr/bin/env python3
"""PreToolUse hook — guard against dangerous operations.

Before allowing a tool to execute, verify it doesn't violate safety rules:
- No flashing firmware without explicit confirmation
- No deletion of project files
- No dangerous system commands
"""

from __future__ import annotations

import json
import os
import sys

DANGEROUS_PATTERNS = [
    "rm -rf",
    "format",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",  # fork bomb
]

EMBEDDED_DANGEROUS = [
    "esptool.py write_flash",
    "platformio run --target upload",
    "--target uploadfs",
]


def main():
    """Check the tool call for dangerous operations."""
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "")

    # Read stdin for full tool context
    if not sys.stdin.isatty():
        try:
            tool_input = sys.stdin.read() or tool_input
        except Exception:
            pass

    combined = f"{tool_name} {tool_input}".lower()

    warnings = []

    # Check for system-dangerous commands
    for pattern in DANGEROUS_PATTERNS:
        if pattern in combined:
            warnings.append(f"DANGEROUS: command contains '{pattern}'. This may destroy data.")

    # Check for embedded flash operations
    for pattern in EMBEDDED_DANGEROUS:
        if pattern in combined:
            warnings.append(
                f"FLASH OPERATION: '{pattern}' detected. "
                "Confirm: correct board? correct port? correct firmware?"
            )

    if warnings:
        print("[AI Embedded Company — Guardrails]", file=sys.stderr)
        for w in warnings:
            print(f"  ⚠️  {w}", file=sys.stderr)
        print("", file=sys.stderr)
        # We don't block the operation — just warn. For blocking, exit non-zero.


if __name__ == "__main__":
    main()
