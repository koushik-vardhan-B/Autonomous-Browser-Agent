"""
Code and vision analysis prompts for browser automation.
"""


def get_code_analysis_prompt(requirements: str, code: str) -> str:
    """
    Generate a code analysis prompt for extracting Playwright selectors from HTML/JSX/TSX/Vue/Angular.
    
    This prompt is used by the code analysis tool to extract robust, stable CSS selectors
    from source code based on user requirements.
    
    Args:
        requirements: List of UI elements to extract selectors for (e.g., "Login Button, Search Input")
        code: Raw source code (HTML, JSX, TSX, Vue, Angular templates)
        
    Returns:
        Formatted prompt string for LLM
    """
    prompt = f"""### ROLE
Act as a Senior SDET (Software Development Engineer in Test) and an expert in Playwright automation. Your goal is to analyze the provided source code (HTML, JSX, TSX, Vue, or Angular templates) and generate the most robust, stable, and maintainable Playwright selectors for the elements requested.

### INPUT DATA
I will provide you with two things:
1. **The Source Code:** The raw code of the webpage or component.
2. **The Requirements List:** A list of specific UI elements (buttons, inputs, modals, etc.) that I need selectors for.

### SELECTOR STRATEGY (PRIORITY ORDER)
1. **IDs & Names:** `input[id="username"]`, `input[name="q"]`
2. **Placeholders (High Priority for Inputs):** `input[placeholder="Job title, skills"]`, `input[placeholder*="Location"]`
3. **Specific Attributes:** `input[type="email"]`, `button[type="submit"]`
4. **Text Content (Visible Only):** `button:has-text("Search")`
5. **Class combinations:** `input.search-bar` (Only if class looks stable, avoiding random hashes like `.css-1x2y`)

**CRITICAL RULE FOR INPUTS:** Always prefer `input[placeholder='...']` over complex nested paths like `div.container > form > div > input`.

### CRITICAL: FIND VISIBLE/CLICKABLE ELEMENTS ONLY

**MOST IMPORTANT RULE**: When looking for buttons/links (like "login", "register", "search"):
1. **FIRST** look for the VISIBLE link/button in the header, navigation, or main page content
2. **DO NOT** return selectors for elements inside hidden modals, drawers, popups, or overlays
3. **AVOID** selectors containing classes like `.drawer`, `.modal`, `.popup`, `.hidden`, `.overlay` unless explicitly asked

**Example - Login Button:**
- [OK] CORRECT: `a[title="Jobseeker Login"]` (visible link in header/nav)
- [OK] CORRECT: `.header a:has-text("Login")` (visible header link)  
- [OK] CORRECT: `nav a[href*="login"]` (navigation link)
- [ERROR] WRONG: `.modal form button.loginButton` (inside unopened modal)
- [ERROR] WRONG: `.drawer .login-layer .loginButton` (inside hidden drawer)
- [ERROR] WRONG: `.popup-content button` (inside popup overlay)

**How to distinguish visible vs hidden elements:**
- **Visible**: In `<header>`, `<nav>`, or top-level `<div>` with classes like `header`, `navbar`, `top-bar`, `main-content`
- **Hidden**: In `<div>` with classes like `modal`, `drawer`, `popup`, `overlay`, `dialog`, `hidden`
- **Rule**: If you see BOTH a header link AND a modal form, return the HEADER LINK

### SELECTOR STRATEGY (PRIORITY ORDER)
You MUST return CSS selectors that work with this Playwright code:
element = page.locator(selector)

CRITICAL: Return ONLY CSS selectors. DO NOT return:
- page.getByRole() syntax
- page.getByText() syntax
- page.getByLabel() syntax
- page.getByPlaceholder() syntax


### CONSTRAINTS
* **Ignore Dynamic Classes:** Do not rely on random or utility classes (e.g., Tailwind classes like `bg-red-500` or hashed classes like `css-1r2f3`) unless absolutely necessary.
* **Uniqueness:** Ensure the selector targets only the specific element requested.
* **Handling Missing Elements:** If a requested element does not exist in the code, explicitly state "Element not found in provided code."

### OUTPUT FORMAT
Provide the output in a Markdown table with the following columns:
1.  **Element Name:** The name of the requirement (e.g., "Login Button").
2.  **Playwright Selector:** The CSS selector ONLY (e.g., `button[type="submit"]` or `#login_button`).
3.  **Strategy Used:** Brief explanation (e.g., "Used type attribute selector").

After the table, provide a code block containing just the constant variables for these selectors, ready to copy-paste into a Page Object Model.

---

### USER INPUT START

**REQUIREMENTS LIST:**
{requirements}

**SOURCE CODE:**
{code}"""
    
    return prompt


def get_vision_analysis_prompt(
    requirements: str, 
    image_width: int = None, 
    image_height: int = None, 
    analysis_type: str = "element_detection"
) -> str:
    """
    Generate a vision analysis prompt for analyzing UI screenshots.
    
    Supports multiple analysis types for different automation scenarios.
    
    Args:
        requirements: Description of what to find/verify in the screenshot
        image_width: Screenshot width in pixels (optional)
        image_height: Screenshot height in pixels (optional)
        analysis_type: Type of analysis to perform
        
    Analysis Types:
        - "element_detection": Locate UI elements by description
        - "page_verification": Check if specific requirements are visible on page
        - "form_verification": Verify if form fields are filled
        - "filter_detection": Detect filter options on job listing pages
        - "hover_detection": Detect tooltips, help text, or validation messages
        - "modal_detection": Detect if modal/popup/dialog overlay is visible
        - "data_extraction": Extract structured data from screenshots
        
    Returns:
        Formatted prompt string for vision LLM
    """
    
    dimension_info = ""
    if image_width and image_height:
        dimension_info = f"\n### Screenshot Dimensions:\n- Width: {image_width} pixels\n- Height: {image_height} pixels\n"
    
    if analysis_type == "element_detection":
        prompt = f"""You are a vision model specialized in analyzing UI screenshots for web automation.

Your task is to locate ALL UI elements described by the user and return their clickable positions.

### Requirements:
1. Identify ALL elements from the screenshot based on the user's description
2. Find the CENTER POINT of each element where a click would be most effective
3. Return coordinates in BOTH normalized (0.0-1.0) and pixel formats
4. Return ONLY valid JSON. No explanation, no markdown formatting
{dimension_info}
### Elements to find:
{requirements}

### Return ONLY the JSON object. No markdown code blocks, no explanations.
"""
    
    elif analysis_type == "page_verification":
        prompt = f"""You are a vision model specialized in verifying page states for web automation.

Your task is to analyze the screenshot and answer specific questions about what is visible on the page.

### Requirements:
1. For EACH requirement in the list, answer "yes" if it's visible on the page, "no" if it's not
2. Describe what is actually visible on the page (list all major elements you can see)
3. Identify the page type (login page, job listing page, search form page, dashboard, etc.)
4. In case of login page, check if the user is logged in or not by checking for profile icon, dashboard, login button, signup button, etc.
4. Return ONLY valid JSON in this exact format:
{{
  "pageType": "description of page type",
  "requirements_met": {{
    "requirement1": "yes" or "no",
    "requirement2": "yes" or "no"
  }},
  "what_is_visible": ["list", "of", "major", "elements", "visible", "on", "page"],
  "summary": "brief description of current page state"
}}
{dimension_info}
### Requirements to check:
{requirements}

### Return ONLY the JSON object. No markdown code blocks, no explanations. Answer "yes" or "no" for each requirement.
"""
    
    elif analysis_type == "form_verification":
        prompt = f"""You are a vision model specialized in verifying form field states.

Your task is to check if form fields have been filled correctly.

### Requirements:
1. For EACH field mentioned, check if it's filled (has text/value visible)
2. Answer "yes" if field is filled, "no" if empty
3. Describe what is actually visible in each field
4. Return ONLY valid JSON in this exact format:
{{
  "fields_status": {{
    "field1": {{"filled": "yes" or "no", "value": "what is visible"}},
    "field2": {{"filled": "yes" or "no", "value": "what is visible"}}
  }},
  "all_fields_filled": "yes" or "no",
  "ready_for_submission": "yes" or "no",
  "what_is_visible": ["list", "of", "all", "form", "elements", "visible"]
}}
{dimension_info}
### Fields to verify:
{requirements}

### Return ONLY the JSON object. No markdown code blocks, no explanations.
"""
    
    elif analysis_type == "filter_detection":
        prompt = f"""You are a vision model specialized in detecting filter options on job listing pages.

Your task is to identify all available filters and their current states.

### Requirements:
1. For EACH requirement in the list, answer "yes" if it's visible on the page, "no" if it's not
2. Identify all filter categories visible (location, experience, salary, job type, etc.)
3. Detect filter input types (dropdown, checkbox, text input, slider)
4. Check current filter states (filled/empty, selected/not selected)
5. Return ONLY valid JSON in this exact format:
{{
  "requirements_met": {{
    "requirement1": "yes" or "no",
    "requirement2": "yes" or "no"
  }},
  "filters_found": [
    {{"name": "filter name", "type": "dropdown/text/checkbox", "state": "filled/empty/selected"}}
  ],
  "what_is_visible": ["list", "of", "all", "filter", "elements", "visible"],
  "summary": "brief description of available filters"
}}
{dimension_info}
### Requirements to check:
{requirements}

### Return ONLY the JSON object. No markdown code blocks, no explanations.
"""
    
    elif analysis_type == "hover_detection":
        prompt = f"""You are a vision model specialized in detecting tooltips, help text, and validation messages that appear on hover.

Your task is to analyze the screenshot and identify any visible tooltips or help information that may have appeared after hovering over elements.

### Requirements:
1. For EACH requirement in the list, check if there is visible help text or tooltip
2. Describe all tooltips, help text, hints, or validation messages visible on the page
3. Identify what each tooltip/help text is associated with (field name, button label, etc.)
4. Return ONLY valid JSON in this exact format:
{{
  "tooltips_found": true or false,
  "requirements_met": {{
    "requirement1": "yes" or "no" (tooltip/help text visible),
    "requirement2": "yes" or "no"
  }},
  "visible_tooltips": [
    {{"element": "field or button name", "tooltip_text": "the visible help/hint text", "type": "tooltip/hint/validation/description"}}
  ],
  "what_is_visible": ["list", "of", "all", "visible", "tooltips", "or", "help", "text"],
  "summary": "brief description of tooltips/help text currently visible"
}}
{dimension_info}
### Requirements to check for tooltips/help text:
{requirements}

### Return ONLY the JSON object. No markdown code blocks, no explanations.
"""
    
    elif analysis_type == "data_extraction":
        prompt = f"""You are a data extraction specialist.
Your task is to extract structured data from the provided screenshot.

### Requirements:
1. Extract ALL items visible in the screenshot that match this description: "{requirements}"
2. For each item, capture all visible details (e.g., Title, Company, Location, Salary, Link).
3. If an exact field is not visible, use "null".
4. Return ONLY valid JSON in this format:
{{
  "items": [
    {{ "title": "...", "company": "...", "location": "...", "other_details": "..." }},
    ...
  ],
  "item_count": number_of_items_found
}}
### mostly use ollama model
### Return ONLY the JSON object. No markdown code blocks, no explanations.
"""
    
    elif analysis_type == "modal_detection":
        prompt = f"""You are a vision model specialized in detecting modal dialogs, popups, and overlays that may be blocking user interactions.

Your task is to analyze the screenshot and determine if any modal, popup, or dialog overlay is visible on the page.

### Critical Analysis Points:
1. Look for semi-transparent overlay layers that cover the background
2. Identify modal content area and its boundaries
3. Find all interactive elements INSIDE the modal (buttons, inputs, etc.)
4. Identify the primary action button in the modal (e.g., "View Results", "Done", "Submit")
5. Look for close button/X icon in the modal
6. Read all text content visible in the modal
7. Return ONLY valid JSON in this exact format:
{{
  "modal_detected": true or false,
  "modal_type": "dialog/sidebar/popup/alert/none",
  "modal_title": "title or heading of the modal if present",
  "modal_visible_text": ["list", "of", "all", "text", "visible", "in", "modal"],
  "interactive_elements_in_modal": [
    {{"type": "button/input/dropdown", "label": "text on element", "location": "top/bottom/left/right/center"}}
  ],
  "primary_action_button": "text of main button (View Results, Done, Submit, etc.) or null",
  "close_button_visible": true or false,
  "what_is_visible": ["list", "of", "all", "modal", "elements", "visible"],
  "blocking_background": true or false,
  "summary": "brief description of the modal/popup - is it blocking the background? what is the main action?"
}}
{dimension_info}
### Requirements to check:
{requirements}

### Return ONLY the JSON object. No markdown code blocks, no explanations. Be precise about what interactive elements you see INSIDE the modal.
"""
    
    return prompt
