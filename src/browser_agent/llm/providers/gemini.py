"""
Google Gemini provider with multi-key rotation support.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from ..base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, model: str = "gemini-2.0-flash", temperature: float = 0.1):
        self.model = model
        self.temperature = temperature
    
    def get_model(self, api_key: str, **kwargs) -> BaseChatModel:
        """
        Initialize Gemini model.
        
        Args:
            api_key: Google API key
            **kwargs: Override model or temperature
            
        Returns:
            ChatGoogleGenerativeAI instance
        """
        return ChatGoogleGenerativeAI(
            model=kwargs.get("model", self.model),
            google_api_key=api_key,
            temperature=kwargs.get("temperature", self.temperature)
        )
    
    def get_provider_name(self) -> str:
        return "gemini"
