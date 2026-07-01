"""FastAPI application entry point for AI Embedded Company."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_embedded_company.api.routes.ideas import router as ideas_router
from ai_embedded_company.api.routes.pipelines import router as pipelines_router
from ai_embedded_company.api.routes.projects import router as projects_router
from ai_embedded_company.api.routes.system import router as system_router
from ai_embedded_company.api.routes.tasks import router as tasks_router
from ai_embedded_company.api.routes.teams import router as teams_router
from ai_embedded_company.storage import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle for the FastAPI app."""
    await init_db()
    yield
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

    return app


app = create_app()
