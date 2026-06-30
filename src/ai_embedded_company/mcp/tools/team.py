"""MCP tools for team management."""

from __future__ import annotations

from ai_embedded_company.mcp._base import _api_call
from ai_embedded_company.types import AgentRole


def register_tools(mcp):
    """Register team management tools with the FastMCP instance."""

    @mcp.tool()
    async def team_create(
        name: str,
        project_id: str,
        members: str = "",
    ) -> dict:
        """Create a new agent team for a project.

        Args:
            name: Team name (e.g., "M5Stack Sensor Team")
            project_id: The project UUID to associate this team with
            members: Comma-separated agent roles (e.g. "firmware-engineer,hardware-engineer,iot-engineer")
        """
        member_list = [m.strip() for m in members.split(",") if m.strip()] if members else []

        # Validate roles
        valid_roles = {r.value for r in AgentRole}
        for m in member_list:
            if m not in valid_roles:
                return {"error": f"Unknown agent role: {m}. Valid roles: {sorted(valid_roles)}"}

        return await _api_call("POST", "/api/teams/", json_data={
            "name": name,
            "project_id": project_id,
            "members": member_list,
        })

    @mcp.tool()
    async def team_list(project_id: str = "") -> dict:
        """List all teams, optionally filtered by project.

        Args:
            project_id: Filter by project UUID (optional)
        """
        params = {}
        if project_id:
            params["project_id"] = project_id
        result = await _api_call("GET", "/api/teams/", params=params)
        return {"teams": result if isinstance(result, list) else []}

    @mcp.tool()
    async def team_status(team_id: str) -> dict:
        """Get detailed status of a team including member workloads.

        Args:
            team_id: The team's UUID
        """
        return await _api_call("GET", f"/api/teams/{team_id}")

    @mcp.tool()
    async def agent_list() -> dict:
        """List all available agent roles with descriptions.

        Returns the full catalog of 18 agent types with their expertise areas.
        """
        return {
            "agents": [
                {
                    "role": "embedded-firmware-engineer",
                    "category": "embedded",
                    "description": "MCU/RTOS 韌體開發 (C/C++), ESP32 系列專家",
                    "expertise": ["C", "C++", "FreeRTOS", "ESP-IDF", "PlatformIO", "I2C/SPI/UART"],
                },
                {
                    "role": "embedded-hardware-engineer",
                    "category": "embedded",
                    "description": "PCB 設計審查, 腳位規劃, 電源管理, 周邊選型",
                    "expertise": ["PCB Design", "Power Management", "Pin Planning", "BOM Selection"],
                },
                {
                    "role": "embedded-linux-engineer",
                    "category": "embedded",
                    "description": "Buildroot/Yocto, Kernel driver, Device Tree",
                    "expertise": ["Linux Kernel", "Device Tree", "Yocto", "Buildroot", "Cross-compilation"],
                },
                {
                    "role": "embedded-iot-engineer",
                    "category": "embedded",
                    "description": "MQTT/CoAP/BLE/WiFi, OTA 更新, 雲端對接",
                    "expertise": ["MQTT", "BLE", "WiFi", "OTA", "AWS IoT", "Azure IoT"],
                },
                {
                    "role": "embedded-sensor-driver-dev",
                    "category": "embedded",
                    "description": "I2C/SPI/UART 感測器驅動, 資料擷取",
                    "expertise": ["I2C", "SPI", "UART", "Sensor Fusion", "Calibration"],
                },
                {
                    "role": "embedded-testing-engineer",
                    "category": "embedded",
                    "description": "HIL 測試, 功耗/記憶體分析, 單元測試",
                    "expertise": ["Unity", "CppUTest", "HIL", "Power Analysis", "CI for Embedded"],
                },
                {
                    "role": "software-architect",
                    "category": "software",
                    "description": "系統架構設計, 技術選型",
                    "expertise": ["System Design", "API Design", "Microservices", "Data Modeling"],
                },
                {
                    "role": "backend-developer",
                    "category": "software",
                    "description": "後端 API 開發 (FastAPI/Node.js/Go)",
                    "expertise": ["FastAPI", "PostgreSQL", "Redis", "Docker", "REST"],
                },
                {
                    "role": "frontend-developer",
                    "category": "software",
                    "description": "前端 UI 開發 (React/Vue)",
                    "expertise": ["React", "Vue", "TypeScript", "Tailwind CSS", "Shadcn UI"],
                },
                {
                    "role": "fullstack-developer",
                    "category": "software",
                    "description": "全端快速原型開發",
                    "expertise": ["React", "FastAPI", "SQLite", "Full-stack", "MVP"],
                },
                {
                    "role": "devops-engineer",
                    "category": "software",
                    "description": "CI/CD, Docker, 部署自動化",
                    "expertise": ["Docker", "GitHub Actions", "Kubernetes", "Terraform", "Monitoring"],
                },
                {
                    "role": "security-engineer",
                    "category": "software",
                    "description": "安全審計 (嵌入式 + Web)",
                    "expertise": ["OWASP", "Secure Boot", "TLS", "Penetration Testing", "Code Audit"],
                },
                {
                    "role": "tech-lead",
                    "category": "management",
                    "description": "技術決策, 任務拆分, 架構審查",
                    "expertise": ["Task Decomposition", "Code Review", "Architecture", "Mentoring"],
                },
                {
                    "role": "project-manager",
                    "category": "management",
                    "description": "進度追蹤, 風險管理, 利害關係人溝通",
                    "expertise": ["Task Tracking", "Risk Management", "Prioritization", "Reporting"],
                },
                {
                    "role": "code-reviewer",
                    "category": "management",
                    "description": "程式碼審查, 品質把關",
                    "expertise": ["Code Review", "Static Analysis", "Best Practices", "Security Review"],
                },
                {
                    "role": "qa-engineer",
                    "category": "management",
                    "description": "測試策略, 品質閘門, 自動化測試",
                    "expertise": ["Test Strategy", "pytest", "Playwright", "Quality Gates", "Bug Triage"],
                },
                {
                    "role": "technical-writer",
                    "category": "management",
                    "description": "文件產生, API 文件, 使用者手冊",
                    "expertise": ["Markdown", "API Docs", "README", "Architecture Docs", "User Guides"],
                },
                {
                    "role": "idea-refiner",
                    "category": "special",
                    "description": "模糊想法 → 具體需求規格",
                    "expertise": ["Requirements", "User Stories", "Scope Definition", "Pipeline Selection"],
                },
                {
                    "role": "rapid-prototyper",
                    "category": "special",
                    "description": "最快路徑做出能跑的原型",
                    "expertise": ["MVP", "Prototyping", "Fast Iteration", "Validation"],
                },
            ]
        }
