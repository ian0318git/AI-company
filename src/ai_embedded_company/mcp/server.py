"""AI Embedded Company — MCP Server entry point.

Runs as a FastMCP stdio server. All tools delegate to the FastAPI REST API.
The API server is auto-started on first tool call.
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from ai_embedded_company.mcp._autostart import _ensure_api_running, _shutdown_api_server
from ai_embedded_company.mcp.tools import register_all

logger = logging.getLogger(__name__)

# Create the MCP server instance
mcp = FastMCP(
    name="ai-embedded-company",
    instructions=(
        "AI Embedded Systems Company — 嵌入式系統 + 全端開發多智能體協作系統。\n"
        "核心能力: 專案管理、任務拆分、Idea→Pipeline、硬體橋接、團隊協作、知識庫搜尋。\n"
        "支援開發板: M5Stack Core S3 (ESP32-S3), 可擴展至 STM32, RP2040, nRF52 等。\n"
        "開發類型: 嵌入式韌體、Embedded Linux、Web 全端、快速原型、技術調研。"
    ),
)

# Register all tool modules
register_all(mcp)


def main():
    """Entry point: ai-embedded-company-serve"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    logger.info("AI Embedded Company MCP Server starting...")
    _ensure_api_running()

    try:
        mcp.run()
    finally:
        _shutdown_api_server()


if __name__ == "__main__":
    main()
