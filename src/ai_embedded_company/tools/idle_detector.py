"""Self-Healing Idle Detection System.

Detects fully idle autonomous cycle states and auto-seeds new ideas
from archived candidates or known improvement opportunities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IdleDepth(Enum):
    """How deeply idle the system is."""

    ACTIVE = "active"
    SHALLOW = "shallow"  # 1-2 consecutive idle cycles
    DEEP = "deep"  # 3+ consecutive idle cycles


@dataclass
class IdleState:
    """Snapshot of system idle state at cycle start."""

    idle: bool
    depth: IdleDepth
    consecutive_idle_cycles: int
    pending_tasks: int
    active_pipelines: int
    new_ideas: int
    total_archived_ideas: int
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RevivalCandidate:
    """An archived idea that could be revived."""

    idea_id: str
    title: str
    score: float
    reason: str


class IdleDetector:
    """Detect and classify system idle states."""

    def __init__(self, state_store: dict[str, Any] | None = None) -> None:
        self._state_store = state_store or {}
        self._consecutive_idle = 0

    async def check(
        self,
        pending_tasks: int,
        active_pipelines: int,
        new_ideas: int,
    ) -> IdleState:
        """Run idle detection and return classified state."""
        is_idle = pending_tasks == 0 and active_pipelines == 0 and new_ideas == 0

        if is_idle:
            self._consecutive_idle += 1
        else:
            self._consecutive_idle = 0

        depth: IdleDepth
        if not is_idle:
            depth = IdleDepth.ACTIVE
        elif self._consecutive_idle >= 3:
            depth = IdleDepth.DEEP
        else:
            depth = IdleDepth.SHALLOW

        self._state_store["consecutive_idle"] = self._consecutive_idle
        self._state_store["last_check"] = datetime.now(timezone.utc).isoformat()

        return IdleState(
            idle=is_idle,
            depth=depth,
            consecutive_idle_cycles=self._consecutive_idle,
            pending_tasks=pending_tasks,
            active_pipelines=active_pipelines,
            new_ideas=new_ideas,
            total_archived_ideas=0,
        )


class RevivalScorer:
    """Score archived ideas for revival priority."""

    def __init__(self) -> None:
        self._system_gap_tags: set[str] = {
            "autonomous-cycle",
            "automation",
            "self-improvement",
            "evolution",
        }

    def score(self, archived_ideas: list[dict[str, Any]]) -> list[RevivalCandidate]:
        """Score archived ideas and return top candidates sorted by priority."""
        candidates: list[RevivalCandidate] = []

        for idea in archived_ideas:
            tags = set(idea.get("tags", []) or [])
            tag_match = len(tags & self._system_gap_tags)
            recency_bonus = self._compute_recency_bonus(idea.get("updated_at", ""))
            attempts_penalty = len(idea.get("pipeline_ids", []))

            score = (tag_match * 30) + recency_bonus - (attempts_penalty * 5)
            score = max(0.0, min(100.0, score))

            if score > 10:
                reasons = []
                if tag_match:
                    reasons.append(f"matches {tag_match} system gap tag(s)")
                if recency_bonus > 10:
                    reasons.append("recently updated")
                if attempts_penalty == 0:
                    reasons.append("never attempted")

                candidates.append(
                    RevivalCandidate(
                        idea_id=idea["id"],
                        title=idea.get("title", "Untitled"),
                        score=round(score, 1),
                        reason="; ".join(reasons),
                    )
                )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:3]

    @staticmethod
    def _compute_recency_bonus(updated_at: str) -> float:
        """Give higher score to recently-updated ideas."""
        if not updated_at:
            return 0.0
        try:
            updated = datetime.fromisoformat(updated_at)
            days_ago = (datetime.now(timezone.utc) - updated).days
            return max(0.0, 20.0 - days_ago)
        except (ValueError, TypeError):
            return 0.0


class AutoSeedGenerator:
    """Generate seed maintenance ideas when deep idle detected."""

    SEED_TEMPLATES: list[dict[str, str]] = [
        {
            "title": "Database Health Checkup",
            "description": "Run database integrity checks, VACUUM, and index optimization on the project database. Verify backup system is working.",
            "pipeline": "quick-prototype",
        },
        {
            "title": "Dependency Version Audit",
            "description": "Audit all Python and Node.js dependencies for updates, security advisories, and breaking changes. Generate upgrade plan.",
            "pipeline": "research-spike",
        },
        {
            "title": "Test Coverage Sweep",
            "description": "Run coverage analysis across the codebase, identify untested modules, and generate test gap report with prioritized fill plan.",
            "pipeline": "quick-prototype",
        },
        {
            "title": "API Documentation Sync",
            "description": "Audit API endpoints against OpenAPI spec, document undocumented endpoints, flag discrepancies between spec and implementation.",
            "pipeline": "research-spike",
        },
        {
            "title": "Cycle Report Archive Cleanup",
            "description": "Review accumulated cycle reports for stale/obsolete entries, consolidate key findings, archive old reports to compressed storage.",
            "pipeline": "quick-prototype",
        },
    ]

    def generate(self, idle_state: IdleState, used_templates: set[str]) -> list[dict[str, str]]:
        """Generate seed ideas for deep idle states."""
        if idle_state.depth != IdleDepth.DEEP:
            return []

        seeds: list[dict[str, str]] = []
        for template in self.SEED_TEMPLATES:
            if template["title"] not in used_templates:
                seeds.append({
                    "title": template["title"],
                    "raw_description": template["description"],
                    "suggested_pipeline": template["pipeline"],
                    "tags": "autonomous-cycle,auto-seed,maintenance",
                })
                used_templates.add(template["title"])
                if len(seeds) >= 1:
                    break

        return seeds
