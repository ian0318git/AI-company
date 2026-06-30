"""MCP tools for meeting collaboration."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ai_embedded_company.mcp._base import _api_call
from ai_embedded_company.storage.database import _get_sessionmaker
from ai_embedded_company.storage.models import EventLogModel


def register_tools(mcp):
    """Register meeting tools with the FastMCP instance."""

    @mcp.tool()
    async def meeting_create(
        title: str,
        project_id: str,
        agenda: str = "",
        participants: str = "",
    ) -> dict:
        """Create a structured meeting for agent collaboration.

        Args:
            title: Meeting title (e.g., "Architecture Review: M5Stack Sensor Hub")
            project_id: The project UUID
            agenda: Meeting agenda items, one per line
            participants: Comma-separated agent roles to invite
        """
        meeting_id = f"meeting-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        # Log the meeting creation
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            log = EventLogModel(
                event_type="meeting_created",
                source="mcp",
                payload=json.dumps({
                    "meeting_id": meeting_id,
                    "title": title,
                    "project_id": project_id,
                    "agenda": agenda,
                    "participants": [p.strip() for p in participants.split(",") if p.strip()],
                }),
            )
            session.add(log)
            await session.commit()

        return {
            "meeting_id": meeting_id,
            "title": title,
            "project_id": project_id,
            "agenda": agenda.split("\n") if agenda else [],
            "participants": [p.strip() for p in participants.split(",") if p.strip()],
            "status": "created",
            "message": f"Meeting '{title}' created. Participants can now send messages to meeting_id: {meeting_id}",
        }

    @mcp.tool()
    async def meeting_send_message(
        meeting_id: str,
        agent_role: str,
        message: str,
    ) -> dict:
        """Send a message in a meeting.

        Args:
            meeting_id: The meeting UUID from meeting_create
            agent_role: The agent role sending the message
            message: The message content
        """
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            log = EventLogModel(
                event_type="meeting_message",
                source=agent_role,
                payload=json.dumps({
                    "meeting_id": meeting_id,
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }),
            )
            session.add(log)
            await session.commit()

        return {
            "meeting_id": meeting_id,
            "agent": agent_role,
            "message": message,
            "status": "sent",
        }

    @mcp.tool()
    async def meeting_conclude(
        meeting_id: str,
        summary: str = "",
        decisions: str = "",
        action_items: str = "",
    ) -> dict:
        """Conclude a meeting with summary, decisions, and action items.

        Args:
            meeting_id: The meeting UUID
            summary: Brief summary of discussion
            decisions: Decisions made, one per line
            action_items: Action items with owners, one per line (e.g., "firmware-engineer: Implement I2C driver")
        """
        decision_list = [d.strip() for d in decisions.split("\n") if d.strip()]
        action_list = [a.strip() for a in action_items.split("\n") if a.strip()]

        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            log = EventLogModel(
                event_type="meeting_concluded",
                source="mcp",
                payload=json.dumps({
                    "meeting_id": meeting_id,
                    "summary": summary,
                    "decisions": decision_list,
                    "action_items": action_list,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }),
            )
            session.add(log)
            await session.commit()

        return {
            "meeting_id": meeting_id,
            "status": "concluded",
            "summary": summary,
            "decisions": decision_list,
            "action_items": action_list,
        }

    @mcp.tool()
    async def meeting_templates() -> dict:
        """List available meeting templates with their recommended agent participants."""
        return {
            "templates": [
                {
                    "name": "architecture-review",
                    "description": "Review system architecture before implementation",
                    "participants": ["software-architect", "tech-lead", "firmware-engineer"],
                    "agenda": [
                        "Review system context and constraints",
                        "Walk through component design",
                        "Identify risks and unknowns",
                        "Agree on implementation approach",
                        "Define interface contracts",
                    ],
                },
                {
                    "name": "sprint-planning",
                    "description": "Plan the next sprint/iteration",
                    "participants": ["project-manager", "tech-lead", "all-assigned"],
                    "agenda": [
                        "Review completed tasks",
                        "Prioritize backlog",
                        "Estimate effort for top items",
                        "Assign tasks to agents",
                        "Set sprint goal",
                    ],
                },
                {
                    "name": "bug-triage",
                    "description": "Prioritize and assign bugs",
                    "participants": ["qa-engineer", "code-reviewer", "tech-lead"],
                    "agenda": [
                        "Review new bugs since last triage",
                        "Assign severity (Critical/High/Medium/Low)",
                        "Assign to responsible agent",
                        "Set target fix version",
                    ],
                },
                {
                    "name": "design-review",
                    "description": "Review UI/UX or hardware design",
                    "participants": ["frontend-developer", "hardware-engineer", "tech-lead"],
                    "agenda": [
                        "Present design",
                        "Gather feedback from all participants",
                        "Identify constraints and trade-offs",
                        "Approve or request changes",
                    ],
                },
                {
                    "name": "post-mortem",
                    "description": "Analyze what went wrong and how to prevent it",
                    "participants": ["tech-lead", "qa-engineer", "all-involved"],
                    "agenda": [
                        "Timeline of the incident",
                        "Root cause analysis (5 Whys)",
                        "What went well in the response",
                        "What could be improved",
                        "Action items to prevent recurrence",
                    ],
                },
            ]
        }
