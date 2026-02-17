"""
Browser lifecycle and helper tools for analysis.
"""

from langchain_core.tools import tool
from ..manager import browser_manager


@tool
def ask_human_help(message: str):
    """
    Pauses the automation and asks the human for help. 
    Use this if you see a CAPTCHA, Cloudflare block, or if you are stuck.
    
    Args:
        message: Description of what help is needed
        
    Returns:
        Confirmation message after human intervention
    """
    print(f"\n\n!!! AGENT NEEDS HELP: {message} !!!")
    print("Perform the necessary action in the browser (e.g., solve captcha).")
    input("Press ENTER here when you are done to continue...")
    return "Human help received. Proceeding."


@tool
def open_browser(url: str, sitename: str):
    """
    Open a browser and navigate to the specified URL.
    
    Args:
        url: URL to navigate to
        sitename: Site name for browser profile management
        
    Returns:
        Success/error message
    """
    return browser_manager.start_browser(url, sitename)


@tool
def close_browser():
    """
    Close the browser and cleanup resources.
    
    Returns:
        Success/error message
    """
    return browser_manager.close_browser()


def extract_html_code():
    """
    Extracts the HTML code from the current page and saves a screenshot.
    
    Returns:
        HTML content as string, or None on error
    """
    try:
        page = browser_manager.get_page()
        page.wait_for_load_state("load", timeout=60000)
        if not page:
            return "Error: No browser page is open"
        
        html_code = page.content()
        screenshot_path = "screenshot.png"
        page.screenshot(path=screenshot_path)
        return html_code
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def extract_page_content_as_markdown() -> str:
    """
    Extracts the page content as clean Markdown.
    
    Uses JavaScript to traverse the DOM and convert visible elements to Markdown format.
    Skips hidden elements, scripts, styles, and SVGs.
    
    Returns:
        Markdown-formatted page content (truncated to 40,000 chars)
    """
    page = browser_manager.get_page()
    if not page:
        return "Error: No page open"

    try:
        markdown = page.evaluate("""
            () => {
                function isVisible(el) {
                    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
                }

                function cleanText(text) {
                    return text.replace(/\\s+/g, ' ').trim();
                }

                function traverse(node) {
                    let text = "";
                    
                    // Handle Text Nodes
                    if (node.nodeType === 3) {
                        return cleanText(node.textContent);
                    }
                    
                    // Handle Elements
                    if (node.nodeType === 1) {
                        if (!isVisible(node)) return "";
                        
                        const tag = node.tagName.toLowerCase();
                        
                        // Skip script/style/noscript
                        if (['script', 'style', 'noscript', 'svg', 'path', 'head', 'meta'].includes(tag)) {
                            return "";
                        }

                        // Process children first
                        let childrenText = "";
                        node.childNodes.forEach(child => {
                            childrenText += traverse(child) + " ";
                        });
                        childrenText = childrenText.replace(/\\s+/g, ' ').trim();

                        if (!childrenText && !['img', 'input', 'br', 'hr'].includes(tag)) return "";

                        // Format based on Tag
                        if (tag === 'a') {
                            const href = node.getAttribute('href');
                            return href ? ` [${childrenText}](${href}) ` : childrenText;
                        }
                        if (tag === 'img') {
                            const alt = node.getAttribute('alt') || 'Image';
                            return ` ![${alt}] `;
                        }
                        if (['h1', 'h2', 'h3'].includes(tag)) {
                            return `\\n\\n# ${childrenText}\\n\\n`;
                        }
                        if (['h4', 'h5', 'h6'].includes(tag)) {
                            return `\\n\\n## ${childrenText}\\n\\n`;
                        }
                        if (tag === 'li') {
                            return `\\n- ${childrenText}`;
                        }
                        if (tag === 'p' || tag === 'div') {
                            return `\\n${childrenText}\\n`;
                        }
                        if (tag === 'button') {
                            return ` [Button: ${childrenText}] `;
                        }
                        if (tag === 'input') {
                            const val = node.value || node.getAttribute('placeholder') || '';
                            return ` [Input: ${val}] `;
                        }
                        
                        return childrenText + " ";
                    }
                    return "";
                }

                return traverse(document.body);
            }
        """)
        
        # Truncate to 40,000 chars to avoid token limits
        return markdown[:40000]

    except Exception as e:
        return f"Error extracting markdown: {e}"
