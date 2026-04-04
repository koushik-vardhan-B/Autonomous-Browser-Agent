"""
Log streaming routes — read agent.log and task-specific logs.
"""

import os
import re
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional

from ..models import LogStreamResponse, LogEntry
from ..task_manager import task_manager

router = APIRouter(prefix="/logs", tags=["Logs"])

# Log file paths
_LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
AGENT_LOG = os.path.join(_LOG_DIR, 'agent.log')
ERROR_LOG = os.path.join(_LOG_DIR, 'error.log')


def _parse_log_line(line: str) -> Optional[LogEntry]:
    """Parse a structured log line into a LogEntry."""
    line = line.strip()
    if not line or line.startswith("==="):
        return None

    # Match format: 2026-04-03 11:35:44 | INFO    | Orchestration | message
    pattern = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*\|\s*(\w+)\s*\|\s*([\w\s]+?)\s*\|\s*(.+)$'
    match = re.match(pattern, line)

    if match:
        return LogEntry(
            timestamp=match.group(1),
            level=match.group(2).strip(),
            source=match.group(3).strip(),
            message=match.group(4).strip()
        )

    # Print-style log: 2026-04-03 11:35:44 | PRINT   | message
    pattern2 = r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*\|\s*PRINT\s*\|\s*(.+)$'
    match2 = re.match(pattern2, line)
    if match2:
        return LogEntry(
            timestamp=match2.group(1),
            level="PRINT",
            source="stdout",
            message=match2.group(2).strip()
        )

    # Unstructured line — include as-is
    if len(line) > 3 and not line.startswith("[notice]"):
        return LogEntry(
            timestamp="",
            level="INFO",
            source="agent",
            message=line
        )

    return None


@router.get(
    "/agent",
    response_model=LogStreamResponse,
    summary="Get recent agent logs",
    description="Returns the last N lines from agent.log, parsed into structured entries."
)
async def get_agent_logs(
    lines: int = Query(default=50, ge=1, le=500, description="Number of recent lines"),
    level: Optional[str] = Query(default=None, description="Filter by log level (INFO, WARNING, ERROR)")
):
    """Get recent agent log entries."""
    if not os.path.exists(AGENT_LOG):
        return LogStreamResponse(entries=[], total_lines=0)

    with open(AGENT_LOG, 'r', encoding='utf-8', errors='ignore') as f:
        all_lines = f.readlines()

    total = len(all_lines)
    recent = all_lines[-lines:]

    entries = []
    for line in recent:
        entry = _parse_log_line(line)
        if entry:
            if level and entry.level.upper() != level.upper():
                continue
            entries.append(entry)

    return LogStreamResponse(entries=entries, total_lines=total)


@router.get(
    "/errors",
    response_model=LogStreamResponse,
    summary="Get error logs",
    description="Returns recent entries from error.log (warnings and errors only)."
)
async def get_error_logs(
    lines: int = Query(default=30, ge=1, le=200)
):
    """Get recent error log entries."""
    if not os.path.exists(ERROR_LOG):
        return LogStreamResponse(entries=[], total_lines=0)

    with open(ERROR_LOG, 'r', encoding='utf-8', errors='ignore') as f:
        all_lines = f.readlines()

    total = len(all_lines)
    recent = all_lines[-lines:]

    entries = []
    for line in recent:
        entry = _parse_log_line(line)
        if entry:
            entries.append(entry)

    return LogStreamResponse(entries=entries, total_lines=total)


@router.get(
    "/task/{task_id}",
    response_model=LogStreamResponse,
    summary="Get task-specific logs",
    description="Returns the live log buffer for a specific task."
)
async def get_task_logs(task_id: str):
    """Get logs for a specific task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    entries = [
        LogEntry(
            timestamp=e["timestamp"],
            level=e["level"],
            source="task",
            message=e["message"]
        )
        for e in task.log_buffer
    ]

    return LogStreamResponse(
        task_id=task_id,
        entries=entries,
        total_lines=len(entries)
    )


@router.get(
    "/stream",
    summary="Stream agent logs (SSE)",
    description="Server-Sent Events stream of agent.log. Connect and receive new lines in real-time."
)
async def stream_logs():
    """Stream agent logs as Server-Sent Events."""
    import asyncio

    async def event_generator():
        if not os.path.exists(AGENT_LOG):
            yield "data: {\"message\": \"Waiting for logs...\"}\n\n"
            return

        with open(AGENT_LOG, 'r', encoding='utf-8', errors='ignore') as f:
            # Seek to end
            f.seek(0, 2)

            while True:
                line = f.readline()
                if line:
                    entry = _parse_log_line(line)
                    if entry:
                        import json
                        yield f"data: {json.dumps(entry.model_dump())}\n\n"
                else:
                    await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
