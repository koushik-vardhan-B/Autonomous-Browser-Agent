"""
Pydantic schemas for browser agent state and outputs.
"""

from typing import Dict, Iterable, List, Tuple, Any, Optional, Literal
from pydantic import BaseModel, Field, create_model


class Attribute_Properties(BaseModel):
    """Properties of a UI element for selector extraction."""
    
    element_name: str = Field(
        ..., 
        description="The name of the requirement (e.g., 'Login Button')."
    )
    playwright_selector: str = Field(
        ..., 
        description="The CSS selector or Playwright locator (e.g., 'button[type=\"submit\"]')."
    )
    strategy_used: str = Field(
        ..., 
        description="Brief explanation (e.g., 'Used type attribute selector')."
    )


def build_attributes_model(
    model_name: str,
    field_names: Iterable[str],
    *,
    required: bool = True,
    default_for_optional: Any = None
) -> type[BaseModel]:
    """
    Dynamically build a Pydantic model where each field has type Attribute_Properties.
    
    This is used for structured output from LLMs when extracting selectors for multiple elements.
    
    Args:
        model_name: Name for the generated Pydantic model class
        field_names: Iterable of field names (e.g., ["login_button", "search_input"])
        required: If True, each field is required; if False, fields are optional
        default_for_optional: Default value when required=False
        
    Returns:
        A dynamically created Pydantic model class
        
    Example:
        >>> model = build_attributes_model("LoginElements", ["login_button", "password_field"])
        >>> # LLM will return: {"login_button": {...}, "password_field": {...}}
    """
    fields: Dict[str, Tuple[type, Any]] = {}
    default_value = ... if required else default_for_optional

    for fname in field_names:
        fields[fname] = (Attribute_Properties, default_value)
    
    DynamicModel = create_model(model_name, **fields)  # type: ignore
    return DynamicModel


class Step(BaseModel):
    """A single step in the supervisor's execution plan."""
    
    step_number: int = Field(
        description="Sequential number of this step (0-indexed)"
    )
    agent: Literal["RAG", "EXECUTION", "OUTPUT_FORMATTING", "PLANNER", "end"] = Field(
        description=(
            "Agent to execute this step:\n"
            "- 'RAG': Retrieve information (URLs, selectors, how-to guides)\n"
            "- 'EXECUTION': Perform browser actions (navigate, click, type, scrape)\n"
            "- 'OUTPUT_FORMATTING': Format extracted data into JSON/CSV\n"
            "- 'PLANNER': Re-plan based on new data (multi-phase workflows)\n"
            "- 'end': Task complete or impossible"
        )
    )
    query: str = Field(
        description=(
            "The instruction for the specified agent. "
            "For 'OUTPUT_FORMATTING', specify the desired format. "
            "For 'end', provide the final user-facing message."
        )
    )
    content: Optional[str] = Field(
        default=None,
        description="Content for OUTPUT_FORMATTING agent to format, or final output for 'end' agent"
    )
    rag_message: Optional[str] = Field(
        default=None,
        description="Error description and solution to store in RAG for future learning"
    )


class SupervisorOutput(BaseModel):
    """Output schema for the central planning agent (supervisor)."""
    
    target_urls: List[str] = Field(
        default_factory=list,
        description=(
            "List of all target URLs identified for this task "
            "(e.g., ['https://www.expedia.com', 'https://www.google.com/flights'])"
        )
    )
    site_names: List[str] = Field(
        default_factory=list,
        description=(
            "List of corresponding site names/domains "
            "(e.g., ['expedia', 'google']). Must match length of target_urls."
        )
    )
    steps: List[Step] = Field(
        description="Ordered list of steps to execute, each with an agent and instruction"
    )
