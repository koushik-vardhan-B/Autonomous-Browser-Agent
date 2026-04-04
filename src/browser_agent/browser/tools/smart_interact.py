"""
Smart interaction tools — uses accessibility tree + text matching
to find and interact with elements by description, not just IDs.
"""

from langchain_core.tools import tool
from browser_agent.browser.manager import browser_manager


@tool
def smart_click(description: str) -> str:
    """
    Intelligently finds and clicks an element by its visible text or description.
    Uses the accessibility tree to find the best match.
    
    Args:
        description: What to click (e.g., "Search button", "Sign in link", "Python programming language")
    
    Returns:
        Result of the click action
    """
    page = browser_manager.get_page()
    if not page or page.is_closed():
        return "Error: No browser page is open."
    
    query = description.lower().strip()
    
    # Strategy 1: Try exact text match with various selectors
    strategies = [
        # Buttons and links with exact/partial text
        f"button:has-text('{description}')",
        f"a:has-text('{description}')",
        f"[role='button']:has-text('{description}')",
        f"input[value='{description}']",
        # Common search patterns
        f"input[placeholder*='{description}' i]",
        f"input[aria-label*='{description}' i]",
        f"[title*='{description}' i]",
    ]
    
    for selector in strategies:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click(timeout=5000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                return f"Successfully clicked element matching '{description}' (selector: {selector})"
        except:
            continue
    
    # Strategy 2: Use accessibility snapshot for semantic matching
    try:
        snapshot = page.accessibility.snapshot()
        matches = _search_accessibility_tree(snapshot, query)
        
        if matches:
            best = matches[0]
            # Try clicking by role and name
            try:
                page.get_by_role(best["role"], name=best["name"]).first.click(timeout=5000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                return f"Successfully clicked '{best['name']}' (role: {best['role']})"
            except:
                # Fallback: click by text
                page.get_by_text(best["name"], exact=False).first.click(timeout=5000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                return f"Successfully clicked text '{best['name']}'"
    except Exception as e:
        pass
    
    # Strategy 3: Try generic text click
    try:
        page.get_by_text(description, exact=False).first.click(timeout=5000)
        page.wait_for_load_state("domcontentloaded", timeout=10000)
        return f"Successfully clicked text '{description}'"
    except:
        pass
    
    return f"Could not find element matching '{description}'. Try using enable_vision_overlay and find_element_ids instead."


@tool
def smart_type(text: str, field_description: str) -> str:
    """
    Intelligently finds an input field by description and types text into it.
    
    Args:
        text: The text to type
        field_description: Description of the input field (e.g., "search box", "email input", "username")
    
    Returns:
        Result of the type action
    """
    page = browser_manager.get_page()
    if not page or page.is_closed():
        return "Error: No browser page is open."
    
    query = field_description.lower().strip()
    
    # Strategy 1: Common input selectors
    strategies = [
        f"input[placeholder*='{field_description}' i]",
        f"input[aria-label*='{field_description}' i]",
        f"input[name*='{field_description}' i]",
        f"textarea[placeholder*='{field_description}' i]",
        f"[role='searchbox']",
        f"[role='textbox']",
        f"input[type='search']",
        f"input[type='text']",
    ]
    
    # For common field names, add specific selectors
    if any(w in query for w in ["search", "query", "find"]):
        strategies.insert(0, "input[type='search']")
        strategies.insert(1, "input[name='q']")
        strategies.insert(2, "input[name='search']")
        strategies.insert(3, "textarea[name='q']")
    elif any(w in query for w in ["email", "mail"]):
        strategies.insert(0, "input[type='email']")
    elif any(w in query for w in ["password", "pass"]):
        strategies.insert(0, "input[type='password']")
    
    for selector in strategies:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                element.click(timeout=3000)
                element.fill(text, timeout=5000)
                return f"Successfully typed '{text}' into field matching '{field_description}' (selector: {selector})"
        except:
            continue
    
    # Strategy 2: Accessibility tree
    try:
        snapshot = page.accessibility.snapshot()
        matches = _search_accessibility_tree(snapshot, query, roles=["textbox", "searchbox", "combobox"])
        
        if matches:
            best = matches[0]
            try:
                element = page.get_by_role(best["role"], name=best.get("name", "")).first
                element.click(timeout=3000)
                element.fill(text, timeout=5000)
                return f"Successfully typed '{text}' into '{best.get('name', best['role'])}'"
            except:
                pass
    except:
        pass
    
    # Strategy 3: Try the first visible input
    try:
        first_input = page.locator("input:visible, textarea:visible").first
        first_input.click(timeout=3000)
        first_input.fill(text, timeout=5000)
        return f"Typed '{text}' into the first visible input field"
    except:
        pass
    
    return f"Could not find input field matching '{field_description}'. Try using get_visible_input_fields to see available fields."


def _search_accessibility_tree(node, query, roles=None, depth=0, max_depth=10):
    """Recursively search accessibility tree for matching elements."""
    if depth > max_depth:
        return []
    
    matches = []
    name = (node.get("name", "") or "").lower()
    role = (node.get("role", "") or "").lower()
    description = (node.get("description", "") or "").lower()
    
    # Check if role filter applies
    role_match = True
    if roles:
        role_match = role in [r.lower() for r in roles]
    
    # Score the match
    if query in name or query in description:
        if role_match:
            matches.append({
                "name": node.get("name", ""),
                "role": node.get("role", ""),
                "score": len(query) / max(len(name), 1)  # Higher score = better match
            })
    
    # Search children
    for child in node.get("children", []):
        matches.extend(_search_accessibility_tree(child, query, roles, depth + 1, max_depth))
    
    # Sort by score (best match first)
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches
