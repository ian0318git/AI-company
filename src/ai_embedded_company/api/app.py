"""FastAPI application entry point for AI Embedded Company."""

from __future__ import annotations

import asyncio
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_embedded_company.api.routes.dashboard import router as dashboard_router
from ai_embedded_company.api.routes.evolution import router as evolution_router
from ai_embedded_company.api.routes.ideas import router as ideas_router
from ai_embedded_company.api.routes.pipelines import router as pipelines_router
from ai_embedded_company.api.routes.prompts import router as prompts_router
from ai_embedded_company.api.routes.projects import router as projects_router
from ai_embedded_company.api.routes.system import router as system_router
from ai_embedded_company.api.routes.tasks import router as tasks_router
from ai_embedded_company.api.routes.teams import router as teams_router
from ai_embedded_company.storage import close_db, init_db


_background_tasks: set[asyncio.Task] = set()


def _auto_backup_db() -> None:
    """Auto-backup the database on server startup to prevent accidental data loss."""
    db_path = Path("data/ai_embedded_company.db")
    if not db_path.exists() or db_path.stat().st_size == 0:
        return

    backup_dir = Path("data/db_backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"ai_embedded_company_{timestamp}.db"

    shutil.copy2(db_path, backup_path)
    print(f"💾 Auto-backup: {backup_path.name} ({db_path.stat().st_size / 1024:.1f} KB)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle for the FastAPI app."""
    _auto_backup_db()
    await init_db()

    # Start background slow-task monitor
    from ai_embedded_company.api.routes.tasks import _check_slow_tasks_background
    task = asyncio.create_task(_check_slow_tasks_background())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    yield
    # Cancel background tasks on shutdown
    for t in _background_tasks:
        t.cancel()
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Embedded Company API",
        description="REST API for the AI Embedded Systems Company — project management, task tracking, hardware bridge, and knowledge base.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(system_router, tags=["System"])
    app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
    app.include_router(ideas_router, prefix="/api/ideas", tags=["Ideas"])
    app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
    app.include_router(teams_router, prefix="/api/teams", tags=["Teams"])
    app.include_router(pipelines_router, prefix="/api/pipelines", tags=["Pipelines"])
    app.include_router(evolution_router, prefix="/api/evolution", tags=["Evolution"])
    app.include_router(prompts_router, prefix="/api/prompts", tags=["Prompts"])
    app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])

    return app


app = create_app()
