"""
Browser analysis tools for selector extraction, vision analysis, scraping, and page observation.
"""

from .helpers import (
    ask_human_help,
    open_browser,
    close_browser,
    extract_html_code,
    extract_page_content_as_markdown
)

from .selector_extraction import extract_and_analyze_selectors

from .vision import analyze_using_vision

from .scraping import scrape_data_using_text

from .screenshot_observer import observe_page

__all__ = [
    # Browser helpers
    "ask_human_help",
    "open_browser",
    "close_browser",
    "extract_html_code",
    "extract_page_content_as_markdown",
    
    # Selector extraction
    "extract_and_analyze_selectors",
    
    # Vision analysis
    "analyze_using_vision",
    
    # Text scraping
    "scrape_data_using_text",
    
    # Page observation (vision-based)
    "observe_page"
]

