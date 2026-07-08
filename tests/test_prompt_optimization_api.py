"""API-level integration tests for prompt optimization endpoints.

Exercises each endpoint against a fresh in-memory SQLite database
per test class through the FastAPI TestClient.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ai_embedded_company.api.app import app
from ai_embedded_company.storage import Base, get_session


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop for async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """TestClient with a fresh in-memory SQLite database per test."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_tables())

    async def _get_session_override() -> AsyncIterator[AsyncSession]:
        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


class TestTemplateAPI:
    """Integration tests for /api/prompts/templates CRUD."""

    def test_create_and_list_templates(self, client):
        resp = client.post("/api/prompts/templates", json={
            "agent_role": "backend-developer",
            "pipeline_type": "web-fullstack",
            "template_name": "API builder",
            "template_body": "Build a REST API for {feature}. Use FastAPI.",
            "token_count": 10,
            "tags": '["fastapi", "rest"]',
        })
        # API returns 201 Created
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["template_name"] == "API builder"
        assert data["agent_role"] == "backend-developer"
        assert data["status"] == "active"
        assert data["version"] == 1
        tmpl_id = data["id"]

        list_resp = client.get("/api/prompts/templates")
        assert list_resp.status_code == 200
        ids = [t["id"] for t in list_resp.json()]
        assert tmpl_id in ids

    def test_get_template_by_id(self, client):
        create_resp = client.post("/api/prompts/templates", json={
            "agent_role": "frontend-developer",
            "template_name": "React component",
            "template_body": "Build a React component for {feature}.",
            "token_count": 8,
        })
        tmpl_id = create_resp.json()["id"]

        get_resp = client.get(f"/api/prompts/templates/{tmpl_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["template_name"] == "React component"

    def test_get_template_returns_404_for_missing(self, client):
        resp = client.get("/api/prompts/templates/nonexistent-id")
        assert resp.status_code == 404

    def test_list_templates_filter_by_agent_role(self, client):
        client.post("/api/prompts/templates", json={
            "agent_role": "qa-engineer",
            "template_name": "QA test plan",
            "template_body": "Write tests for {feature}.",
            "token_count": 6,
        })
        client.post("/api/prompts/templates", json={
            "agent_role": "tech-lead",
            "template_name": "Task breakdown",
            "template_body": "Decompose {feature} into sub-tasks.",
            "token_count": 8,
        })

        qa_list = client.get("/api/prompts/templates?agent_role=qa-engineer")
        assert all(t["agent_role"] == "qa-engineer" for t in qa_list.json())

    def test_create_template_tracks_version(self, client):
        create_resp = client.post("/api/prompts/templates", json={
            "agent_role": "devops-engineer",
            "template_name": "deploy script",
            "template_body": "Deploy {feature} to staging.",
            "token_count": 7,
        })
        assert create_resp.json()["version"] == 1


class TestExperimentAPI:
    """Integration tests for /api/prompts/experiments."""

    def test_create_and_list_experiments(self, client):
        ctrl = client.post("/api/prompts/templates", json={
            "agent_role": "backend-developer",
            "template_name": "control",
            "template_body": "Build {feature}.",
            "token_count": 3,
        }).json()
        var = client.post("/api/prompts/templates", json={
            "agent_role": "backend-developer",
            "template_name": "variant",
            "template_body": "Build {feature} with tests first.",
            "token_count": 7,
        }).json()

        resp = client.post("/api/prompts/experiments", json={
            "experiment_name": "Backend concise vs standard",
            "control_template_id": ctrl["id"],
            "variant_template_id": var["id"],
            "target_agent_role": "backend-developer",
            "target_task_types": '["backend"]',
            "sample_size_target": 20,
        })
        assert resp.status_code == 201, resp.text
        exp = resp.json()
        assert exp["status"] == "running"
        assert exp["target_agent_role"] == "backend-developer"

        list_resp = client.get("/api/prompts/experiments")
        assert list_resp.status_code == 200
        ids = [e["id"] for e in list_resp.json()]
        assert exp["id"] in ids

    def test_conclude_experiment(self, client):
        ctrl = client.post("/api/prompts/templates", json={
            "agent_role": "qa-engineer",
            "template_name": "control-qa",
            "template_body": "QA: test {feature}.",
            "token_count": 4,
        }).json()
        var = client.post("/api/prompts/templates", json={
            "agent_role": "qa-engineer",
            "template_name": "variant-qa",
            "template_body": "QA: test {feature} edge cases.",
            "token_count": 6,
        }).json()

        exp = client.post("/api/prompts/experiments", json={
            "experiment_name": "QA concise vs standard",
            "control_template_id": ctrl["id"],
            "variant_template_id": var["id"],
            "target_agent_role": "qa-engineer",
            "sample_size_target": 10,
        }).json()

        conclude = client.post(f"/api/prompts/experiments/{exp['id']}/conclude")
        assert conclude.status_code == 200
        assert conclude.json()["status"] == "complete"


class TestResultsAPI:
    """Integration tests for logging and retrieving prompt results."""

    def test_log_and_list_results(self, client):
        tmpl = client.post("/api/prompts/templates", json={
            "agent_role": "backend-developer",
            "template_name": "perf-test",
            "template_body": "Build {feature}.",
            "token_count": 3,
        }).json()

        log_resp = client.post("/api/prompts/results", json={
            "task_id": "test-task-1",
            "template_id": tmpl["id"],
            "agent_role": "backend-developer",
            "tokens_used": 1500,
            "completion_seconds": 45.2,
            "task_status": "done",
            "arm": "control",
        })
        assert log_resp.status_code == 201, log_resp.text
        result = log_resp.json()
        assert result["tokens_used"] == 1500
        assert result["arm"] == "control"

        list_resp = client.get(f"/api/prompts/results?template_id={tmpl['id']}")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

    def test_log_result_with_variant_arm(self, client):
        tmpl = client.post("/api/prompts/templates", json={
            "agent_role": "tech-lead",
            "template_name": "tl-test",
            "template_body": "Lead: {feature}.",
            "token_count": 3,
        }).json()

        log_resp = client.post("/api/prompts/results", json={
            "task_id": "test-task-2",
            "template_id": tmpl["id"],
            "agent_role": "tech-lead",
            "tokens_used": 3200,
            "completion_seconds": 120.0,
            "task_status": "done",
            "arm": "variant",
        })
        assert log_resp.status_code == 201, log_resp.text
        assert log_resp.json()["arm"] == "variant"


class TestInsightsAPI:
    """Integration tests for optimization insights."""

    def test_generate_insights(self, client):
        tmpl = client.post("/api/prompts/templates", json={
            "agent_role": "backend-developer",
            "template_name": "insight-test",
            "template_body": "Build {feature} with FastAPI.",
            "token_count": 5,
        }).json()

        for i in range(8):
            client.post("/api/prompts/results", json={
                "task_id": f"task-{i}",
                "template_id": tmpl["id"],
                "agent_role": "backend-developer",
                "tokens_used": 1000 + i * 50,
                "completion_seconds": 40.0 + i * 2,
                "task_status": "done",
                "arm": "control",
            })

        gen = client.post("/api/prompts/insights/generate")
        assert gen.status_code == 200

        list_resp = client.get("/api/prompts/insights")
        assert list_resp.status_code == 200


class TestROIAPI:
    """Integration tests for ROI endpoint."""

    def test_roi_with_data(self, client):
        tmpl = client.post("/api/prompts/templates", json={
            "agent_role": "backend-developer",
            "template_name": "roi-test",
            "template_body": "Build {feature}.",
            "token_count": 3,
        }).json()

        for i in range(5):
            client.post("/api/prompts/results", json={
                "task_id": f"roi-task-{i}",
                "template_id": tmpl["id"],
                "agent_role": "backend-developer",
                "tokens_used": 1000,
                "completion_seconds": 50.0,
                "task_status": "done",
                "arm": "control",
            })

        roi = client.get("/api/prompts/roi")
        assert roi.status_code == 200
        assert roi.json()["total_results"] >= 5

    def test_roi_with_no_data_returns_valid_structure(self, client):
        roi = client.get("/api/prompts/roi")
        assert roi.status_code == 200
        data = roi.json()
        assert "total_results" in data
        assert "avg_tokens_per_task" in data
        assert "avg_seconds_per_task" in data
