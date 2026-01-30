"""
LLM router with intelligent fallback and rate limit handling.
Replaces the original LLMConfig class with modular provider system.
"""

import os
from typing import List, Tuple, Optional
from langchain_core.language_models import BaseChatModel

from .providers import GeminiProvider, GroqProvider, SambanovaProvider, OllamaProvider
from .rate_limiter import api_key_rotator


class LLMRouter:
    """
    Intelligent LLM router with multi-provider fallback.
    Handles API key rotation and rate limit resilience.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMRouter, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.gemini_provider = GeminiProvider()
            self.groq_provider = GroqProvider()
            self.sambanova_provider = SambanovaProvider()
            self.ollama_provider = OllamaProvider()
            self._initialized = True
    
    def get_main_llm_with_rotation(
        self, 
        start_index: int = 0, 
        provider: Optional[str] = None
    ) -> List[Tuple[str, BaseChatModel]]:
        """
        Get LLM instances with rotation for text/reasoning tasks.
        
        Args:
            start_index: Starting index for rotation (from state)
            provider: Optional provider filter ("gemini", "groq", "sambanova", "ollama", or None for all)
            
        Returns:
            List of (model_name, llm_instance) tuples to try in order
        """
        rotation_list = []
        
        # Add Gemini keys (if no provider specified or provider="gemini")
        if provider is None or provider == "gemini":
            gemini_keys = api_key_rotator.get_gemini_keys()
            for idx, key in enumerate(gemini_keys, start=1):
                try:
                    llm = self.gemini_provider.get_model(api_key=key)
                    rotation_list.append((f"gemini_llm{idx}", llm))
                except Exception as e:
                    print(f"❌ Failed to initialize gemini_llm{idx}: {e}")
        
        # Add Groq keys (if no provider specified or provider="groq")
        if provider is None or provider == "groq":
            groq_keys = api_key_rotator.get_groq_keys()
            for idx, key in enumerate(groq_keys, start=1):
                try:
                    llm = self.groq_provider.get_model(api_key=key)
                    rotation_list.append((f"groq_llm{idx}", llm))
                except Exception as e:
                    print(f"❌ Failed to initialize groq_llm{idx}: {e}")
        
        # Add SambaNova keys (if provider="sambanova")
        if provider == "sambanova":
            sambanova_keys = api_key_rotator.get_sambanova_keys()
            for idx, key in enumerate(sambanova_keys, start=1):
                try:
                    llm = self.sambanova_provider.get_model(api_key=key)
                    rotation_list.append((f"sambanova{idx}", llm))
                except Exception as e:
                    print(f"❌ Failed to initialize sambanova{idx}: {e}")
        
        # Add Ollama (if provider="ollama")
        if provider == "ollama":
            if OllamaProvider.check_availability():
                try:
                    llm = self.ollama_provider.get_model()
                    rotation_list.append(("ollama_text", llm))
                except Exception as e:
                    print(f"❌ Failed to initialize Ollama text: {e}")
        
        if not rotation_list:
            provider_msg = f" for provider '{provider}'" if provider else ""
            raise ValueError(f"No valid API keys found for main LLM rotation{provider_msg}")
        
        # Rotate based on start_index
        if start_index > 0:
            rotation_list = rotation_list[start_index:] + rotation_list[:start_index]
        
        return rotation_list
    
    def get_vision_llm_with_rotation(
        self, 
        start_index: int = 0
    ) -> List[Tuple[str, BaseChatModel]]:
        """
        Get vision LLM instances with rotation.
        Priority: Ollama (if available) -> Groq rotation
        
        Args:
            start_index: Starting index for Groq rotation (from state)
            
        Returns:
            List of (model_name, llm_instance) tuples to try in order
        """
        rotation_list = []
        
        # Check Ollama first (local, no rate limits)
        if OllamaProvider.check_availability():
            try:
                llm = self.ollama_provider.get_model(model="llama3.2-vision:11b")
                rotation_list.append(("ollama_vision", llm))
                print(">>> ✅ Added Ollama to vision rotation (priority)")
            except Exception as e:
                print(f"❌ Failed to initialize Ollama vision: {e}")
        
        # Add Groq vision keys as fallback
        groq_keys = api_key_rotator.get_groq_keys()
        for idx, key in enumerate(groq_keys, start=1):
            try:
                llm = self.groq_provider.get_model(
                    api_key=key,
                    model="llama-3.2-90b-vision-preview"
                )
                rotation_list.append((f"groq_llm{idx}_vision", llm))
            except Exception as e:
                print(f"❌ Failed to initialize groq_llm{idx} vision: {e}")
        
        if not rotation_list:
            raise ValueError("No valid vision LLM available (Ollama or Groq)")
        
        # Rotate based on start_index (only affects Groq keys if Ollama failed)
        if start_index > 0 and len(rotation_list) > 1:
            rotation_list = rotation_list[start_index:] + rotation_list[:start_index]
        
        return rotation_list
    
    def get_main_llm(self) -> BaseChatModel:
        """
        Legacy method: Returns the first Gemini LLM (no rotation).
        For backward compatibility only.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: No Google API Key found (checked 'GOOGLE_API_KEY'). Please set it in .env")
        return self.gemini_provider.get_model(api_key=api_key)
    
    def get_vision_llm(self) -> BaseChatModel:
        """
        Legacy method: Returns Ollama or Groq vision LLM (no rotation).
        For backward compatibility only.
        """
        if OllamaProvider.check_availability():
            print(">>> Using Local Ollama for Vision.")
            return self.ollama_provider.get_model(model="llama3.2-vision:11b")
        else:
            print(">>> Ollama not available. Falling back to Groq for Vision.")
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("CRITICAL: No Groq API Key found (checked 'GROQ_API_KEY'). Please set it in .env")
            return self.groq_provider.get_model(
                api_key=api_key,
                model="llama-3.2-90b-vision-preview"
            )


# Global singleton instance (backward compatibility with original LLMConfig)
LLMConfig = LLMRouter()


def validate_config():
    """Validate LLM configuration on startup."""
    print("--- Validating LLM Configuration ---")
    try:
        LLMConfig.get_main_llm()
        print("✅ Main LLM (Gemini) Configured")
    except Exception as e:
        print(f"❌ Main LLM Config Error: {e}")

    # Check Vision
    is_ollama = OllamaProvider.check_availability()
    if not is_ollama:
        print("⚠️  Ollama not available. Checking Groq fallback...")
        try:
            LLMConfig.get_vision_llm()
            print("✅ Vision Fallback (Groq) Configured")
        except Exception as e:
            print(f"❌ Vision Config Error: {e}")
    else:
        print("✅ Vision LLM (Ollama) Configured")
    print("------------------------------------")


if __name__ == "__main__":
    validate_config()
