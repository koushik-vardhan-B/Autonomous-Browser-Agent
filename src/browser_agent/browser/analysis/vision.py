"""
Vision-based analysis strategy using screenshots and vision LLMs.
"""

import os
import time
import base64
from typing import Optional, Literal
from langchain_core.tools import tool

from ...llm import LLMConfig
from ...prompts import get_vision_analysis_prompt
from ...core import extract_json_from_markdown
from ..manager import browser_manager


@tool
def analyze_using_vision(
    requirements: list[str], 
    analysis_type: Optional[Literal[
        "element_detection", 
        "page_verification", 
        "form_verification", 
        "filter_detection", 
        "hover_detection", 
        "modal_detection",
        "data_extraction"
    ]] = "element_detection", 
    model: Optional[Literal["ollama", "groq"]] = "ollama"
):
    """
    Analyzes the current page using vision AI and returns the result.
    
    Takes 5 screenshots by scrolling down to cover more of the page.
    Automatically selects the best available vision model (Ollama or Groq) with rotation.
    
    Args:
        requirements: List of requirements for analysis (e.g., ["login button", "search input"])
        analysis_type: Type of analysis to perform:
            - "element_detection": Locate UI elements by description
            - "page_verification": Check if specific requirements are visible
            - "form_verification": Verify if form fields are filled
            - "filter_detection": Detect filter options on job listing pages
            - "hover_detection": Detect tooltips/help text
            - "modal_detection": Detect if modal/popup is visible
            - "data_extraction": Extract structured data from screenshots
        model: Legacy argument, ignored in favor of auto-config with rotation
        
    Returns:
        JSON response from vision LLM or {"error": "..."} on failure
    """
    page = browser_manager.get_page()
    page.wait_for_load_state("load", timeout=60000)
    
    screenshot_paths = []
    
    # Take 5 screenshots while scrolling down
    try:
        for i in range(5):
            path = f"screenshot_{i}.png"
            page.screenshot(path=path)
            screenshot_paths.append(path)
            
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            time.sleep(1)  # Wait for scroll animation
            
    except Exception as e:
        print(f"Error extracting screenshots: {str(e)}")
        
        # Cleanup on error
        for p in screenshot_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
        return {"error": f"Screenshot error: {str(e)}"}
    
    # Encode screenshots as base64 for LLM
    image_contents = []
    try:
        for path in screenshot_paths:
            with open(path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
            mime_type = "image/png"
            img_url = f"data:{mime_type};base64,{img_b64}"
            image_contents.append({"type": "image_url", "image_url": {"url": img_url}})
            
    except Exception as e:
        print(f"Error encoding screenshots: {str(e)}")
        for p in screenshot_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
        return {"error": f"Encoding error: {str(e)}"}
    finally:
        # Always cleanup screenshot files
        for p in screenshot_paths:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

    # Build vision prompt
    img_width, img_height = 1920, 1080  # Standard desktop resolution
    requirements_text = "\n".join(requirements)
    prompt = get_vision_analysis_prompt(requirements_text, img_width, img_height, analysis_type)
    prompt += "\n\nNote: You are provided with 5 sequential screenshots of the page, scrolling down from top to bottom. Use all of them to find the requested elements."

    # Scroll back to top
    try:
        page.evaluate("window.scrollTo(0, 0)")
    except:
        pass

    # Get vision LLM rotation (Ollama first, then Groq)
    llm_rotation = LLMConfig.get_vision_llm_with_rotation(0)
    
    # Try each vision LLM in rotation
    for idx, (model_name, llm) in enumerate(llm_rotation):
        try:
            print(f"\n>>> analyze_using_vision trying {model_name}...")
            
            # Message format: text prompt + N images
            content_block = [{"type": "text", "text": prompt}] + image_contents
            
            messages = [
                {"role": "user", "content": content_block},
            ]
            
            response = llm.invoke(messages)
            json_response = extract_json_from_markdown(response.content)
            
            print(f">>> [OK] Successfully analyzed vision with {model_name}")
            return json_response
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                print(f">>> [WARN] Rate limit hit on {model_name}, rotating to next key...")
                continue  # Try next LLM
            else:
                print(f">>> Error in vision analysis: {str(e)}")
                return {"error": f"Vision analysis failed: {str(e)}"}
    
    # All vision keys exhausted
    return {"error": "All vision API keys exhausted due to rate limits"}
