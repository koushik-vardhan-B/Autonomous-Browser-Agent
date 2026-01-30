"""
Prompts for browser automation agents.
"""

from .planning import (
    get_central_agent_prompt,
    get_central_agent_prompt1,
    get_central_agent_prompt2,
    get_central_agent_prompt3,
    get_central_agent_prompt4,
    get_central_agent_prompt5
)

from .execution import (
    get_navigator_prompt,
    get_autonomous_browser_prompt2,
    get_autonomous_browser_prompt3,
    get_autonomous_browser_prompt4
)

from .analysis import (
    get_code_analysis_prompt,
    get_vision_analysis_prompt
)

__all__ = [
    # Planning prompts (6 versions)
    "get_central_agent_prompt",
    "get_central_agent_prompt1",
    "get_central_agent_prompt2",
    "get_central_agent_prompt3",
    "get_central_agent_prompt4",
    "get_central_agent_prompt5",
    
    # Execution prompts (4 versions)
    "get_navigator_prompt",
    "get_autonomous_browser_prompt2",
    "get_autonomous_browser_prompt3",
    "get_autonomous_browser_prompt4",
    
    # Analysis prompts
    "get_code_analysis_prompt",
    "get_vision_analysis_prompt"
]
