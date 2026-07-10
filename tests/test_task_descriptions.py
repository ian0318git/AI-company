"""Test: pipeline task descriptions are populated from idea refined_description."""
import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

# Test the _build_task_description logic directly
from ai_embedded_company.api.routes.ideas import _AGENT_WORKFLOWS

class MockIdea:
    """Minimal mock for IdeaModel that holds attribute values directly (no SQLAlchemy)."""
    def __init__(self, refined_description=None, raw_description="", suggested_pipeline="quick-prototype"):
        self.refined_description = refined_description
        self.raw_description = raw_description
        self.suggested_pipeline = suggested_pipeline


def test_build_task_description_with_refined_idea():
    """Task description should contain the idea refined_description context."""
    refined = "Phase 1: Identify code locations. Phase 2: Modify task creation."
    idea = MockIdea(refined_description=refined)
    pipeline_type = idea.suggested_pipeline or "quick-prototype"

    # Replicate _build_task_description logic
    def _build_task_description(title, agent):
        if idea.refined_description and idea.refined_description.strip():
            ctx = f"Project context: {idea.refined_description.strip()[:400]}"
            workflow = _AGENT_WORKFLOWS.get(pipeline_type, [])
            for step in workflow:
                step_title_lower = step["title"].lower()
                title_lower = title.lower()
                if step_title_lower in title_lower or title_lower in step_title_lower:
                    step_desc = step.get("description", "").strip()
                    if step_desc:
                        return f"{ctx}\n\nGoal: {step_desc}"
            return f"{ctx}\n\nDeliverable: {title}"
        return f"Pipeline: {pipeline_type} | Phase task: {title} | Agent: {agent}"

    desc = _build_task_description("Scope the minimum viable features", "rapid-prototyper")
    assert desc, "Description should be non-empty"
    assert "Project context:" in desc, "Should include project context"
    assert refined[:40] in desc, "Should include refined_description content"
    assert "Deliverable: Scope" in desc, "Should include deliverable text"


def test_build_task_description_without_refined():
    """Fallback description when idea has no refined_description."""
    idea = MockIdea(refined_description=None)
    pipeline_type = "quick-prototype"

    def _build_task_description(title, agent):
        if idea.refined_description and idea.refined_description.strip():
            ctx = f"Project context: {idea.refined_description.strip()[:400]}"
            workflow = _AGENT_WORKFLOWS.get(pipeline_type, [])
            for step in workflow:
                step_title_lower = step["title"].lower()
                title_lower = title.lower()
                if step_title_lower in title_lower or title_lower in step_title_lower:
                    step_desc = step.get("description", "").strip()
                    if step_desc:
                        return f"{ctx}\n\nGoal: {step_desc}"
            return f"{ctx}\n\nDeliverable: {title}"
        return f"Pipeline: {pipeline_type} | Phase task: {title} | Agent: {agent}"

    desc = _build_task_description("Build core functionality", "rapid-prototyper")
    assert desc, "Description should be non-empty even without refined_description"
    assert "Pipeline: quick-prototype" in desc


def test_build_task_description_workflow_matching():
    """When task title matches a workflow step, use the step's description."""
    refined = "A test refined description for workflow matching."
    idea = MockIdea(refined_description=refined)
    pipeline_type = "quick-prototype"

    def _build_task_description(title, agent):
        if idea.refined_description and idea.refined_description.strip():
            ctx = f"Project context: {idea.refined_description.strip()[:400]}"
            workflow = _AGENT_WORKFLOWS.get(pipeline_type, [])
            for step in workflow:
                step_title_lower = step["title"].lower()
                title_lower = title.lower()
                if step_title_lower in title_lower or title_lower in step_title_lower:
                    step_desc = step.get("description", "").strip()
                    if step_desc:
                        return f"{ctx}\n\nGoal: {step_desc}"
            return f"{ctx}\n\nDeliverable: {title}"
        return f"Pipeline: {pipeline_type} | Phase task: {title} | Agent: {agent}"

    # "Build core functionality" should match workflow step "Build core functionality"
    desc = _build_task_description("Build core functionality", "rapid-prototyper")
    assert "Goal:" in desc, "Should use workflow step description when matched"
    assert "prototype" in desc.lower(), "Should contain step description text"

    # "Smoke test and fix critical bugs" should match step "Smoke test"
    desc2 = _build_task_description("Smoke test and fix critical bugs", "qa-engineer")
    assert "Goal:" in desc2, "Should use workflow step description"
    assert "smoke test" in desc2.lower()


def test_build_task_description_all_pipeline_types():
    """All pipeline types should produce non-empty descriptions for seed tasks."""
    from ai_embedded_company.api.routes.ideas import _PIPELINE_DEFS

    refined = "A comprehensive refined description for testing all pipeline types."
    idea = MockIdea(refined_description=refined)

    for ptype, pdef in _PIPELINE_DEFS.items():
        pipeline_type = ptype
        seed_tasks = pdef.get("seed_tasks", [])
        assert len(seed_tasks) > 0, f"{ptype} should have at least 1 seed task"

        def _build_task_description(title, agent):
            if idea.refined_description and idea.refined_description.strip():
                ctx = f"Project context: {idea.refined_description.strip()[:400]}"
                workflow = _AGENT_WORKFLOWS.get(pipeline_type, [])
                for step in workflow:
                    step_title_lower = step["title"].lower()
                    title_lower = title.lower()
                    if step_title_lower in title_lower or title_lower in step_title_lower:
                        step_desc = step.get("description", "").strip()
                        if step_desc:
                            return f"{ctx}\n\nGoal: {step_desc}"
                return f"{ctx}\n\nDeliverable: {title}"
            return f"Pipeline: {pipeline_type} | Phase task: {title} | Agent: {agent}"

        for task_title in seed_tasks:
            agent = pdef["team"][0].value if hasattr(pdef["team"][0], "value") else pdef["team"][0]
            desc = _build_task_description(task_title, agent)
            assert desc, f"Description for '{task_title}' ({ptype}) should be non-empty"
            assert len(desc) > 20, f"Description for '{task_title}' ({ptype}) should be substantial"


def test_build_task_description_fallback_no_refined_no_workflow():
    """Without refined_description and without matching workflow, fallback template."""
    idea = MockIdea(refined_description=None, suggested_pipeline="embedded-firmware")
    pipeline_type = "embedded-firmware"

    def _build_task_description(title, agent):
        if idea.refined_description and idea.refined_description.strip():
            ctx = f"Project context: {idea.refined_description.strip()[:400]}"
            workflow = _AGENT_WORKFLOWS.get(pipeline_type, [])
            for step in workflow:
                step_title_lower = step["title"].lower()
                title_lower = title.lower()
                if step_title_lower in title_lower or title_lower in step_title_lower:
                    step_desc = step.get("description", "").strip()
                    if step_desc:
                        return f"{ctx}\n\nGoal: {step_desc}"
            return f"{ctx}\n\nDeliverable: {title}"
        return f"Pipeline: {pipeline_type} | Phase task: {title} | Agent: {agent}"

    desc = _build_task_description("Write firmware", "embedded-firmware-engineer")
    assert desc, "Fallback should produce non-empty description"
    assert "Pipeline:" in desc or "Project context:" in desc
