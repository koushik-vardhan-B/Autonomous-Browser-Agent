"""
Groq provider (Llama models) with multi-key rotation support.
"""

from langchain_groq import ChatGroq
from langchain_core.language_models import BaseChatModel
from ..base import BaseLLMProvider


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider (Llama 3.3 70B, Llama 3.2 Vision)."""
    
    def __init__(self, model: str = "llama-3.3-70b-versatile", temperature: float = 0.1):
        self.model = model
        self.temperature = temperature
    
    def get_model(self, api_key: str, **kwargs) -> BaseChatModel:
        """
        Initialize Groq model.
        
        Args:
            api_key: Groq API key
            **kwargs: Override model or temperature
            
        Returns:
            ChatGroq instance
        """
        return ChatGroq(
            api_key=api_key,
            model=kwargs.get("model", self.model),
            temperature=kwargs.get("temperature", self.temperature)
        )
    
    def get_provider_name(self) -> str:
        return "groq"
