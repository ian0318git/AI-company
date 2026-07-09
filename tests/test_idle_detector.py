"""Tests for the idle detection system."""

from __future__ import annotations

import pytest

from ai_embedded_company.tools.idle_detector import (
    AutoSeedGenerator,
    IdleDepth,
    IdleDetector,
    IdleState,
    RevivalScorer,
)


@pytest.mark.asyncio
async def test_idle_detector_active() -> None:
    detector = IdleDetector()
    state = await detector.check(pending_tasks=2, active_pipelines=1, new_ideas=0)
    assert state.idle is False
    assert state.depth == IdleDepth.ACTIVE
    assert state.consecutive_idle_cycles == 0


@pytest.mark.asyncio
async def test_idle_detector_shallow() -> None:
    detector = IdleDetector()
    state = await detector.check(pending_tasks=0, active_pipelines=0, new_ideas=0)
    assert state.idle is True
    assert state.depth == IdleDepth.SHALLOW
    assert state.consecutive_idle_cycles == 1


@pytest.mark.asyncio
async def test_idle_detector_deep() -> None:
    detector = IdleDetector()
    for _ in range(3):
        state = await detector.check(pending_tasks=0, active_pipelines=0, new_ideas=0)
    assert state.idle is True
    assert state.depth == IdleDepth.DEEP
    assert state.consecutive_idle_cycles >= 3


@pytest.mark.asyncio
async def test_idle_detector_resets_on_activity() -> None:
    detector = IdleDetector()
    for _ in range(2):
        await detector.check(pending_tasks=0, active_pipelines=0, new_ideas=0)
    state = await detector.check(pending_tasks=1, active_pipelines=0, new_ideas=0)
    assert state.depth == IdleDepth.ACTIVE
    assert state.consecutive_idle_cycles == 0


def test_revival_scorer_empty() -> None:
    scorer = RevivalScorer()
    candidates = scorer.score([])
    assert candidates == []


def test_revival_scorer_tags_match() -> None:
    scorer = RevivalScorer()
    ideas = [
        {"id": "1", "title": "Auto Seed", "tags": ["autonomous-cycle"], "updated_at": "", "pipeline_ids": []},
        {"id": "2", "title": "Unrelated", "tags": ["test"], "updated_at": "", "pipeline_ids": []},
    ]
    candidates = scorer.score(ideas)
    assert len(candidates) >= 1
    assert candidates[0].idea_id == "1"
    assert candidates[0].score > 10


def test_revival_scorer_top_3_limit() -> None:
    scorer = RevivalScorer()
    ideas = [
        {"id": str(i), "title": f"Idea {i}", "tags": ["autonomous-cycle"], "updated_at": "2026-07-09T12:00:00", "pipeline_ids": []}
        for i in range(10)
    ]
    candidates = scorer.score(ideas)
    assert len(candidates) <= 3


def test_auto_seed_generates_on_deep_idle() -> None:
    generator = AutoSeedGenerator()
    state = IdleState(
        idle=True,
        depth=IdleDepth.DEEP,
        consecutive_idle_cycles=3,
        pending_tasks=0,
        active_pipelines=0,
        new_ideas=0,
        total_archived_ideas=5,
    )
    seeds = generator.generate(state, set())
    assert len(seeds) >= 1
    assert "title" in seeds[0]
    assert seeds[0]["tags"] == "autonomous-cycle,auto-seed,maintenance"


def test_auto_seed_skips_shallow_idle() -> None:
    generator = AutoSeedGenerator()
    state = IdleState(
        idle=True,
        depth=IdleDepth.SHALLOW,
        consecutive_idle_cycles=1,
        pending_tasks=0,
        active_pipelines=0,
        new_ideas=0,
        total_archived_ideas=5,
    )
    seeds = generator.generate(state, set())
    assert len(seeds) == 0


def test_auto_seed_tracks_used_templates() -> None:
    generator = AutoSeedGenerator()
    state = IdleState(
        idle=True,
        depth=IdleDepth.DEEP,
        consecutive_idle_cycles=3,
        pending_tasks=0,
        active_pipelines=0,
        new_ideas=0,
        total_archived_ideas=5,
    )
    used: set[str] = set()
    seed1 = generator.generate(state, used)
    seed2 = generator.generate(state, used)
    assert len(seed1) == 1
    assert len(seed2) == 1
    assert seed1[0]["title"] != seed2[0]["title"]
