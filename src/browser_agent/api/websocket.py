"""
WebSocket handler for real-time task updates.
Frontend connects here to get live status updates during agent execution.
"""

import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .task_manager import task_manager, TaskRecord

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/task/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates.
    
    Protocol:
    - Server sends JSON messages with task status updates
    - Client can send 'cancel' to cancel the task
    - Connection closes when task completes/fails/cancels
    
    Message format:
    {
        "event": "status_update" | "log" | "step_update" | "completed" | "error",
        "data": { ... }
    }
    """
    await websocket.accept()

    task = task_manager.get_task(task_id)
    if not task:
        await websocket.send_json({
            "event": "error",
            "data": {"message": f"Task '{task_id}' not found"}
        })
        await websocket.close()
        return

    # Send initial status
    await websocket.send_json({
        "event": "status_update",
        "data": task.to_dict()
    })

    # Event queue for this connection
    event_queue = asyncio.Queue()

    def on_task_event(event_type: str, data: dict):
        """Callback for task events — puts them in the async queue."""
        try:
            event_queue.put_nowait({
                "event": event_type,
                "data": data
            })
        except asyncio.QueueFull:
            pass

    # Register listener
    task_manager.add_event_listener(task_id, on_task_event)

    try:
        while True:
            # Check for client messages (cancel, ping) with timeout
            try:
                client_msg = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=1.0
                )
                if client_msg.strip().lower() == "cancel":
                    task_manager.cancel_task(task_id)
                    await websocket.send_json({
                        "event": "cancelled",
                        "data": {"message": "Task cancelled by client"}
                    })
            except asyncio.TimeoutError:
                pass

            # Drain event queue and send to client
            while not event_queue.empty():
                event = await event_queue.get()
                await websocket.send_json(event)

            # Send periodic status updates
            task = task_manager.get_task(task_id)
            if task:
                await websocket.send_json({
                    "event": "status_update",
                    "data": task.to_dict()
                })

                # Check if task is finished
                if task.status.value in ("completed", "failed", "cancelled"):
                    await websocket.send_json({
                        "event": "finished",
                        "data": task.to_dict()
                    })
                    break

            await asyncio.sleep(2)  # Poll interval

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "event": "error",
                "data": {"message": str(e)}
            })
        except Exception:
            pass
    finally:
        task_manager.remove_event_listener(task_id, on_task_event)
        try:
            await websocket.close()
        except Exception:
            pass
