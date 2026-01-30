"""
Base LLM interface and shared utilities for all providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Any
from langchain_core.language_models import BaseChatModel


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def get_model(self, api_key: str, **kwargs) -> BaseChatModel:
        """
        Initialize and return an LLM instance.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Initialized LLM instance
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'gemini', 'groq')."""
        pass


class LLMRotationResult:
    """Container for LLM rotation results."""
    
    def __init__(self, model_name: str, llm: BaseChatModel):
        self.model_name = model_name
        self.llm = llm
    
    def __iter__(self):
        """Allow tuple unpacking: name, llm = result"""
        return iter((self.model_name, self.llm))
    
    def __repr__(self):
        return f"LLMRotationResult(model_name='{self.model_name}')"
