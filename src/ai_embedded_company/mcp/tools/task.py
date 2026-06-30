"""MCP tools for task management."""

from __future__ import annotations

from ai_embedded_company.mcp._base import _api_call, _resolve_project_id


def register_tools(mcp):
    """Register task management tools with the FastMCP instance."""

    @mcp.tool()
    async def task_create(
        title: str,
        project_id: str,
        description: str = "",
        priority: str = "medium",
        assigned_agent: str = "",
    ) -> dict:
        """Create a new task on the task wall.

        Args:
            title: Task title (e.g., "Implement I2C driver for BME280")
            project_id: The project UUID
            description: Detailed task description
            priority: Task priority: low, medium, high, critical
            assigned_agent: Agent role to assign (e.g., "embedded-firmware-engineer")
        """
        payload = {
            "project_id": project_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
        if assigned_agent:
            payload["assigned_agent"] = assigned_agent

        return await _api_call("POST", "/api/tasks/", json_data=payload)

    @mcp.tool()
    async def task_list(
        project_id: str = "",
        status: str = "",
    ) -> dict:
        """List tasks, optionally filtered by project and status.

        Args:
            project_id: Filter by project UUID
            status: Filter by status: todo, in_progress, blocked, review, done
        """
        params = {}
        if project_id:
            params["project_id"] = project_id
        if status:
            params["status"] = status
        result = await _api_call("GET", "/api/tasks/", params=params)
        tasks = result if isinstance(result, list) else []
        return {"tasks": tasks, "count": len(tasks)}

    @mcp.tool()
    async def task_wall(project_id: str = "") -> dict:
        """Display the task wall (Kanban-style view) for a project.

        Groups tasks by status: todo, in_progress, blocked, review, done.

        Args:
            project_id: The project UUID
        """
        params = {}
        if project_id:
            params["project_id"] = project_id
        result = await _api_call("GET", "/api/tasks/", params=params)
        all_tasks = result if isinstance(result, list) else []

        # Group by status
        wall = {"todo": [], "in_progress": [], "blocked": [], "review": [], "done": []}
        for t in all_tasks:
            status = t.get("status", "todo")
            if status in wall:
                wall[status].append({
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "priority": t.get("priority"),
                    "assigned_agent": t.get("assigned_agent"),
                })

        return {
            "project_id": project_id or "all",
            "total": len(all_tasks),
            "wall": wall,
            "summary": {s: len(tasks) for s, tasks in wall.items()},
        }

    @mcp.tool()
    async def task_update_status(task_id: str, status: str) -> dict:
        """Update a task's status.

        Args:
            task_id: The task UUID
            status: New status: todo, in_progress, blocked, review, done
        """
        return await _api_call("PATCH", f"/api/tasks/{task_id}/status", params={"status": status})

    @mcp.tool()
    async def task_decompose(task_id: str) -> dict:
        """Suggest subtask breakdown for a large task.

        Analyzes the task description and suggests smaller, implementable subtasks.
        Each subtask targets 1-4 hours of work.

        Args:
            task_id: The task UUID to decompose
        """
        # Get the task
        task = await _api_call("GET", f"/api/tasks/{task_id}")

        title = task.get("title", "")
        description = task.get("description", "")
        project_id = task.get("project_id", "")

        # Generate sensible subtasks based on task content
        # This is a heuristic decomposition — the real decomposition happens
        # when a tech-lead agent uses this tool
        subtasks = _suggest_subtasks(title, description)

        # Create the subtasks
        created = []
        for st in subtasks:
            sub = await _api_call("POST", "/api/tasks/", json_data={
                "project_id": project_id,
                "title": st["title"],
                "description": st.get("description", ""),
                "priority": "medium",
                "parent_task_id": task_id,
            })
            created.append({"id": sub.get("id"), "title": st["title"]})

        return {
            "parent_task_id": task_id,
            "parent_title": title,
            "subtasks": created,
            "message": f"Decomposed into {len(created)} subtasks.",
        }

    @mcp.tool()
    async def task_auto_assign(task_id: str) -> dict:
        """Suggest the best agent for a task based on its description.

        Args:
            task_id: The task UUID
        """
        task = await _api_call("GET", f"/api/tasks/{task_id}")
        title = (task.get("title", "") + " " + task.get("description", "")).lower()

        # Simple keyword-based assignment
        agent_map = {
            "firmware": "embedded-firmware-engineer",
            "driver": "embedded-sensor-driver-dev",
            "i2c": "embedded-sensor-driver-dev",
            "spi": "embedded-sensor-driver-dev",
            "sensor": "embedded-sensor-driver-dev",
            "hardware": "embedded-hardware-engineer",
            "pin": "embedded-hardware-engineer",
            "power": "embedded-hardware-engineer",
            "linux": "embedded-linux-engineer",
            "kernel": "embedded-linux-engineer",
            "mqtt": "embedded-iot-engineer",
            "wifi": "embedded-iot-engineer",
            "ble": "embedded-iot-engineer",
            "ota": "embedded-iot-engineer",
            "frontend": "frontend-developer",
            "backend": "backend-developer",
            "api": "backend-developer",
            "database": "backend-developer",
            "ui": "frontend-developer",
            "docker": "devops-engineer",
            "deploy": "devops-engineer",
            "security": "security-engineer",
            "test": "qa-engineer",
            "doc": "technical-writer",
            "architecture": "software-architect",
            "prototype": "rapid-prototyper",
            "review": "code-reviewer",
        }

        best_match = None
        for keyword, agent in agent_map.items():
            if keyword in title:
                best_match = agent
                break

        return {
            "task_id": task_id,
            "title": task.get("title"),
            "suggested_agent": best_match or "tech-lead",
            "rationale": f"Keyword match: '{best_match}'" if best_match else "No clear match — tech-lead should review and assign.",
        }


def _suggest_subtasks(title: str, description: str) -> list[dict]:
    """Heuristic subtask generation."""
    combined = (title + " " + description).lower()

    # Common patterns
    if "driver" in combined or "i2c" in combined or "spi" in combined:
        return [
            {"title": "Read sensor datasheet and identify registers", "description": "Document key registers, I2C/SPI address, and conversion formulas."},
            {"title": "Implement device init function", "description": "Write init sequence: check chip ID, configure power mode, set measurement params."},
            {"title": "Implement read function", "description": "Write read function: trigger measurement, wait for data-ready, read registers, convert to engineering units."},
            {"title": "Write unit tests", "description": "Test with mocked I2C/SPI: chip ID check, timeout handling, conversion formulas."},
            {"title": "Integrate and test on hardware", "description": "Wire sensor, flash firmware, verify readings against known reference."},
        ]

    if "mqtt" in combined or "wifi" in combined or "cloud" in combined:
        return [
            {"title": "Set up WiFi connection with reconnection logic", "description": "Implement WiFi init, connection, and exponential backoff on disconnect."},
            {"title": "Implement MQTT client", "description": "Connect to broker, set Last Will, subscribe to command topics."},
            {"title": "Implement data publishing", "description": "Format sensor data as JSON, publish on telemetry topic."},
            {"title": "Add OTA update support", "description": "Subscribe to OTA topic, download firmware, verify checksum, apply update."},
        ]

    if "display" in combined or "lcd" in combined or "screen" in combined:
        return [
            {"title": "Initialize display driver", "description": "Set up SPI/I2C for display, configure resolution and rotation."},
            {"title": "Design UI layout", "description": "Define screen regions, font sizes, and update strategy."},
            {"title": "Implement display rendering", "description": "Draw UI elements: text, shapes, sensor values."},
            {"title": "Add touch interaction", "description": "Configure touch controller, handle touch events."},
        ]

    if "web" in combined or "dashboard" in combined or "api" in combined:
        return [
            {"title": "Design data model and API endpoints", "description": "Define database schema and REST API contract."},
            {"title": "Implement backend API", "description": "Create FastAPI routes with validation, error handling, and tests."},
            {"title": "Build frontend pages", "description": "Create React components for main views."},
            {"title": "Integrate frontend with API", "description": "Connect UI to backend, handle loading/error/empty states."},
            {"title": "Deploy to production", "description": "Docker setup, CI/CD pipeline, deploy to server."},
        ]

    # Generic decomposition
    return [
        {"title": f"Research and plan: {title}", "description": "Investigate requirements, gather references, design approach."},
        {"title": f"Core implementation: {title}", "description": "Implement the main functionality with error handling."},
        {"title": f"Testing: {title}", "description": "Write tests and verify on target hardware/platform."},
        {"title": f"Documentation: {title}", "description": "Document the implementation, usage, and any gotchas."},
    ]
