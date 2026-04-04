"""
Task Manager — handles async agent execution with status tracking.
Since browser agent runs are long (30s-5min), we run them in background threads
and expose status via API polling + WebSocket streaming.
"""

import uuid
import threading
import time
import traceback
from datetime import datetime
from typing import Dict, Optional, List, Callable
from collections import deque

from .models import TaskStatus, StepInfo


class TaskRecord:
    """In-memory record for a single agent task."""

    def __init__(self, task_id: str, instruction: str, headless: bool = True,
                 provider: Optional[str] = None, max_steps: int = 30):
        self.task_id = task_id
        self.instruction = instruction
        self.headless = headless
        self.provider = provider
        self.max_steps = max_steps

        # Lifecycle timestamps
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # Status
        self.status = TaskStatus.QUEUED
        self.current_step: Optional[int] = None
        self.total_steps: Optional[int] = None
        self.plan: List[StepInfo] = []

        # Results
        self.output: Optional[str] = None
        self.error: Optional[str] = None
        self.extracted_data: List[str] = []
        self.provider_used: Optional[str] = None

        # Execution
        self._thread: Optional[threading.Thread] = None
        self._cancelled = False

        # Live log buffer (last 200 lines for this task)
        self.log_buffer: deque = deque(maxlen=200)

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at:
            end = self.completed_at or datetime.now()
            return (end - self.started_at).total_seconds() * 1000
        return None

    def add_log(self, message: str, level: str = "INFO"):
        """Add a log entry to this task's buffer."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.log_buffer.append(entry)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to API response dict."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "instruction": self.instruction,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "plan": self.plan,
            "output": self.output,
            "error": self.error,
            "extracted_data": self.extracted_data,
            "provider_used": self.provider_used,
        }


class TaskManager:
    """
    Manages agent task lifecycle — submit, execute, track, cancel.
    Uses background threads for non-blocking execution.
    """

    def __init__(self):
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock = threading.Lock()
        self._event_listeners: Dict[str, List[Callable]] = {}

    def submit_task(
        self,
        instruction: str,
        headless: bool = True,
        provider: Optional[str] = None,
        max_steps: int = 30
    ) -> TaskRecord:
        """
        Submit a new task for execution.
        Returns immediately with a task_id for polling.
        """
        task_id = str(uuid.uuid4())[:8]
        task = TaskRecord(
            task_id=task_id,
            instruction=instruction,
            headless=headless,
            provider=provider,
            max_steps=max_steps
        )

        with self._lock:
            self._tasks[task_id] = task

        # Start execution in background thread
        thread = threading.Thread(
            target=self._execute_task,
            args=(task,),
            daemon=True,
            name=f"agent-task-{task_id}"
        )
        task._thread = thread
        thread.start()

        return task

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 20) -> List[TaskRecord]:
        """List recent tasks, newest first."""
        tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )
        return tasks[:limit]

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return False

        task._cancelled = True
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        task.add_log("Task cancelled by user", "WARNING")
        self._notify_listeners(task_id, "cancelled")
        return True

    def delete_task(self, task_id: str) -> bool:
        """Delete a task record (only completed/failed/cancelled)."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task.status in (TaskStatus.QUEUED, TaskStatus.PLANNING, TaskStatus.EXECUTING):
            return False  # Can't delete running tasks

        with self._lock:
            del self._tasks[task_id]
        return True

    def add_event_listener(self, task_id: str, callback: Callable):
        """Add a listener for task events (for WebSocket streaming)."""
        if task_id not in self._event_listeners:
            self._event_listeners[task_id] = []
        self._event_listeners[task_id].append(callback)

    def remove_event_listener(self, task_id: str, callback: Callable):
        """Remove a task event listener."""
        if task_id in self._event_listeners:
            self._event_listeners[task_id] = [
                cb for cb in self._event_listeners[task_id] if cb != callback
            ]

    def _notify_listeners(self, task_id: str, event_type: str, data: dict = None):
        """Notify all listeners for a task."""
        for callback in self._event_listeners.get(task_id, []):
            try:
                callback(event_type, data or {})
            except Exception:
                pass

    def _execute_task(self, task: TaskRecord):
        """
        Execute the agent task in a background thread.
        This is the bridge between FastAPI and the orchestration engine.
        """
        try:
            task.status = TaskStatus.PLANNING
            task.started_at = datetime.now()
            task.add_log(f"Starting task: {task.instruction[:100]}")
            self._notify_listeners(task.task_id, "started")

            # Import here to avoid circular imports and keep startup fast
            from browser_agent.orchestration import run_agent
            from browser_agent.browser.manager import browser_manager

            # Set headless mode
            browser_manager.headless = task.headless
            task.add_log(f"Browser headless={task.headless}")

            # Check for cancellation
            if task._cancelled:
                return

            task.status = TaskStatus.EXECUTING
            task.add_log("Calling orchestration engine...")
            self._notify_listeners(task.task_id, "executing")

            # Run the agent
            result = run_agent(
                task.instruction,
                provider=task.provider
            )

            # Check for cancellation
            if task._cancelled:
                return

            # Parse result
            if isinstance(result, dict):
                task.output = result.get("output", str(result))
                task.error = result.get("error")

                # Extract plan info
                raw_plan = result.get("plan", [])
                if raw_plan:
                    task.total_steps = len(raw_plan)
                    task.plan = [
                        StepInfo(
                            step_number=s.get("step_number", i + 1),
                            agent=s.get("agent", "unknown"),
                            query=s.get("query", ""),
                            status="completed"
                        )
                        for i, s in enumerate(raw_plan)
                    ]

                # Extract data
                extracted = result.get("output_content", [])
                if extracted:
                    task.extracted_data = [str(d) for d in extracted]

                if task.error:
                    task.status = TaskStatus.FAILED
                    task.add_log(f"Task failed: {task.error}", "ERROR")
                else:
                    task.status = TaskStatus.COMPLETED
                    task.add_log("Task completed successfully")
            else:
                task.output = str(result)
                task.status = TaskStatus.COMPLETED
                task.add_log("Task completed")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.add_log(f"Task crashed: {traceback.format_exc()}", "ERROR")

        finally:
            task.completed_at = datetime.now()
            task.updated_at = datetime.now()
            self._notify_listeners(task.task_id, "finished", task.to_dict())


# ─── Global singleton ────────────────────────────────────────────────────────
task_manager = TaskManager()
