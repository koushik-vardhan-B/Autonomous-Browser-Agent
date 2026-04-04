"""
FastAPI backend for the Autonomous Browser Agent.
"""

from .app import app
from .task_manager import task_manager
from .models import TaskRequest, TaskStatusResponse, HealthResponse

__all__ = ["app", "task_manager", "TaskRequest", "TaskStatusResponse", "HealthResponse"]
