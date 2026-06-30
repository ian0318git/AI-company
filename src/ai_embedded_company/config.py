"""Application configuration via pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for AI Embedded Company."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///data/ai_embedded_company.db"

    # ── API Server ────────────────────────────────────────
    api_host: str = "127.0.0.1"
    api_port: int = 8765

    # ── MCP Server ────────────────────────────────────────
    mcp_server_name: str = "ai-embedded-company"

    # ── Paths ─────────────────────────────────────────────
    data_dir: str = "~/.claude/data/ai-embedded-company"
    agents_dir: str = "~/.claude/agents"
    hooks_dir: str = "~/.claude/hooks/ai-embedded-company"

    # ── Embedded Hardware Defaults ────────────────────────
    default_board: str = "m5stack-core-s3"
    default_port: str = "/dev/ttyACM0"
    default_baudrate: int = 115200
    platformio_baud: int = 921600

    # ── Logging ───────────────────────────────────────────
    log_level: str = "INFO"

    # ── Computed ──────────────────────────────────────────
    @property
    def resolved_data_dir(self) -> Path:
        return Path(self.data_dir).expanduser().resolve()

    @property
    def resolved_agents_dir(self) -> Path:
        return Path(self.agents_dir).expanduser().resolve()

    @property
    def resolved_hooks_dir(self) -> Path:
        return Path(self.hooks_dir).expanduser().resolve()

    @property
    def api_base_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}"

    @property
    def database_path(self) -> Path:
        """Resolved path to the SQLite database file."""
        if self.database_url.startswith("sqlite"):
            # Extract path from sqlite URL
            path_str = self.database_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            p = Path(path_str)
            if not p.is_absolute():
                p = Path.cwd() / p
            return p.resolve()
        return Path(".")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return the singleton Settings instance, creating it on first call."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force a reload of settings (useful in tests)."""
    global _settings
    _settings = Settings()
    return _settings
