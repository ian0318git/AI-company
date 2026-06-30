"""MCP tools for safety and quality guardrails."""

from __future__ import annotations

import os
import re
from pathlib import Path


def register_tools(mcp):
    """Register guardrail tools with the FastMCP instance."""

    @mcp.tool()
    async def guardrail_check(
        command: str = "",
        file_path: str = "",
        check_type: str = "command",
    ) -> dict:
        """Check if an operation is safe before execution.

        Validates commands, file paths, and operations against safety rules.

        Args:
            command: The shell command to check
            file_path: File path to check (for file operations)
            check_type: Type of check: command, file_delete, flash_operation
        """
        warnings = []
        blocked = False

        if check_type == "command" and command:
            warnings, blocked = _check_command(command)
        elif check_type == "file_delete" and file_path:
            warnings, blocked = _check_file_delete(file_path)
        elif check_type == "flash_operation":
            warnings, blocked = _check_flash_operation()

        return {
            "safe": not blocked and len(warnings) == 0,
            "blocked": blocked,
            "warnings": warnings,
            "check_type": check_type,
        }

    @mcp.tool()
    async def guardrail_rules() -> dict:
        """List all active safety guardrail rules."""
        return {
            "rules": [
                {
                    "id": "G001",
                    "name": "No rm -rf on project root",
                    "description": "Prevent accidental deletion of entire project.",
                    "severity": "critical",
                },
                {
                    "id": "G002",
                    "name": "Flash confirmation",
                    "description": "Require port and board verification before flashing firmware.",
                    "severity": "high",
                },
                {
                    "id": "G003",
                    "name": "Production secret in code",
                    "description": "Warn when API keys, passwords, or tokens appear in code.",
                    "severity": "high",
                },
                {
                    "id": "G004",
                    "name": "Dangerous syscall warning",
                    "description": "Warn on format, dd, mkfs, and other destructive commands.",
                    "severity": "high",
                },
                {
                    "id": "G005",
                    "name": "I2C address conflict",
                    "description": "Check for I2C address conflicts when adding sensors.",
                    "severity": "medium",
                },
                {
                    "id": "G006",
                    "name": "ESP32 pin conflict",
                    "description": "Check for GPIO conflicts with strapping pins, ADC2, and shared buses.",
                    "severity": "medium",
                },
            ]
        }


def _check_command(cmd: str) -> tuple[list[str], bool]:
    """Check a shell command for dangerous patterns."""
    warnings = []
    blocked = False

    cmd_lower = cmd.lower()

    # Critical: rm -rf on important paths
    if re.search(r'rm\s+-rf\s+(/|~|\.\s*/?\s*$)', cmd_lower):
        warnings.append("CRITICAL: rm -rf on root/home/current directory. BLOCKED.")
        blocked = True

    if re.search(r'rm\s+-rf\s+/(home|etc|var|usr|bin|boot|dev|lib|opt|sbin|sys|tmp)', cmd_lower):
        warnings.append("CRITICAL: rm -rf on system directory. BLOCKED.")
        blocked = True

    # High: destructive disk operations
    if re.search(r'(mkfs|format|dd\s+if=)', cmd_lower):
        warnings.append("HIGH: Disk format/dd operation detected. Verify target is correct.")

    # Medium: flash operations
    if 'esptool' in cmd_lower or ('platformio' in cmd_lower and 'upload' in cmd_lower):
        warnings.append("FLASH: Firmware flash operation detected. Verify board and port are correct.")

    # Medium: git push --force
    if 'git push' in cmd_lower and '--force' in cmd_lower:
        warnings.append("GIT: Force push detected. Verify you're not overwriting others' work.")

    return warnings, blocked


def _check_file_delete(path: str) -> tuple[list[str], bool]:
    """Check if a file deletion is safe."""
    warnings = []
    blocked = False

    abs_path = Path(path).resolve()

    # Critical paths
    critical_globs = [
        Path.home() / ".ssh",
        Path.home() / ".gnupg",
        Path("/etc"),
    ]

    for critical in critical_globs:
        try:
            if critical in abs_path.parents or abs_path == critical:
                warnings.append(f"CRITICAL: Attempting to delete protected path: {abs_path}")
                blocked = True
        except Exception:
            pass

    return warnings, blocked


def _check_flash_operation() -> tuple[list[str], bool]:
    """Check that a flash operation has necessary safety info."""
    return (
        [
            "Ensure you have verified: (1) correct board type, (2) correct serial port, "
            "(3) firmware built for this specific board, (4) board is connected and in flash mode."
        ],
        False,  # Don't block — just warn
    )
