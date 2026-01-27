from langchain_core.tools import tool
from browser_manager import browser_manager
from .base import get_som_state, set_som_state


@tool
def enable_vision_overlay():
    """
    Scans the page, draws Red Box IDs (Set-of-Marks) on interactive elements,
    and stores their details in memory.
    
    RETURNS: A summary count. DOES NOT return the full list to save tokens.
    You MUST use `find_element_ids(query)` after this to get specific IDs.
    """
    
    global SOM_STATE
    page = browser_manager.get_page()
    if not page: return "Error: No page open"

    try:
        elements_data = page.evaluate("""
            () => {
                document.querySelectorAll('.ai-som-overlay').forEach(el => el.remove());
                let idCounter = 1;
                let data = [];
                
                // Select inputs, buttons, links, etc.
                const elements = document.querySelectorAll('a, button, input, textarea, select, [role="button"], [onclick], [tabindex]:not([tabindex="-1"])');
                
                elements.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    
                    if (rect.width > 5 && rect.height > 5 && style.visibility !== 'hidden' && style.display !== 'none') {
                        
                        // Extract Text for Search
                        let text = el.innerText || el.placeholder || el.value || el.getAttribute('aria-label') || "";
                        text = text.replace(/\\s+/g, ' ').trim();
                        
                        // Filter empty non-inputs
                        if (!text && el.tagName.toLowerCase() !== 'input' && !el.querySelector('img')) return;

                        // Assign ID
                        el.setAttribute('data-ai-id', idCounter);
                        
                        // Draw Box
                        let overlay = document.createElement('div');
                        overlay.className = 'ai-som-overlay';
                        overlay.style.position = 'absolute';
                        overlay.style.left = (rect.left + window.scrollX) + 'px';
                        overlay.style.top = (rect.top + window.scrollY) + 'px';
                        overlay.style.width = rect.width + 'px';
                        overlay.style.height = rect.height + 'px';
                        overlay.style.border = '2px solid #FF0000';
                        overlay.style.zIndex = '2147483647';
                        overlay.style.pointerEvents = 'none';
                        
                        let label = document.createElement('span');
                        label.className = 'ai-som-overlay';
                        label.innerText = idCounter;
                        label.style.position = 'absolute';
                        label.style.top = '-20px';
                        label.style.left = '0';
                        label.style.backgroundColor = '#FF0000';
                        label.style.color = 'white';
                        label.style.fontSize = '12px';
                        label.style.zIndex = '2147483648';
                        
                        overlay.appendChild(label);
                        document.body.appendChild(overlay);
                        
                        // Add to Data List
                        data.push({
                            id: idCounter,
                            tag: el.tagName.toLowerCase(),
                            type: el.getAttribute('type') || '',
                            text: text.substring(0, 100) // Limit text length
                        });

                        idCounter++;
                    }
                });
                return data;
            }
        """)
        
        
        SOM_STATE = elements_data
        
        return f"Success: Overlay enabled. {len(elements_data)} elements indexed in memory. Use 'find_element_ids' to find specific items."

    except Exception as e:
        return f"Error enabling overlay: {e}"

@tool
def find_element_ids(query: str) -> str:
    """
    Searches the indexed Set-of-Marks elements for a specific text or description.
    
    Args:
        query: What you are looking for (e.g., "login", "search input", "apply button", "footer links")
    
    Returns:
        A list of matching Element IDs and their text.
    """

    global SOM_STATE
    if not SOM_STATE:
        return "Error: No elements indexed. Run 'enable_vision_overlay' first."
    
    query = query.lower().strip()
    matches = []
    
   
    for el in SOM_STATE:
       
        content = f"{el['tag']} {el['type']} {el['text']}".lower()
        
        if query in content:
            matches.append(f"[ID: {el['id']}] <{el['tag']}> {el['text']}")
    
    if not matches:
        return f"No elements found matching '{query}'. Try a broader term."
    
    
    return "Matches Found:\n" + "\n".join(matches[:20])


@tool
def get_interactive_elements() -> str:
    """
    Returns a list of all marked interactive elements on the screen.
    Format: [ID] Type: "Text content"
    Use this to decide which ID to click or fill.
    """
    page = browser_manager.get_page()
    if not page: return "Error: No page open"

    try:
        elements_info = page.evaluate("""
            () => {
                const els = document.querySelectorAll('[data-ai-id]');
                return Array.from(els).map(el => {
                    const tag = el.tagName.toLowerCase();
                    const type = el.getAttribute('type') || '';
                    const id = el.getAttribute('data-ai-id');
                    
                    // Get useful text
                    let text = el.innerText || el.placeholder || el.getAttribute('aria-label') || el.value || '';
                    text = text.replace(/\\s+/g, ' ').trim().substring(0, 50); // Clean and truncate
                    
                    return `[${id}] <${tag} ${type}>: "${text}"`;
                });
            }
        """)
        #print("Interactive Elements:\n" + "\n".join(elements_info))
        
        return "Interactive Elements:\n" + "\n".join(elements_info)
    except Exception as e:
        return f"Error getting elements: {e}"


@tool
def get_accessibility_tree() -> str:
    """
    Returns a simplified text representation of the page's interactive elements.
    Use this to 'see' the page structure and find IDs/Roles for elements.
    """
    page = browser_manager.get_page()
    if not page: return "Error: No page open"
    
    try:
        snapshot = page.accessibility.snapshot()
        
        def parse_node(node, depth=0):
            text = ""
            indent = "  " * depth
            
            
            role = node.get("role", "generic")
            name = node.get("name", "").strip()
            value = node.get("value", "")
            description = node.get("description", "")
            
            
            if name or value or role in ["button", "link", "textbox", "combobox", "checkbox"]:
                info = f"{role}"
                if name: info += f": '{name}'"
                if value: info += f" [Value: {value}]"
                if description: info += f" ({description})"
                
                text += f"{indent}- {info}\n"
            
            for child in node.get("children", []):
                text += parse_node(child, depth + 1)
            
            return text

        tree_text = parse_node(snapshot)
        return f"Current Page Interactive Elements:\n{tree_text}"
    except Exception as e:
        return f"Error getting accessibility tree: {e}"
