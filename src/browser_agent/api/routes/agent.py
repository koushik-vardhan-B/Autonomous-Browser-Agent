"""
Agent task routes — submit, status, cancel, delete.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models import (
    TaskRequest, CancelRequest,
    TaskSubmitResponse, TaskStatusResponse, TaskListResponse,
    TaskStatus
)
from ..task_manager import task_manager

router = APIRouter(prefix="/agent", tags=["Agent Tasks"])


@router.post(
    "/run",
    response_model=TaskSubmitResponse,
    summary="Submit a browser automation task",
    description="Submits a natural language instruction for the agent to execute. "
                "Returns immediately with a task_id. Poll /agent/status/{task_id} for progress."
)
async def submit_task(request: TaskRequest):
    """Submit a new agent task for async execution."""
    provider = request.provider.value if request.provider and request.provider.value != "auto" else None

    task = task_manager.submit_task(
        instruction=request.instruction,
        headless=request.headless,
        provider=provider,
        max_steps=request.max_steps
    )

    return TaskSubmitResponse(
        task_id=task.task_id,
        status=task.status,
        message=f"Task queued. Poll /api/agent/status/{task.task_id} for progress.",
        created_at=task.created_at.isoformat()
    )


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get task status and results",
    description="Returns the current status, plan, output, and extracted data for a task."
)
async def get_task_status(task_id: str):
    """Get status of a submitted task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    return TaskStatusResponse(**task.to_dict())


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    summary="List all tasks",
    description="Returns a list of recent tasks with their status."
)
async def list_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[TaskStatus] = Query(default=None)
):
    """List recent tasks, optionally filtered by status."""
    tasks = task_manager.list_tasks(limit=limit)

    if status:
        tasks = [t for t in tasks if t.status == status]

    return TaskListResponse(
        tasks=[TaskStatusResponse(**t.to_dict()) for t in tasks],
        total=len(tasks)
    )


@router.post(
    "/cancel/{task_id}",
    summary="Cancel a running task",
    description="Cancels an in-progress task. Cannot cancel completed/failed tasks."
)
async def cancel_task(task_id: str, request: CancelRequest = None):
    """Cancel a running task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    success = task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(
            status_code=409,
            detail=f"Task '{task_id}' cannot be cancelled (status: {task.status})"
        )

    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "Task cancelled successfully"
    }


@router.delete(
    "/task/{task_id}",
    summary="Delete a task record",
    description="Deletes a completed/failed/cancelled task record. Cannot delete running tasks."
)
async def delete_task(task_id: str):
    """Delete a task record."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    success = task_manager.delete_task(task_id)
    if not success:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete task '{task_id}' (still running)"
        )

    return {"task_id": task_id, "deleted": True}
