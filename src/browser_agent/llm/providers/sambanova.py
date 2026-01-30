"""
SambaNova provider with multi-key rotation support.
"""

from langchain_sambanova import ChatSambaNova
from langchain_core.language_models import BaseChatModel
from ..base import BaseLLMProvider


class SambanovaProvider(BaseLLMProvider):
    """SambaNova LLM provider (GPT-OSS 120B)."""
    
    def __init__(self, model: str = "gpt-oss-120b", temperature: float = 0.1):
        self.model = model
        self.temperature = temperature
    
    def get_model(self, api_key: str, **kwargs) -> BaseChatModel:
        """
        Initialize SambaNova model.
        
        Args:
            api_key: SambaNova API key
            **kwargs: Override model or temperature
            
        Returns:
            ChatSambaNova instance
        """
        return ChatSambaNova(
            api_key=api_key,
            model=kwargs.get("model", self.model),
            temperature=kwargs.get("temperature", self.temperature)
        )
    
    def get_provider_name(self) -> str:
        return "sambanova"
