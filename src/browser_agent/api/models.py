"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ─── Enums ────────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    """Status of an agent task."""
    QUEUED = "queued"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LLMProvider(str, Enum):
    """Available LLM providers."""
    AUTO = "auto"
    GEMINI = "gemini"
    GROQ = "groq"
    SAMBANOVA = "sambanova"
    OLLAMA = "ollama"


# ─── Request Models ──────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    """Request to submit a new agent task."""
    instruction: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Natural language instruction for the browser agent",
        examples=[
            "Open google.com and search for Python tutorials",
            "Go to amazon.com and find the price of iPhone 15",
        ]
    )
    headless: bool = Field(
        default=True,
        description="Run browser in headless mode (no visible window)"
    )
    provider: Optional[LLMProvider] = Field(
        default=None,
        description="Force a specific LLM provider (default: auto-rotate)"
    )
    max_steps: int = Field(
        default=30,
        ge=5,
        le=100,
        description="Maximum execution steps before timeout"
    )


class CancelRequest(BaseModel):
    """Request to cancel a running task."""
    reason: Optional[str] = Field(
        default=None,
        description="Optional reason for cancellation"
    )


# ─── Response Models ─────────────────────────────────────────────────────────

class TaskSubmitResponse(BaseModel):
    """Response after submitting a task."""
    task_id: str
    status: TaskStatus
    message: str
    created_at: str


class StepInfo(BaseModel):
    """Info about a single execution step."""
    step_number: int
    agent: str
    query: str
    status: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Response with task status details."""
    task_id: str
    status: TaskStatus
    instruction: str
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    plan: List[StepInfo] = []
    output: Optional[str] = None
    error: Optional[str] = None
    extracted_data: List[str] = []
    provider_used: Optional[str] = None


class TaskListResponse(BaseModel):
    """Response with list of tasks."""
    tasks: List[TaskStatusResponse]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: float
    llm_keys: Dict[str, int]
    browser_active: bool


class LogEntry(BaseModel):
    """A single log entry."""
    timestamp: str
    level: str
    source: str
    message: str


class LogStreamResponse(BaseModel):
    """Response with recent log entries."""
    task_id: Optional[str] = None
    entries: List[LogEntry]
    total_lines: int
