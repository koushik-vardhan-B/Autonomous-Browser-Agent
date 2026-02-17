"""
Browser Agent - Autonomous web automation powered by LLMs.
"""

from .orchestration import run_agent, create_agent, AgentState

__version__ = "1.0.0"

__all__ = [
    "run_agent",
    "create_agent",
    "AgentState"
]
