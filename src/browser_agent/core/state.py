"""
LangGraph state definitions for the browser automation workflow.
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import MessagesState
import operator


class AgentState(TypedDict):
    """
    State shared across all agents in the LangGraph workflow.
    
    This state is passed between nodes and updated as the workflow progresses.
    """
    
    # User input and planning
    user_input: str
    """Original user request"""
    
    current_step_index: int
    """Index of the current step being executed (0-based)"""
    
    plan: List[Dict[str, Any]]
    """List of steps from the supervisor (each step is a dict with 'agent', 'query', etc.)"""
    
    # Execution context
    current_url: str
    """Current browser URL"""
    
    current_site_name: str
    """Current site name (for browser profile management)"""
    
    # Results and errors
    execution_results: Annotated[List[str], operator.add]
    """Accumulated results from execution steps (appended to, not replaced)"""
    
    errors: Annotated[List[str], operator.add]
    """Accumulated errors (appended to, not replaced)"""
    
    extracted_data: Optional[Dict[str, Any]]
    """Data extracted from the current page (scraping results)"""
    
    # LLM rotation state
    llm_rotation_index: int
    """Current index for LLM API key rotation (for rate limit handling)"""
    
    # RAG context
    rag_context: Optional[str]
    """Retrieved context from RAG agent (URLs, selectors, how-to guides)"""
    
    # Workflow control
    should_continue: bool
    """Whether to continue execution or stop"""
    
    final_output: Optional[str]
    """Final formatted output to return to user"""


class ExecutionAgentState(MessagesState):
    """
    State for the execution agent (extends LangChain's MessagesState for chat history).
    
    This allows the execution agent to maintain conversation context across tool calls.
    """
    
    current_instruction: str
    """The current step instruction being executed"""
    
    page_state: Optional[Dict[str, Any]]
    """Current page state (visible elements, accessibility tree, etc.)"""
    
    execution_result: Optional[str]
    """Result of the current execution step"""
    
    error: Optional[str]
    """Error message if execution failed"""
