from langchain_core.tools import tool
from browser_agent.browser.manager import browser_manager

@tool
def get_page_text() -> str:
    """
    Returns the visible text of the page. 
    Use this to READ content (like product details) that isn't a button/link.
    """
    #time.sleep(15)
    page = browser_manager.get_page()
    if not page: return "Error: No page open"
    try:
        return page.evaluate("document.body.innerText")[:10000] # Limit to 10k chars
    except Exception as e:
        return f"Error reading text: {e}"

@tool
def extract_text_from_selector(selector: str) -> str:
    """
    Extracts visible text from a single specific element.
    Useful for: Getting the job title or company name from a specific card.
    
    Args:
        selector: CSS selector for the element
    """
    page = browser_manager.get_page()
    page.wait_for_load_state("load")
    if not page:
        return "Error: No browser page is open"
    try:
        if page.locator(selector).count() > 0:
            return page.locator(selector).first.inner_text().strip()
        return "Not Found"
    except Exception as e:
        print(f" Error Extracting text: {e}")
        return ""

@tool
def extract_attribute_from_selector(selector: str, attribute: str = "href") -> str:
    """
    Extracts an attribute (like 'href' for URLs) from an element.
    
    Args:
        selector: CSS selector for the element
        attribute: Attribute name to extract (default: href)
    """
    page = browser_manager.get_page()
    page.wait_for_load_state("load",timeout=60000)
    if not page:
        return "Error: No browser page is open"
    try:
        element = page.locator(selector).first
        return element.get_attribute(attribute) or ""
    except Exception as e:
        print(f"Error extracting attribute: {e}")
        return ""

@tool
def get_visible_input_fields() -> dict:
    """
    Gets all visible input fields on the current page with their placeholders and estimated purposes.
    Useful when fill_element fails and you need to find the right visible input to use.
    
    Returns a dictionary with placeholder text as keys and field info as values.
    """

    page = browser_manager.get_page()
    if not page:
        return {"error": "no browser page is open"}
    
    try:
        visible_fields = page.evaluate('''
            () => {
                const fields = {};
                const inputs = document.querySelectorAll('input[type="text"], input:not([type]), textarea, select');
                
                inputs.forEach((input, idx) => {
                    const style = window.getComputedStyle(input);
                    const isVisible = style.display !== 'none' && 
                                    style.visibility !== 'hidden' && 
                                    input.offsetParent !== null &&
                                    input.offsetWidth > 0 &&
                                    input.offsetHeight > 0;
                    
                    if (isVisible) {
                        const placeholder = input.placeholder || input.name || input.id || `field_${idx}`;
                        const tagName = input.tagName;
                        const value = input.value;
                        const classes = input.className;
                        
                        fields[placeholder] = {
                            tag: tagName,
                            placeholder: input.placeholder,
                            name: input.name,
                            id: input.id,
                            type: input.type,
                            value: value,
                            class: classes,
                            selector_options: [
                                input.id ? `#${input.id}` : null,
                                input.placeholder ? `input[placeholder="${input.placeholder}"]` : null,
                                input.placeholder ? `input[placeholder*="${input.placeholder.split(' ')[0]}"]` : null,
                                input.name ? `input[name="${input.name}"]` : null,
                            ].filter(Boolean)
                        };
                    }
                });
                
                return fields;
            }
        ''')
        return visible_fields if visible_fields else {"note":"No visible input fields found"}
    except Exception as e:
        return {"error" : f"Could not get visible input fields: {str(e)}"}