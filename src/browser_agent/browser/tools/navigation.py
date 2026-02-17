from langchain_core.tools import tool
from browser_agent.browser.manager import browser_manager

@tool 
def scroll_one_screen():
    """Scrolls down one screen."""
    page = browser_manager.get_page()
    if page:
        page.mouse.wheel(0, 600)
        return "Scroll down."
    return "No browser open."

@tool
def scroll_to_bottom():
    """Scrolls to the bottom of the page."""
    page = browser_manager.get_page()
    if not page:
        return "Error: No browser page is open"
    try:
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        return "Scrolled to bottom"
    except Exception as e:
        return f"Error scrolling: {str(e)}"