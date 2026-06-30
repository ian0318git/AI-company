"""MCP tool registration.

All tool modules are imported and registered here.
Tools are grouped into tiers:

CORE (14 tools):
  - project: project_create, project_list, project_set_active
  - task: task_create, task_list, task_update_status, task_wall
  - idea: idea_capture, idea_refine
  - pipeline: pipeline_create, pipeline_advance
  - hardware: hw_detect_board, hw_build, hw_flash_firmware
  - system: system_health

ADVANCED (remaining tools):
  - team, meeting, memory, knowledge, code, guardrails
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register_all(mcp):
    """Register all tool modules with the FastMCP instance."""
    # Core tools — registered first
    from ai_embedded_company.mcp.tools import project, system

    project.register_tools(mcp)
    system.register_tools(mcp)
    logger.info("Registered CORE tools: project, system")

    # Task + Pipeline tools (created in later sprints — will be no-ops for now)
    _try_register(mcp, "ai_embedded_company.mcp.tools.task", "task")
    _try_register(mcp, "ai_embedded_company.mcp.tools.idea", "idea")
    _try_register(mcp, "ai_embedded_company.mcp.tools.pipeline", "pipeline")
    _try_register(mcp, "ai_embedded_company.mcp.tools.hardware", "hardware")
    _try_register(mcp, "ai_embedded_company.mcp.tools.team", "team")
    _try_register(mcp, "ai_embedded_company.mcp.tools.meeting", "meeting")
    _try_register(mcp, "ai_embedded_company.mcp.tools.memory", "memory")
    _try_register(mcp, "ai_embedded_company.mcp.tools.knowledge", "knowledge")
    _try_register(mcp, "ai_embedded_company.mcp.tools.code", "code")
    _try_register(mcp, "ai_embedded_company.mcp.tools.guardrails", "guardrails")


def _try_register(mcp, module_name: str, label: str):
    """Try to register a tool module; skip if not yet implemented."""
    try:
        mod = __import__(module_name, fromlist=["register_tools"])
        mod.register_tools(mcp)
        logger.info(f"Registered tools: {label}")
    except (ImportError, AttributeError) as e:
        logger.debug(f"Tool module not yet available: {label} ({e})")
