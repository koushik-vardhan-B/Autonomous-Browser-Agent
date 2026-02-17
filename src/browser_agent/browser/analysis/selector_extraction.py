"""
Selector extraction strategy using code analysis.
"""

from langchain_core.tools import tool
from ...llm import LLMConfig
from ...core import build_attributes_model
from ...prompts import get_code_analysis_prompt
from ..manager import browser_manager


@tool
def extract_and_analyze_selectors(requirements: list[str], provider: str = None):
    """
    Extracts HTML code from current page and immediately analyzes it for selectors.
    
    This is a combined function that replaces the need to call extract_html_code() 
    followed by extract_selector_from_code().
    
    Uses LLM rotation with rate limit handling to extract robust Playwright selectors
    from the page's HTML source code.
    
    Args:
        requirements: List of UI elements to find selectors for (e.g., ["login button", "password field"])
        provider: Optional LLM provider ("gemini", "groq", "sambanova", "ollama", or None for all)
    
    Returns:
        Dict mapping requirement names to selector information (playwright_selector, strategy_used, element_name)
        or {"error": "..."} on failure
    """
    try:
        page = browser_manager.get_page()
        
        if not page:
            return {"error": "No browser page is open"}
        
        page.wait_for_load_state("load", timeout=60000)
        
        html_code = page.content()
            
        requirements_text = "\n".join(requirements)
        
        # Get LLM rotation list with optional provider filter
        llm_rotation = LLMConfig.get_main_llm_with_rotation(0, provider=provider)
        
        # Try each LLM in rotation until success or all exhausted
        for idx, (model_name, llm) in enumerate(llm_rotation):
            try:
                print(f"\n>>> extract_and_analyze_selectors trying {model_name}...")
                
                prompt = get_code_analysis_prompt(requirements_text, html_code)
                
                # Use structured output with dynamically built model
                structured_llm = llm.with_structured_output(
                    build_attributes_model("Element_Properties", requirements)
                )
                response = structured_llm.invoke(prompt)
                
                print(f">>> Successfully extracted selectors with {model_name}")
                
                # Clean response: fallback to text-based selector if LLM returned placeholder
                clean_response = {}
                for key, val in response.dict().items():
                    sel = val.get('playwright_selector', '')
                    if "sample" in sel.lower() or len(sel) < 2:
                        print(f"Bad selector for {key}, attempting generic fallback")
                        clean_response[key] = f"text={key}"  # Fallback to text selector
                    else:
                        clean_response[key] = val
            
                return clean_response
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if "429" in error_str or "rate limit" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                    print(f">>> [WARN] Rate limit hit on {model_name}, rotating to next key...")
                    continue  # Try next LLM
                else:
                    print(f">>> Error in selector extraction: {error_str}")
                    return {"error": f"Extraction failed: {str(e)}"}
        
        # All keys exhausted
        return {"error": "All API keys exhausted due to rate limits"}
        
    except Exception as e:
        error = f"Error in extract_and_analyze_selectors: {str(e)}"
        return {"error": error}
