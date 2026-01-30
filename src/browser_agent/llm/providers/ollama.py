"""
Ollama local provider with availability checking.
"""

import requests
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel
from ..base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""
    
    _availability_checked = False
    _is_available = False
    
    def __init__(self, model: str = "llama3.2", temperature: float = 0.1, base_url: str = "http://localhost:11434"):
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
    
    @classmethod
    def check_availability(cls, base_url: str = "http://localhost:11434", timeout: int = 2) -> bool:
        """
        Check if Ollama is running locally.
        
        Args:
            base_url: Ollama server URL
            timeout: Connection timeout in seconds
            
        Returns:
            True if Ollama is available, False otherwise
        """
        if cls._availability_checked:
            return cls._is_available
        
        try:
            response = requests.get(base_url, timeout=timeout)
            if response.status_code == 200:
                print(">>> ✅ Ollama detected and running.")
                cls._is_available = True
            else:
                print(f">>> ⚠️ Ollama returned unexpected status: {response.status_code}")
                cls._is_available = False
        except requests.exceptions.ConnectionError:
            print(">>> ❌ Ollama not detected (ConnectionError).")
            cls._is_available = False
        except Exception as e:
            print(f">>> ❌ Error checking Ollama: {e}")
            cls._is_available = False
        
        cls._availability_checked = True
        return cls._is_available
    
    def get_model(self, api_key: str = None, **kwargs) -> BaseChatModel:
        """
        Initialize Ollama model (no API key needed).
        
        Args:
            api_key: Ignored (Ollama is local)
            **kwargs: Override model or temperature
            
        Returns:
            ChatOllama instance
        """
        return ChatOllama(
            model=kwargs.get("model", self.model),
            temperature=kwargs.get("temperature", self.temperature)
        )
    
    def get_provider_name(self) -> str:
        return "ollama"
