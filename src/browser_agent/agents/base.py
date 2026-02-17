"""
Base agent interface and shared utilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    Provides common interface for agent execution.
    """
    
    def __init__(self, name: str):
        """
        Initialize base agent.
        
        Args:
            name: Agent identifier for logging
        """
        self.name = name
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's task.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dict
        """
        pass
    
    def validate_state(self, state: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate that state contains required keys.
        
        Args:
            state: State dictionary to validate
            required_keys: List of required key names
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        missing = [key for key in required_keys if key not in state]
        if missing:
            raise ValueError(f"{self.name}: Missing required state keys: {missing}")
        return True
    
    def log(self, message: str, level: str = "INFO"):
        """
        Log a message with agent name prefix.
        
        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        print(f"[{level}] [{self.name}] {message}")


class AgentResult:
    """
    Standardized result container for agent execution.
    """
    
    def __init__(
        self,
        success: bool,
        data: Optional[Any] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent result.
        
        Args:
            success: Whether execution succeeded
            data: Result data if successful
            error: Error message if failed
            metadata: Additional metadata
        """
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }
    
    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"AgentResult({status}, error={self.error})"
