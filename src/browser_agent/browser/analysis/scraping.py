"""
Text-based scraping strategy using markdown extraction and LLM analysis.
"""

from langchain_core.tools import tool

from ...llm import LLMConfig
from ...core import extract_json_from_markdown
from .helpers import extract_page_content_as_markdown


@tool
def scrape_data_using_text(requirements: str, provider: str = None):
    """
    Scrapes structured data (JSON) from the page using text analysis.
    
    FAST & CHEAP alternative to Vision-based scraping.
    Extracts page content as markdown, then uses LLM to extract structured data.
    
    Args:
        requirements: What to extract (e.g., "list of products with name, price, and url")
        provider: Optional LLM provider ("gemini", "groq", "sambanova", "ollama", or None for all)
        
    Returns:
        JSON response with extracted data or {"error": "..."} on failure
        
    Example:
        >>> scrape_data_using_text("list of job postings with title, company, location")
        {
            "items": [
                {"title": "Software Engineer", "company": "Google", "location": "Mountain View"},
                ...
            ],
            "count": 30
        }
    """
    # Extract page content as markdown
    content = extract_page_content_as_markdown()
    
    if "Error" in content:
        return {"error": content}

    # Get LLM rotation with optional provider filter
    llm_rotation = LLMConfig.get_main_llm_with_rotation(0, provider=provider)

    prompt = f"""
    You are a Data Extraction Agent.
    
    ### USER REQUEST
    Extract the following data: {requirements}
    
    ### PAGE CONTENT (Markdown)
    {content}
    
    ### INSTRUCTIONS
    1. Identify all items matching the request.
    2. Extract details accurately.
    3. Return ONLY valid JSON.
    
    ### FORMAT
    {{
      "items": [
        {{ "name": "...", "price": "...", "url": "...", "description": "..." }}
      ],
      "count": N
    }}
    """
    
    # Try each LLM in rotation
    for idx, (model_name, llm) in enumerate(llm_rotation):
        try:
            print(f"\n>>> scrape_data_using_text trying {model_name}...")
            
            response = llm.invoke(prompt)
            result = extract_json_from_markdown(response.content)
            
            print(f">>> [OK] Successfully scraped data with {model_name}")
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                print(f">>> [WARN] Rate limit hit on {model_name}, rotating to next key...")
                continue  # Try next LLM
            else:
                print(f">>> LLM Extraction failed: {e}")
                return {"error": f"LLM Extraction failed: {e}"}
    
    # All keys exhausted
    return {"error": "All API keys exhausted due to rate limits"}
