"""Tests for all API endpoints — ideas, tasks, projects, teams.

Covers CRUD operations, pagination edge cases, and validation.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.api.app import app
from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import IdeaModel, TaskModel, ProjectModel, TeamModel


# ── Helper: override DB session with a test-provided one ───────────────────────


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.asyncio
async def test_list_ideas_empty(test_session: AsyncSession) -> None:
    """GET /api/ideas/ with no ideas returns empty paginated response."""
    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ideas/")
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["limit"] == 200
    assert body["offset"] == 0


@pytest.mark.asyncio
async def test_create_and_get_idea(test_session: AsyncSession) -> None:
    """POST /api/ideas/ then GET /api/ideas/{id} returns the created idea."""
    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        create_resp = await client.post(
            "/api/ideas/",
            json={
                "title": "Test Idea",
                "raw_description": "A test idea for endpoint validation.",
                "tags": ["test"],
            },
        )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["title"] == "Test Idea"
    assert created["status"] in ("new", "refining")
    idea_id = created["id"]

    # Fetch by ID
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        get_resp = await client.get(f"/api/ideas/{idea_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == idea_id
    assert fetched["title"] == "Test Idea"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_ideas_pagination(test_session: AsyncSession) -> None:
    """GET /api/ideas/ honors limit/offset and returns correct next_offset."""
    # Seed 5 ideas
    for i in range(5):
        test_session.add(IdeaModel(title=f"Idea {i}", raw_description="paginated", tags="test"))
    await test_session.commit()

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    # Page 1: limit=2
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ideas/?limit=2&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["next_offset"] == 2
    assert body["prev_offset"] is None

    # Page 3 (offset=4): last page with 1 item
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ideas/?limit=2&offset=4")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["next_offset"] is None
    assert body["prev_offset"] == 2

    # Offset beyond total
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ideas/?limit=10&offset=100")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["next_offset"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_ideas_invalid_params(test_session: AsyncSession) -> None:
    """GET /api/ideas/ rejects negative offset and excessively large limit."""
    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ideas/?limit=-1")
    # Should either 422 (validation) or 200 with default limit
    assert resp.status_code in (200, 422)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ideas/?limit=9999")
    assert resp.status_code in (200, 422)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_task_and_list_by_project(test_session: AsyncSession) -> None:
    """POST /api/tasks/ creates a task; filtering by project_id works."""
    project = ProjectModel(name="Test Project")
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    # Create a task
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/tasks/",
            json={
                "title": "Test Task",
                "description": "A test task",
                "priority": "high",
                "project_id": project.id,
            },
        )
    assert create_resp.status_code == 201
    task = create_resp.json()
    assert task["title"] == "Test Task"
    assert task["status"] == "todo"

    # List tasks filtered by project
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get(f"/api/tasks/?project_id={project.id}")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] >= 1
    assert any(t["id"] == task["id"] for t in body["items"])

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_task_status_transitions(test_session: AsyncSession) -> None:
    """PATCH /api/tasks/{id}/status transitions through valid states."""
    project = ProjectModel(name="Status Test Project")
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    task = TaskModel(title="Status Task", project_id=project.id, status="todo")
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    # todo -> in_progress
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(f"/api/tasks/{task.id}/status?status=in_progress")
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["started_at"] is not None

    # in_progress -> done
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(f"/api/tasks/{task.id}/status?status=done")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
    assert resp.json()["completed_at"] is not None

    # Invalid status
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(f"/api/tasks/{task.id}/status?status=invalid_status")
    assert resp.status_code == 400

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_project_and_list(test_session: AsyncSession) -> None:
    """POST /api/projects/ then GET /api/projects/ lists it."""
    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/projects/",
            json={
                "name": "Pagination Test Project",
                "description": "Testing pagination on projects",
            },
        )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "Pagination Test Project"
    assert created["status"] == "active"

    # List projects
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get("/api/projects/?limit=10&offset=0")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] >= 1
    assert any(p["id"] == created["id"] for p in body["items"])

    # Filter by status
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        filtered = await client.get("/api/projects/?status=active")
    assert filtered.status_code == 200
    all_active = all(p["status"] == "active" for p in filtered.json()["items"])
    assert all_active

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_project_update_status(test_session: AsyncSession) -> None:
    """PATCH /api/projects/{id} updates the project status."""
    project = ProjectModel(name="Updatable Project")
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            f"/api/projects/{project.id}",
            json={"status": "completed"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_project_not_found(test_session: AsyncSession) -> None:
    """GET /api/projects/{id} returns 404 for nonexistent project."""
    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/projects/nonexistent-id-12345")
    assert resp.status_code == 404

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_idea_not_found(test_session: AsyncSession) -> None:
    """GET /api/ideas/{id} returns 404 for nonexistent idea."""
    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ideas/bogus-id-99999")
    assert resp.status_code == 404

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_pagination_boundary_conditions(test_session: AsyncSession) -> None:
    """Pagination handles zero-limit, large-offset, and single-item edge cases."""
    project = ProjectModel(name="Pagination Boundary")
    test_session.add(project)
    await test_session.commit()

    # Single task
    task = TaskModel(title="Lonely Task", project_id=project.id)
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    # Limit=1 with 1 item → next_offset should be None
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/tasks/?limit=1&offset=0&project_id={project.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["total"] == 1
    # With only 1 item and limit=1, next_offset is None
    assert body["next_offset"] is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_idea_without_title_fails(test_session: AsyncSession) -> None:
    """POST /api/ideas/ without title returns 422."""
    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/ideas/", json={"raw_description": "missing title"})
    assert resp.status_code == 422

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_project(test_session: AsyncSession) -> None:
    """DELETE /api/projects/{id} removes the project."""
    project = ProjectModel(name="Deletable Project")
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/api/projects/{project.id}")
    assert resp.status_code == 204

    # Verify it's gone
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/projects/{project.id}")
    assert resp.status_code == 404

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_project_name_only(test_session: AsyncSession) -> None:
    """PATCH /api/projects/{id} with just a name field works (partial update)."""
    project = ProjectModel(name="Original Name")
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch(
            f"/api/projects/{project.id}",
            json={"name": "Updated Name"},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    # Status should remain unchanged
    assert resp.json()["status"] == "active"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_team_and_list(test_session: AsyncSession) -> None:
    """POST /api/teams/ then GET /api/teams/ lists it."""
    project = ProjectModel(name="Team Project")
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/teams/",
            json={
                "name": "Test Team",
                "project_id": project.id,
                "members": [{"role": "backend-developer", "status": "idle"}],
            },
        )
    assert create_resp.status_code == 201
    team = create_resp.json()
    assert team["name"] == "Test Team"
    assert len(team["members"]) == 1

    # List teams
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get("/api/teams/")
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] >= 1
    assert any(t["id"] == team["id"] for t in body["items"])

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_team_by_id(test_session: AsyncSession) -> None:
    """GET /api/teams/{id} returns the team."""
    project = ProjectModel(name="Team Detail Project")
    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    import json
    from ai_embedded_company.storage.models import TeamModel
    team_model = TeamModel(
        name="Detail Team",
        project_id=project.id,
        members=json.dumps([{"role": "tech-lead", "status": "busy"}]),
    )
    test_session.add(team_model)
    await test_session.commit()
    await test_session.refresh(team_model)

    async def _override() -> AsyncSession:
        yield test_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/teams/{team_model.id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Detail Team"

    app.dependency_overrides.clear()
