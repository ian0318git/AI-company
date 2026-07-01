"""MCP tools for self-evolution: failure alchemy, research loop, knowledge injection."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ai_embedded_company.storage.database import _get_sessionmaker
from ai_embedded_company.storage.models import FailureRecord, ResearchFinding, KnowledgeModel


def register_tools(mcp):
    """Register self-evolution tools with the FastMCP instance."""

    # ── Failure Alchemy ────────────────────────────────────────────────────

    @mcp.tool()
    async def failure_report(
        title: str,
        description: str,
        root_cause: str = "",
        category: str = "unknown",
        severity: str = "medium",
        task_id: str = "",
        project_id: str = "",
        agent_role: str = "",
        tags: str = "",
    ) -> dict:
        """Report a task failure for root-cause analysis. The system will extract
        antibodies (prevention), vaccines (warnings), and catalysts (prompt improvements).

        Categories: logic_error, resource_leak, race_condition, config_miss,
                   dependency, timeout, api_error, security, other

        Args:
            title: Short description of the failure
            description: Detailed account of what happened
            root_cause: Identified root cause (can be filled later by analyze step)
            category: Failure category
            severity: low, medium, high, or critical
            task_id: Associated task UUID (optional)
            project_id: Associated project UUID (optional)
            agent_role: Agent that encountered the failure
            tags: Comma-separated tags
        """
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        # Check if similar failure already exists (frequency counter)
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select

            # Find existing pattern
            existing_result = await session.execute(
                select(FailureRecord).where(
                    FailureRecord.category == category,
                    FailureRecord.title.ilike(f"%{title[:30]}%"),
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.frequency += 1
                existing.description = f"{existing.description}\n\n--- Updated {datetime.now(timezone.utc).isoformat()} ---\n{description}"
                existing.updated_at = datetime.now(timezone.utc)
                await session.commit()
                return {
                    "status": "merged",
                    "failure_id": existing.id,
                    "frequency": existing.frequency,
                    "message": f"Merged with existing failure record (now frequency={existing.frequency}). Root cause analysis will be updated.",
                }

            # New failure record
            record = FailureRecord(
                task_id=task_id or None,
                project_id=project_id or None,
                agent_role=agent_role or None,
                title=title,
                description=description,
                root_cause=root_cause,
                category=category,
                severity=severity,
                frequency=1,
                tags=json.dumps(tag_list),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)

            return {
                "status": "reported",
                "failure_id": record.id,
                "category": category,
                "severity": severity,
                "message": f"Failure recorded. Use failure_analyze to extract antibodies, vaccines, and catalysts.",
            }

    @mcp.tool()
    async def failure_analyze(failure_id: str) -> dict:
        """Analyze a failure record and produce the three alchemy outputs:
        - antibody: prevention strategy stored in team memory
        - vaccine: pre-task warning for similar future tasks
        - catalyst: prompt improvement to inject into agent system prompts
        """
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(FailureRecord).where(FailureRecord.id == failure_id)
            )
            record = result.scalar_one_or_none()
            if record is None:
                return {"error": f"Failure record not found: {failure_id}"}

            # Generate antibody (prevention strategy)
            antibody = _generate_antibody(record.category, record.root_cause, record.description)

            # Generate vaccine (pre-task warning)
            vaccine = _generate_vaccine(record.category, record.title, record.root_cause)

            # Generate catalyst (prompt improvement)
            catalyst = _generate_catalyst(record.agent_role, record.category, record.root_cause)

            record.antibody = antibody
            record.vaccine = vaccine
            record.catalyst = catalyst
            record.status = "analyzed"
            await session.commit()

            return {
                "failure_id": record.id,
                "category": record.category,
                "antibody": antibody,
                "vaccine": vaccine,
                "catalyst": catalyst,
                "message": "Analysis complete. Antibody stored, vaccine registered, catalyst ready for injection.",
            }

    @mcp.tool()
    async def failure_list(
        category: str = "",
        severity: str = "",
        status: str = "",
        limit: int = 20,
    ) -> dict:
        """List failure records with optional filters."""
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select

            stmt = select(FailureRecord)
            if category:
                stmt = stmt.where(FailureRecord.category == category)
            if severity:
                stmt = stmt.where(FailureRecord.severity == severity)
            if status:
                stmt = stmt.where(FailureRecord.status == status)
            stmt = stmt.order_by(FailureRecord.frequency.desc()).limit(limit)

            result = await session.execute(stmt)
            records = result.scalars().all()

            return {
                "failures": [
                    {
                        "id": r.id,
                        "title": r.title,
                        "category": r.category,
                        "severity": r.severity,
                        "frequency": r.frequency,
                        "status": r.status,
                        "antibody": r.antibody[:200] if r.antibody else None,
                        "vaccine": r.vaccine[:200] if r.vaccine else None,
                        "catalyst": r.catalyst[:200] if r.catalyst else None,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in records
                ]
            }

    @mcp.tool()
    async def knowledge_inject(agent_role: str = "", category: str = "") -> dict:
        """Inject accumulated antibodies, vaccines, and catalysts into an agent's system prompt.

        Call this before starting a task to give the agent awareness of past failures and prevention strategies.

        Args:
            agent_role: Target agent role (e.g., 'embedded-firmware-engineer'). If empty, returns all.
            category: Filter by failure category
        """
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select

            stmt = select(FailureRecord).where(FailureRecord.status == "analyzed")
            if category:
                stmt = stmt.where(FailureRecord.category == category)
            stmt = stmt.order_by(FailureRecord.frequency.desc()).limit(10)

            result = await session.execute(stmt)
            records = result.scalars().all()

            vaccines = [r.vaccine for r in records if r.vaccine and r.frequency >= 2]
            catalysts = [r.catalyst for r in records if r.catalyst]
            antibodies = [r.antibody for r in records if r.antibody]

            # Build the injection context
            sections = []
            if vaccines:
                sections.append("## ⚠️ Pre-Task Warnings (Vaccines)\n" + "\n".join(f"- {v}" for v in vaccines[:5]))
            if catalysts:
                sections.append("## 💡 Execution Improvements (Catalysts)\n" + "\n".join(f"- {c}" for c in catalysts[:5]))
            if antibodies:
                sections.append("## 🛡️ Prevention Strategies (Antibodies)\n" + "\n".join(f"- {a}" for a in antibodies[:5]))

            injection = "\n\n".join(sections) if sections else "No accumulated learnings yet."

            return {
                "agent_role": agent_role or "all",
                "vaccines_count": len(vaccines),
                "catalysts_count": len(catalysts),
                "antibodies_count": len(antibodies),
                "injection": injection,
                "usage": "Paste this injection block into the agent's system prompt or context before task execution.",
            }

    # ── Research Loop ──────────────────────────────────────────────────────

    @mcp.tool()
    async def research_submit(
        title: str,
        summary: str,
        source: str = "",
        source_type: str = "web",
        relevance_score: int = 5,
        tags: str = "",
    ) -> dict:
        """Submit a research finding from the research agent loop.

        These findings feed into brainstorming sessions where agents debate
        their relevance and turn accepted findings into implementation tasks.

        Args:
            title: Finding title (e.g., "Rust gaining adoption in embedded Linux")
            summary: Detailed summary of the finding
            source: URL, paper DOI, or tool name
            source_type: competitor, framework, paper, tool, pattern, trend
            relevance_score: 1-10 how relevant this is to our work
            tags: Comma-separated tags
        """
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            finding = ResearchFinding(
                title=title,
                source=source,
                source_type=source_type,
                summary=summary,
                relevance_score=relevance_score,
                tags=json.dumps(tag_list),
                status="new",
            )
            session.add(finding)
            await session.commit()
            await session.refresh(finding)

            return {
                "finding_id": finding.id,
                "title": title,
                "source_type": source_type,
                "status": "new",
                "message": "Finding submitted. Next: agents debate during brainstorming, accepted findings become ideas in the Inbox.",
            }

    @mcp.tool()
    async def research_debate(finding_id: str, verdict: str, debate_notes: str = "", action_items: str = "") -> dict:
        """Record the outcome of a research debate. Accepted findings create ideas.

        Args:
            finding_id: The research finding UUID
            verdict: 'accepted', 'rejected', or 'needs_more_research'
            debate_notes: Summary of agent debate/discussion
            action_items: JSON list of action items derived from this finding
        """
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(ResearchFinding).where(ResearchFinding.id == finding_id)
            )
            finding = result.scalar_one_or_none()
            if finding is None:
                return {"error": f"Research finding not found: {finding_id}"}

            finding.status = verdict
            finding.debate_notes = debate_notes
            finding.action_items = action_items
            await session.commit()

            # If accepted, auto-create an idea
            idea_id = None
            if verdict == "accepted":
                from ai_embedded_company.storage.models import IdeaModel, ProjectModel

                project = ProjectModel(
                    name=finding.title,
                    description=finding.summary,
                )
                session.add(project)
                await session.flush()

                idea = IdeaModel(
                    project_id=project.id,
                    title=finding.title,
                    raw_description=finding.summary,
                    tags=finding.tags,
                    status="new",
                )
                session.add(idea)
                await session.commit()
                await session.refresh(idea)

                finding.idea_id = idea.id
                await session.commit()
                idea_id = idea.id

            return {
                "finding_id": finding.id,
                "verdict": verdict,
                "idea_id": idea_id,
                "message": f"Finding {verdict}.{' Idea created in Inbox.' if idea_id else ''} Agents can now refine and start a pipeline.",
            }

    @mcp.tool()
    async def research_list(status: str = "", source_type: str = "", limit: int = 20) -> dict:
        """List research findings."""
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select

            stmt = select(ResearchFinding)
            if status:
                stmt = stmt.where(ResearchFinding.status == status)
            if source_type:
                stmt = stmt.where(ResearchFinding.source_type == source_type)
            stmt = stmt.order_by(ResearchFinding.relevance_score.desc()).limit(limit)

            result = await session.execute(stmt)
            findings = result.scalars().all()

            return {
                "findings": [
                    {
                        "id": f.id,
                        "title": f.title,
                        "source": f.source,
                        "source_type": f.source_type,
                        "summary": f.summary[:300],
                        "relevance_score": f.relevance_score,
                        "status": f.status,
                        "debate_notes": f.debate_notes[:200] if f.debate_notes else None,
                        "idea_id": f.idea_id,
                        "created_at": f.created_at.isoformat() if f.created_at else None,
                    }
                    for f in findings
                ]
            }

    @mcp.tool()
    async def evolution_status() -> dict:
        """Get the current self-evolution state: failure stats, research pipeline, knowledge health."""
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select, func

            # Failure stats
            total_failures_result = await session.execute(select(func.count(FailureRecord.id)))
            total_failures = total_failures_result.scalar() or 0

            analyzed_result = await session.execute(
                select(func.count(FailureRecord.id)).where(FailureRecord.status == "analyzed")
            )
            analyzed = analyzed_result.scalar() or 0

            high_freq_result = await session.execute(
                select(func.count(FailureRecord.id)).where(FailureRecord.frequency >= 3)
            )
            high_freq = high_freq_result.scalar() or 0

            # Category breakdown
            cat_result = await session.execute(
                select(FailureRecord.category, func.count(FailureRecord.id))
                .group_by(FailureRecord.category)
            )
            categories = {row[0]: row[1] for row in cat_result.fetchall()}

            # Research stats
            total_research_result = await session.execute(select(func.count(ResearchFinding.id)))
            total_research = total_research_result.scalar() or 0

            accepted_result = await session.execute(
                select(func.count(ResearchFinding.id)).where(ResearchFinding.status == "accepted")
            )
            accepted = accepted_result.scalar() or 0

            return {
                "failures": {
                    "total": total_failures,
                    "analyzed": analyzed,
                    "high_frequency_patterns": high_freq,
                    "by_category": categories,
                    "antibodies_active": analyzed,
                    "vaccines_active": high_freq,
                },
                "research": {
                    "total_findings": total_research,
                    "accepted": accepted,
                    "conversion_rate": f"{int(accepted / total_research * 100)}%" if total_research > 0 else "0%",
                },
                "evolution_health": "healthy" if analyzed > 0 else "nascent",
                "message": (
                    "Self-evolution is active: failures become antibodies, research feeds the idea pipeline."
                    if analyzed > 0 else
                    "System is young. Report failures to build immunity. Submit research to feed the pipeline."
                ),
            }


# ── Alchemy Generators ──────────────────────────────────────────────────────


def _generate_antibody(category: str, root_cause: str, description: str) -> str:
    """Generate a prevention strategy (antibody) from a failure."""
    templates = {
        "logic_error": "Add edge-case validation and unit test for the identified logic path. Review state machine transitions.",
        "resource_leak": "Audit all resource acquisition points. Ensure RAII pattern or defer/cleanup in all exit paths. Add leak detection tests.",
        "race_condition": "Review all shared state access. Add mutex/semaphore guards. Consider lock-free data structures for ISR contexts.",
        "config_miss": "Create configuration checklist template. Add pre-flight config validation step. Document all required env vars and defaults.",
        "dependency": "Pin dependency versions. Add compatibility matrix check to CI. Maintain vendor fork of critical dependencies.",
        "timeout": "Add configurable timeout with sensible defaults. Implement retry with exponential backoff. Add circuit breaker pattern.",
        "api_error": "Add response validation. Handle all HTTP error codes explicitly. Add retry for 429/503. Log full request context on failure.",
        "security": "Run security audit on affected component. Add input sanitization. Review authentication/authorization flow. Update threat model.",
    }
    base = templates.get(category, "Document the failure pattern. Add a regression test. Share learning in team knowledge base.")
    if root_cause:
        base += f" Root cause: {root_cause}."
    return base


def _generate_vaccine(category: str, title: str, root_cause: str) -> str:
    """Generate a pre-task warning (vaccine) from a failure."""
    return (
        f"[VACCINE] Before starting similar work, verify: {title}. "
        f"Historical failures in category '{category}' occurred {1 if not root_cause else 'due to'}: "
        f"{root_cause or 'pattern not yet fully analyzed'}. "
        f"Check the antibody for prevention steps."
    )


def _generate_catalyst(agent_role: str, category: str, root_cause: str) -> str:
    """Generate a prompt improvement (catalyst) to inject into agent system prompts."""
    role_hint = f" as a {agent_role}" if agent_role else ""
    return (
        f"[CATALYST] When working{role_hint}, be aware that failures in category '{category}' "
        f"have been observed. Root cause pattern: {root_cause or 'under analysis'}. "
        f"Proactively apply prevention strategies. Before completing any task in this category, "
        f"self-audit against known failure patterns in the knowledge base."
    )
