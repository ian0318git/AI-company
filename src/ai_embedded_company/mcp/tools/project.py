"""MCP tools for project management."""

from __future__ import annotations

from ai_embedded_company.mcp._base import _api_call


def register_tools(mcp):
    """Register project management tools with the FastMCP instance."""

    @mcp.tool()
    async def project_create(
        name: str,
        description: str = "",
        board_family: str = "unknown",
        board_model: str = "",
    ) -> dict:
        """Create a new embedded/software project.

        Use this at the start of any new idea or development effort.
        The project becomes the container for all tasks, ideas, and pipeline runs.

        Args:
            name: Project name (e.g., "m5stack-env-monitor")
            description: What this project aims to build
            board_family: Target hardware family if known (esp32, esp32-s3, stm32, rp2040, nrf52, unknown)
            board_model: Specific board model (e.g., "m5stack-core-s3")
        """
        return await _api_call("POST", "/api/projects/", json_data={
            "name": name,
            "description": description,
            "board_family": board_family,
            "board_model": board_model,
        })

    @mcp.tool()
    async def project_list(status: str = "") -> dict:
        """List all projects, optionally filtered by status.

        Args:
            status: Filter by status (active, paused, completed, archived). Empty = all.
        """
        params = {}
        if status:
            params["status"] = status
        result = await _api_call("GET", "/api/projects/", params=params)
        return {"projects": result if isinstance(result, list) else []}

    @mcp.tool()
    async def project_get(project_id: str) -> dict:
        """Get detailed information about a specific project.

        Args:
            project_id: The project's UUID
        """
        return await _api_call("GET", f"/api/projects/{project_id}")

    @mcp.tool()
    async def project_set_active(project_id: str) -> dict:
        """Set a project as the currently active context.

        Subsequent tool calls will default to this project.

        Args:
            project_id: The project's UUID
        """
        # Verify the project exists
        result = await _api_call("GET", f"/api/projects/{project_id}")
        result["_active"] = True
        return result
