"""
Health check and system info routes.
"""

import time
from fastapi import APIRouter

from ..models import HealthResponse

router = APIRouter(tags=["System"])

# Track server start time
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns server health, LLM key counts, and browser status."
)
async def health_check():
    """Server health check with LLM key counts."""
    try:
        from browser_agent.llm.rate_limiter import api_key_rotator
        llm_keys = {
            "gemini": len(api_key_rotator.get_gemini_keys()),
            "groq": len(api_key_rotator.get_groq_keys()),
            "sambanova": len(api_key_rotator.get_sambanova_keys()),
        }
    except Exception:
        llm_keys = {"gemini": 0, "groq": 0, "sambanova": 0}

    try:
        from browser_agent.browser.manager import browser_manager
        browser_active = browser_manager.get_page() is not None
    except Exception:
        browser_active = False

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=round(time.time() - _start_time, 1),
        llm_keys=llm_keys,
        browser_active=browser_active
    )
