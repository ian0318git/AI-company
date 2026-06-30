"""State definitions for the orchestrator state graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ai_embedded_company.types import PipelinePhase, PipelineType, TaskStatus


@dataclass
class OrchestratorState:
    """State carried through the orchestrator graph.

    This is the shared state object passed between nodes in the
    LangGraph StateGraph that drives the Idea → Pipeline → Done flow.
    """

    # Input
    idea_description: str = ""
    pipeline_type: Optional[PipelineType] = None
    project_id: str = ""
    board_family: str = "unknown"

    # Work products (populated by graph nodes)
    requirements: str = ""
    architecture_doc: str = ""
    implementation_tasks: list[dict] = field(default_factory=list)
    test_plan: str = ""

    # Progress tracking
    current_phase: PipelinePhase = PipelinePhase.IDEA
    completed_phases: list[PipelinePhase] = field(default_factory=list)

    # Agent assignments
    agent_assignments: dict[str, str] = field(default_factory=dict)  # task_id → agent_role

    # Results
    build_success: bool = False
    flash_success: bool = False
    final_summary: str = ""

    # Error tracking
    errors: list[str] = field(default_factory=list)
