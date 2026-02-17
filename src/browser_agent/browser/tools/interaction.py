from langchain_core.tools import tool
from browser_agent.browser.manager import browser_manager


@tool
def click_id(element_id: int):
    """
    Clicks an element by its Set-of-Marks ID. 
    Example: click_id(12)
    """
    #time.sleep(15)
    page = browser_manager.get_page()
    if not page: return "Error: No page open"
    
    try:
        loc = page.locator(f'[data-ai-id="{element_id}"]').first
        if loc.count() == 0:
            return f"Error: Element ID {element_id} not found. Did you run enable_vision_overlay()?"
        
        loc.scroll_into_view_if_needed()
        loc.click(force=True) 
        return f"Clicked Element #{element_id}"
    except Exception as e:
        return f"Error clicking #{element_id}: {e}"

@tool
def fill_id(element_id: int, text: str):
    """
    Fills an input element by its Set-of-Marks ID.
    Example: fill_id(45, "Python Developer")
    """
    #time.sleep(15)
    page = browser_manager.get_page()
    if not page: return "Error: No page open"
    
    try:
        loc = page.locator(f'[data-ai-id="{element_id}"]').first
        if loc.count() == 0:
            return f"Error: Element ID {element_id} not found."
            
        loc.scroll_into_view_if_needed()
        loc.fill(text)
        return f"Filled Element #{element_id} with '{text}'"
    except Exception as e:
        return f"Error filling #{element_id}: {e}"


@tool
def press_key(key: str):
    """Presses a key (Enter, Escape, ArrowDown, Tab)."""
    page = browser_manager.get_page()
    if page:
        page.keyboard.press(key)
        return f"Pressed {key}"
    return "No browser open."


@tool
def upload_file_by_id(element_id: int, file_path: str):
    """Uploads file."""
    page = browser_manager.get_page()
    if not page: return "No browser open."
    try:
        loc = page.locator(f'[data-ai-id="{element_id}"]').first
        loc.set_input_files(file_path)
        return f"Uploaded to #{element_id}"
    except Exception as e:
        return f"Upload error: {e}"


@tool
def click_element(selector: str):
    """Clicks an element. Handles 'Strict Mode' and Overlays automatically."""
    page = browser_manager.get_page()
    if not page: return "Error: No browser page is open"
    
    try:
        
        count = page.locator(selector).count()
        if count > 1:
            print(f"Warning: {count} elements found for '{selector}'. Clicking the first visible one.")
            locator = page.locator(selector).filter(has=page.locator("visible=true")).first
            if not locator.is_visible():
                locator = page.locator(selector).first
        else:
            locator = page.locator(selector).first

        
        locator.scroll_into_view_if_needed()
        page.wait_for_timeout(500)

        
        try:
            locator.click(timeout=2000)
        except Exception as e:
            print(f"Standard click failed ({e}). forcing click...")
            locator.click(force=True)
            
        page.wait_for_load_state("domcontentloaded")
        return f"Clicked: {selector}"
    except Exception as e:
        return f"Error clicking: {str(e)}"

@tool
def fill_element(selector: str, text: str):
    """Fills input. Uses JS Injection if standard fill is blocked (Fixes Wellfound)."""
    page = browser_manager.get_page()
    if not page: return "Error: No browser page is open"
    
    try:
        locator = page.locator(selector).first
        
        
        if not locator.is_visible():
            locator.scroll_into_view_if_needed()
            page.wait_for_timeout(500)

        
        try:
            locator.click(force=True, timeout=1000)
            locator.clear()
            page.keyboard.type(text, delay=50)
            return f"Filled {selector} with: {text}"
        except Exception:
            print(f"Standard fill failed. Using JS Injection for {selector}...")

        
        page.evaluate(f"""
            const el = document.querySelector('{selector}');
            if (el) {{
                el.value = '{text}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            }}
        """)
        
        page.keyboard.press("Enter")
        
        return f"Filled {selector} using JS Injection."
    except Exception as e:
        return f"Error filling: {str(e)}"

@tool
def select_dropdown_option(option_text: str, dropdown_selector: str = None, option_selector: str = None):
    """
    Selects an option from a visible dropdown menu.
    
    Args:
        option_text: The visible text of the option to click.
        dropdown_selector: (Optional) The container of the dropdown.
        option_selector: (Optional) The specific selector for the option element.
    """
    page = browser_manager.get_page()
    if not page:
        return "Error: No browser page is open"
    
    try:
        
        page.wait_for_timeout(500)
        
        target_option = None

        
        if dropdown_selector and option_selector:
            
            target_option = page.locator(f"{dropdown_selector} {option_selector}").filter(has_text=option_text).first
            if target_option.count() == 0:
                
                target_option = page.locator(f"{dropdown_selector} span, {dropdown_selector} div").filter(has_text=option_text).first
        
        
        elif option_text:
            
            target_option = page.get_by_text(option_text, exact=True).first
            if not target_option.is_visible():
                 target_option = page.get_by_text(option_text, exact=False).first

        
        if target_option and target_option.count() > 0 and target_option.is_visible():
            target_option.scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            target_option.click(force=True) 
            page.wait_for_timeout(800)
            return f"Selected option: '{option_text}'"
        else:
            return f"Error: Option '{option_text}' not visible. Ensure the dropdown is open first."

    except Exception as e:
        return f"Error selecting option: {str(e)}"

@tool
def open_dropdown_and_select(dropdown_selector: str, option_text: str, click_to_open: bool = True):
    """
    Opens a dropdown menu and selects a specific option.
    Useful for custom dropdown implementations (not native <select> elements).
    
    Args:
        dropdown_selector: CSS selector for the dropdown trigger/container
        option_text: The visible text of the option to select
        click_to_open: Whether to click the dropdown to open it (default True)
    
    Returns:
        Status message indicating success or error
    """
    page = browser_manager.get_page()
    if not page:
        return "Error: No browser page is open"
    
    try:
        
        dropdown_trigger = page.locator(dropdown_selector).first
        
        if not dropdown_trigger.is_visible():
            dropdown_trigger.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
        
        if click_to_open:
            dropdown_trigger.click(force=True)
            page.wait_for_timeout(1000)  # Wait for dropdown animation
        
        
        option_element = None
        
        
        option_element = page.get_by_text(option_text, exact=True).first
        
        
        if option_element.count() == 0:
            option_element = page.get_by_text(option_text, exact=False).first
        
        
        if option_element.count() == 0:
            option_element = page.locator(f"span:has-text('{option_text}'), div:has-text('{option_text}'), option:has-text('{option_text}')").first
        
        
        if option_element.count() > 0 and option_element.is_visible():
            option_element.scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            option_element.click(force=True)
            page.wait_for_timeout(800)
            return f"Successfully opened dropdown and selected: '{option_text}'"
        else:
            return f"Error: Could not find option '{option_text}' in dropdown menu. Dropdown may not have opened correctly."
    
    except Exception as e:
        return f"Error in dropdown selection: {str(e)}"

@tool
def select_native_select_option(select_selector: str, option_value: str):
    """
    Selects an option from a native HTML <select> element.
    Use this for standard HTML select dropdowns (not custom implementations).
    
    Args:
        select_selector: CSS selector for the <select> element
        option_value: The value of the <option> to select (can be the visible text)
    
    Returns:
        Status message
    """
    page = browser_manager.get_page()
    if not page:
        return "Error: No browser page is open"
    
    try:
        select_element = page.locator(select_selector).first
        
        if not select_element.is_visible():
            select_element.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
        
     
        select_element.select_option(option_value)
        page.wait_for_timeout(800)
        
        return f"Selected '{option_value}' from select element"
    except Exception as e:
        return f"Error selecting from select element: {str(e)}"

@tool
def hover_element(selector: str, wait_time: int = 1500):
    """
    Hovers over an element to trigger tooltips, help text, or field validation messages.
    Useful for revealing additional information when hovering over input fields, help icons, or info buttons.
    
    Args:
        selector: CSS selector for the element to hover over
        wait_time: Time in milliseconds to wait after hovering for tooltip/help text to appear (default: 1500ms)
    
    Returns:
        Status message indicating success or error
    """
    page = browser_manager.get_page()
    if not page:
        return "Error: No browser page is open"
    
    try:
        element = page.locator(selector).first
        
        
        if element.count() == 0:
            return f"Error: Element not found with selector: {selector}"
        
    
        if not element.is_visible():
            element.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
        
        
        if not element.is_visible():
            return f"Error: Element with selector '{selector}' exists but is not visible"
        
        
        element.hover(force=True)
        
        
        page.wait_for_timeout(wait_time)
        
        return f"Successfully hovered over element: {selector}. Tooltip/help text should now be visible."
    
    except Exception as e:
        return f"Error hovering over element: {str(e)}"
