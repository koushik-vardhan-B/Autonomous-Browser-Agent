"""
Base memory interfaces and configuration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MemoryConfig:
    """Configuration for memory systems."""
    persist_directory: str = "./data"
    collection_name: str = "agent_memory"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_history_length: int = 100


class BaseMemory(ABC):
    """Abstract base class for memory systems."""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize memory system.
        
        Args:
            config: Memory configuration
        """
        self.config = config or MemoryConfig()
    
    @abstractmethod
    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """
        Store a value with optional metadata.
        
        Args:
            key: Storage key
            value: Value to store
            metadata: Optional metadata dict
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.
        
        Args:
            key: Storage key
            
        Returns:
            Retrieved value or None
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Any]:
        """
        Search for similar items.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching items
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value.
        
        Args:
            key: Storage key
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all stored data.
        
        Returns:
            True if successful
        """
        pass
