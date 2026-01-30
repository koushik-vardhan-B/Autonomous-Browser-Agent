"""
Core utility functions for the browser agent.
"""

import re
import json
from typing import List, Dict, Any
from langchain_core.tools import tool


def extract_json_from_markdown(text: str) -> str:
    """
    Extract JSON from markdown code blocks like ```json ... ```
    
    Args:
        text: Text potentially containing JSON in markdown code blocks
        
    Returns:
        Extracted JSON string or original text if no code blocks found
    """
    # Try to find JSON in markdown code blocks
    pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # If no markdown blocks found, return the original text
    return text.strip()


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
