"""System health check for Cycle #78."""
import asyncio
from ai_embedded_company.storage.database import get_session
from ai_embedded_company.storage import models as m


async def main():
    async with get_session() as db:
        print("=== SYSTEM HEALTH ===")
        ideas = (await db.execute(m.select(m.IdeaModel))).scalars().all()
        print(f"Ideas: {len(ideas)}")
        statuses = {}
        for idea in ideas:
            s = idea.status
            statuses[s] = statuses.get(s, 0) + 1
        for s, c in sorted(statuses.items()):
            print(f"  {s}: {c}")

        tasks = (await db.execute(m.select(m.TaskModel))).scalars().all()
        print(f"Tasks: {len(tasks)}")
        for s in ["done", "pending", "in_progress", "failed", "blocked"]:
            c = (await db.execute(
                m.select(m.func.count(m.TaskModel.id)).filter(m.TaskModel.status == s)
            )).scalar()
            if c:
                print(f"  {s}: {c}")

        pipelines = (await db.execute(m.select(m.PipelineModel))).scalars().all()
        print(f"Pipelines: {len(pipelines)}")
        done = (await db.execute(
            m.select(m.func.count(m.PipelineModel.id)).filter(m.PipelineModel.current_phase == "done")
        )).scalar()
        print(f"  done: {done}")

        kn = (await db.execute(
            m.select(m.func.count(m.KnowledgeModel.id))
        )).scalar()
        print(f"Knowledge entries: {kn}")

        fr = (await db.execute(
            m.select(m.func.count(m.FailureRecord.id))
        )).scalar()
        print(f"Failure records: {fr}")

        ac = (await db.execute(
            m.select(m.func.count(m.AntibodyCandidate.id))
        )).scalar()
        print(f"Antibody candidates: {ac}")

        for name, model_cls_name in [
            ("A/B experiments", "ABExperimentModel"),
            ("Optimization insights", "OptimizationInsightModel"),
            ("Prompt templates", "PromptTemplateModel"),
            ("Prompt results", "PromptResultModel"),
        ]:
            cls = getattr(m, model_cls_name, None)
            if cls:
                try:
                    cnt = (await db.execute(m.select(m.func.count(cls.id)))).scalar()
                    print(f"{name}: {cnt}")
                except Exception as e:
                    print(f"{name}: error - {e}")
            else:
                print(f"{name}: model class not found")


asyncio.run(main())
