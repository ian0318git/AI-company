"""One-shot fix: mark projects as done when all their pipelines are done."""
import asyncio
from sqlalchemy import select
from ai_embedded_company.storage.database import _get_sessionmaker
from ai_embedded_company.storage.models import ProjectModel, PipelineModel


async def fix_stuck_projects():
    sessionmaker = _get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(
            select(ProjectModel).where(ProjectModel.status == "active")
        )
        active_projects = result.scalars().all()

        fixed = 0
        for proj in active_projects:
            pipe_result = await session.execute(
                select(PipelineModel).where(PipelineModel.project_id == proj.id)
            )
            pipelines = pipe_result.scalars().all()

            if not pipelines:
                print(f"SKIP {proj.id} ({proj.name}): no pipeline found")
                continue

            all_done = all(p.current_phase == "done" for p in pipelines)
            if all_done:
                proj.status = "done"
                fixed += 1
                print(f"FIXED {proj.id} ({proj.name}) -> done")
            else:
                phases = [p.current_phase for p in pipelines]
                print(f"SKIP {proj.id} ({proj.name}): pipeline phases={phases}")

        await session.commit()
        print(f"\nFixed {fixed} projects")


if __name__ == "__main__":
    asyncio.run(fix_stuck_projects())
