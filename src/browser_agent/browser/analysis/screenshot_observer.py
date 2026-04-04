"""
Screenshot-based page observer — gives the agent "eyes".
Takes a screenshot and asks a vision LLM to describe what it sees,
enabling the agent to make decisions based on visual page state.
"""

import base64
import time
from typing import Optional
from langchain_core.tools import tool

from ...llm import LLMConfig
from ..manager import browser_manager


@tool
def observe_page(task_context: str) -> str:
    """
    Takes a screenshot of the current page and uses AI vision to understand it.
    
    Call this AFTER every major action (click, navigate, type) to:
    1. Verify your action worked
    2. Understand what's on the page now
    3. Decide what to do next
    
    Args:
        task_context: What you're trying to accomplish (e.g., "Find the search bar on Wikipedia")
    
    Returns:
        AI description of the page with recommended next actions
    """
    page = browser_manager.get_page()
    if not page or page.is_closed():
        return "Error: No browser page is open. Use open_browser first."
    
    try:
        page.wait_for_load_state("load", timeout=15000)
    except:
        pass  # Page might already be loaded
    
    # Take a screenshot (returns bytes directly)
    try:
        screenshot_bytes = page.screenshot(full_page=False)
        encoded = base64.b64encode(screenshot_bytes).decode("utf-8")
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"
    
    # Get current URL for context
    try:
        current_url = page.url
    except:
        current_url = "unknown"
    
    # Build the vision prompt
    vision_prompt = f"""You are an AI browser agent's eyes. Analyze this screenshot and help the agent.

CURRENT URL: {current_url}
AGENT'S TASK: {task_context}

Provide a concise response with:
1. **Page Description**: What page is this? What's the main content?
2. **Key Elements**: What clickable buttons, links, input fields, or important data do you see?
3. **Relevant Data**: Any data visible that relates to the task (prices, names, dates, etc.)
4. **Recommended Action**: What should the agent do next to accomplish the task?

Be specific and actionable. Mention exact text on buttons/links when visible."""

    # Get vision LLM and send screenshot
    llm_rotation = LLMConfig.get_vision_llm_with_rotation(0)
    
    for idx, (model_name, llm) in enumerate(llm_rotation):
        try:
            print(f"\n>>> observe_page trying {model_name}...")
            
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}}
                ]
            }]
            
            response = llm.invoke(messages)
            result = response.content if hasattr(response, 'content') else str(response)
            
            print(f">>> [OK] Page observed with {model_name}")
            return f"[Page Observation — {current_url}]\n{result}"
            
        except Exception as e:
            error_str = str(e).lower()
            if any(k in error_str for k in ["429", "rate limit", "quota", "resource_exhausted"]):
                print(f">>> [WARN] Rate limit on {model_name}, rotating...")
                continue
            else:
                print(f">>> observe_page error with {model_name}: {str(e)[:100]}")
                continue  # Try next model instead of failing
    
    return "Warning: Could not observe page (all vision models rate-limited). Proceed with text-based analysis."
