"""
Core utility functions for the browser agent.
"""

import re
import json
from typing import List, Dict, Any
from langchain_core.tools import tool


def extract_json_from_markdown(text) -> str:
    """
    Extract JSON from markdown code blocks or raw text, handling trailing data.
    
    Args:
        text: Text potentially containing JSON in markdown code blocks
        
    Returns:
        Extracted JSON string or original text if no code blocks found
    """
    if not text:
        return "{}"
    text = str(text).strip()

    # 1. Try markdown code block: ```json ... ```
    md_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if md_match:
        candidate = md_match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except (json.JSONDecodeError, ValueError):
            pass

    # 2. Try parsing the full text as-is
    try:
        json.loads(text)
        return text
    except (json.JSONDecodeError, ValueError):
        pass

    # 3. Extract the first complete JSON object {...} using brace matching
    start = text.find('{')
    if start != -1:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except (json.JSONDecodeError, ValueError):
                        break

    # 4. Fallback
    return text


@tool
def save_json_to_file(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Save a list of dictionaries to a JSON file.
    
    Args:
        data: List of dictionaries to save
        filename: Name of the file to save to
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_json_from_file(filename: str) -> List[Dict[str, Any]]:
    """
    Load JSON data from a file.
    
    Args:
        filename: Name of the file to load from
        
    Returns:
        List of dictionaries loaded from the file
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_json_safe(text: str) -> Dict[str, Any] | None:
    """
    Safely parse JSON string, returning None on failure.
    
    Args:
        text: JSON string to parse
        
    Returns:
        Parsed dictionary or None if parsing fails
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
