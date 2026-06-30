"""Foundation tests for Sprint 1 — verify core infrastructure works."""

from __future__ import annotations

import pytest


class TestConfig:
    """Verify settings management."""

    def test_default_settings(self):
        from ai_embedded_company.config import get_settings, reload_settings

        settings = reload_settings()
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 8765
        assert settings.mcp_server_name == "ai-embedded-company"
        assert settings.default_board == "m5stack-core-s3"
        assert settings.api_base_url.startswith("http")  # just checking it resolves

    def test_resolved_paths(self):
        from ai_embedded_company.config import get_settings

        settings = get_settings()
        assert settings.resolved_data_dir is not None
        assert settings.resolved_agents_dir is not None


class TestTypes:
    """Verify shared type definitions."""

    def test_project_create(self):
        from ai_embedded_company.types import ProjectCreate, BoardFamily

        p = ProjectCreate(
            name="test-project",
            description="A test",
            board_family=BoardFamily.ESP32_S3,
            board_model="m5stack-core-s3",
        )
        assert p.name == "test-project"
        assert p.board_family == BoardFamily.ESP32_S3

    def test_task_create(self):
        from ai_embedded_company.types import TaskCreate, TaskPriority, AgentRole

        t = TaskCreate(
            title="Test task",
            project_id="fake-uuid",
            priority=TaskPriority.HIGH,
            assigned_agent=AgentRole.FIRMWARE_ENGINEER,
        )
        assert t.priority == TaskPriority.HIGH
        assert t.assigned_agent == AgentRole.FIRMWARE_ENGINEER

    def test_idea_model(self):
        from ai_embedded_company.types import IdeaCreate

        i = IdeaCreate(
            title="溫濕度監測器",
            raw_description="使用 M5Stack Core S3 做環境監測",
            tags=["m5stack", "sensor", "iot"],
        )
        assert "M5Stack" in i.raw_description
        assert len(i.tags) == 3

    def test_pipeline_phases_exist(self):
        from ai_embedded_company.types import PipelinePhase, PipelineType

        phases = list(PipelinePhase)
        assert len(phases) == 7
        assert PipelinePhase.IDEA in phases
        assert PipelinePhase.DEPLOY in phases

        types = list(PipelineType)
        assert len(types) == 5


class TestStorage:
    """Verify database layer."""

    @pytest.mark.asyncio
    async def test_init_db(self):
        from ai_embedded_company.storage import init_db, close_db

        # Should create tables without error
        await init_db()

        # Should dispose without error
        await close_db()

    @pytest.mark.asyncio
    async def test_create_project(self):
        from ai_embedded_company.storage import init_db, close_db
        from ai_embedded_company.storage.database import _get_sessionmaker
        from ai_embedded_company.storage.models import ProjectModel

        await init_db()

        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            project = ProjectModel(
                name="test-project",
                description="A test project",
                board_family="esp32-s3",
                board_model="m5stack-core-s3",
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)

            assert project.id is not None
            assert project.name == "test-project"

            # Clean up
            await session.delete(project)
            await session.commit()

        await close_db()

    @pytest.mark.asyncio
    async def test_create_and_list_tasks(self):
        from ai_embedded_company.storage import init_db, close_db
        from ai_embedded_company.storage.database import _get_sessionmaker
        from ai_embedded_company.storage.models import ProjectModel, TaskModel
        from sqlalchemy import select

        await init_db()
        sessionmaker = _get_sessionmaker()

        async with sessionmaker() as session:
            # Create project first
            project = ProjectModel(name="task-test", board_family="esp32")
            session.add(project)
            await session.commit()
            await session.refresh(project)

            # Create tasks
            for i in range(3):
                task = TaskModel(
                    project_id=project.id,
                    title=f"Task {i}",
                    priority="medium",
                    status="todo",
                )
                session.add(task)
            await session.commit()

            # List tasks for project
            result = await session.execute(
                select(TaskModel).where(TaskModel.project_id == project.id)
            )
            tasks = result.scalars().all()
            assert len(tasks) == 3

            # Clean up
            for t in tasks:
                await session.delete(t)
            await session.delete(project)
            await session.commit()

        await close_db()


class TestAPIRoutes:
    """Verify API router structure can be imported."""

    def test_app_creation(self):
        from ai_embedded_company.api.app import create_app

        app = create_app()
        assert app.title == "AI Embedded Company API"
        assert len(app.routes) > 0


class TestMCPTools:
    """Verify MCP tools are defined and importable."""

    def test_project_tools_defined(self):
        from ai_embedded_company.mcp.tools.project import register_tools

        assert callable(register_tools)

    def test_system_tools_defined(self):
        from ai_embedded_company.mcp.tools.system import register_tools

        assert callable(register_tools)

    def test_tool_registration(self):
        from ai_embedded_company.mcp.server import mcp

        # The mcp instance should be created
        assert mcp is not None
        assert mcp.name == "ai-embedded-company"
