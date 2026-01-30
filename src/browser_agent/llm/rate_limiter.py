"""
API key rotation and rate limit handling.
"""

import os
from typing import List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()


class APIKeyRotator:
    """Manages API key rotation for rate limit resilience."""
    
    def __init__(self):
        self._gemini_keys: List[str] = []
        self._groq_keys: List[str] = []
        self._sambanova_keys: List[str] = []
        self._load_keys()
    
    def _load_keys(self):
        """Load all API keys from environment variables."""
        # Load Gemini keys (GOOGLE_API_KEY1 to GOOGLE_API_KEY16)
        for i in range(1, 17):
            key = os.getenv(f"GOOGLE_API_KEY{i}")
            if key:
                self._gemini_keys.append(key)
        
        # Load Groq keys (GROQ_API_KEY1 to GROQ_API_KEY5)
        for i in range(1, 6):
            key = os.getenv(f"GROQ_API_KEY{i}")
            if key:
                self._groq_keys.append(key)
        
        # Load SambaNova keys (SAMBANOVA_API_KEY1 to SAMBANOVA_API_KEY3)
        for i in range(1, 4):
            key = os.getenv(f"SAMBANOVA_API_KEY{i}")
            if key:
                self._sambanova_keys.append(key)
        
        print(f">>> 🔑 Loaded API Keys: Gemini={len(self._gemini_keys)}, Groq={len(self._groq_keys)}, SambaNova={len(self._sambanova_keys)}")
    
    def get_gemini_keys(self) -> List[str]:
        """Return all Gemini API keys."""
        return self._gemini_keys.copy()
    
    def get_groq_keys(self) -> List[str]:
        """Return all Groq API keys."""
        return self._groq_keys.copy()
    
    def get_sambanova_keys(self) -> List[str]:
        """Return all SambaNova API keys."""
        return self._sambanova_keys.copy()
    
    def get_keys_for_provider(self, provider: str) -> List[str]:
        """
        Get all keys for a specific provider.
        
        Args:
            provider: Provider name ('gemini', 'groq', 'sambanova')
            
        Returns:
            List of API keys for that provider
        """
        if provider == "gemini":
            return self.get_gemini_keys()
        elif provider == "groq":
            return self.get_groq_keys()
        elif provider == "sambanova":
            return self.get_sambanova_keys()
        else:
            return []
    
    def rotate_keys(self, keys: List[str], start_index: int = 0) -> List[str]:
        """
        Rotate keys starting from a specific index.
        
        Args:
            keys: List of API keys
            start_index: Starting index for rotation
            
        Returns:
            Rotated list of keys
        """
        if not keys or start_index == 0:
            return keys
        
        return keys[start_index:] + keys[:start_index]


# Global singleton instance
api_key_rotator = APIKeyRotator()
