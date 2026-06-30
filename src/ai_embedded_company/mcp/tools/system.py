"""MCP tools for system health and status."""

from __future__ import annotations

from ai_embedded_company.mcp._base import _api_call
from ai_embedded_company.__init__ import __version__


def register_tools(mcp):
    """Register system tools with the FastMCP instance."""

    @mcp.tool()
    async def system_health() -> dict:
        """Check the health of the AI Embedded Company system.

        Returns API status, database connectivity, and version info.
        Use this to verify the system is operational.
        """
        try:
            result = await _api_call("GET", "/status")
            return {
                "api": result.get("api", "unknown"),
                "database": result.get("database", "unknown"),
                "version": __version__,
            }
        except Exception as e:
            return {
                "api": "unreachable",
                "database": "unknown",
                "version": __version__,
                "error": str(e),
            }

    @mcp.tool()
    async def system_info() -> dict:
        """Get detailed system information.

        Returns version, available tool modules, supported hardware,
        and agent template counts.
        """
        return {
            "name": "AI Embedded Company",
            "version": __version__,
            "description": "Multi-agent embedded systems + full-stack development OS",
            "supported_hardware": [
                {"family": "esp32-s3", "boards": ["m5stack-core-s3", "m5stack-cores3"]},
                {"family": "esp32", "boards": ["m5stack-core2", "esp32-devkit"]},
                {"family": "stm32", "boards": ["stm32f4-discovery", "nucleo-f446re"]},
                {"family": "rp2040", "boards": ["raspberry-pi-pico", "pico-w"]},
                {"family": "nrf52", "boards": ["nrf52840-dk", "seeed-xiao-nrf52840"]},
            ],
            "pipeline_types": [
                "embedded-firmware",
                "embedded-linux",
                "web-fullstack",
                "quick-prototype",
                "research-spike",
            ],
            "agent_templates": 18,
            "active": True,
        }
