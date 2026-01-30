"""
Core utilities, schemas, and state definitions for the browser agent.
"""

from .utils import (
    extract_json_from_markdown,
    save_json_to_file,
    load_json_from_file,
    parse_json_safe
)

from .schemas import (
    Attribute_Properties,
    build_attributes_model,
    Step,
    SupervisorOutput
)

from .state import (
    AgentState,
    ExecutionAgentState
)

__all__ = [
    # Utils
    "extract_json_from_markdown",
    "save_json_to_file",
    "load_json_from_file",
    "parse_json_safe",
    
    # Schemas
    "Attribute_Properties",
    "build_attributes_model",
    "Step",
    "SupervisorOutput",
    
    # State
    "AgentState",
    "ExecutionAgentState"
]
