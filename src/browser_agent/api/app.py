"""
FastAPI application for the Autonomous Browser Agent.

Endpoints:
  POST   /api/agent/run              — Submit a task
  GET    /api/agent/status/{task_id} — Get task status
  GET    /api/agent/tasks            — List all tasks
  POST   /api/agent/cancel/{task_id} — Cancel a task
  DELETE /api/agent/task/{task_id}   — Delete a task record
  GET    /api/health                 — Health check
  GET    /api/logs/agent             — Get agent logs
  GET    /api/logs/errors            — Get error logs
  GET    /api/logs/task/{task_id}    — Get task-specific logs
  GET    /api/logs/stream            — SSE log stream
  WS     /api/ws/task/{task_id}      — WebSocket for real-time updates
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load env vars
from dotenv import load_dotenv
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # ── Startup ──
    print("🚀 Starting Autonomous Browser Agent API...")

    # Initialize logging
    from browser_agent.observability.logger import setup_logging
    setup_logging()

    # Pre-initialize the LLM router (validates API keys)
    from browser_agent.llm import LLMConfig
    print(f"✅ LLM Router initialized")

    print("✅ API ready at http://localhost:8000")
    print("📖 Docs at http://localhost:8000/docs")

    yield

    # ── Shutdown ──
    print("🛑 Shutting down...")
    try:
        from browser_agent.browser.manager import browser_manager
        browser_manager.close()
        print("✅ Browser closed")
    except Exception:
        pass


# ─── Create App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Autonomous Browser Agent API",
    description=(
        "AI-powered browser automation agent with multi-LLM orchestration. "
        "Submit natural language tasks and the agent will plan, execute, "
        "and extract data from websites autonomously."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── CORS (allow frontend from any origin during development) ────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routes ─────────────────────────────────────────────────────────

from browser_agent.api.routes.agent import router as agent_router
from browser_agent.api.routes.health import router as health_router
from browser_agent.api.routes.logs import router as logs_router
from browser_agent.api.websocket import router as ws_router

app.include_router(agent_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(ws_router, prefix="/api")


# ─── Root Redirect ───────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint — redirect to docs."""
    return {
        "name": "Autonomous Browser Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "submit_task": "POST /api/agent/run"
    }
