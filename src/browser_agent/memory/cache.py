"""
LLM response caching to reduce API calls and cost.
"""

import json
import hashlib
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base import BaseMemory, MemoryConfig


class LLMCache(BaseMemory):
    """
    Cache for LLM responses.
    Uses file-based storage with hash-based keys.
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None, ttl_seconds: int = 3600):
        """
        Initialize LLM cache.
        
        Args:
            config: Memory configuration
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
        """
        super().__init__(config)
        self.cache_dir = Path(self.config.persist_directory) / "llm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """
        Store LLM response in cache.
        
        Args:
            key: Prompt or request identifier
            value: LLM response
            metadata: Optional metadata (model name, tokens, etc.)
            
        Returns:
            True if successful
        """
        try:
            hash_key = self._hash_key(key)
            cache_file = self.cache_dir / f"{hash_key}.json"
            
            data = {
                "key": key,
                "value": value,
                "metadata": metadata or {},
                "timestamp": time.time(),
                "ttl": self.ttl
            }
            
            with open(cache_file,'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error storing in cache: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve cached LLM response.
        
        Args:
            key: Prompt or request identifier
            
        Returns:
            Cached response or None if expired/not found
        """
        try:
            hash_key = self._hash_key(key)
            cache_file = self.cache_dir / f"{hash_key}.json"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Check TTL
            age = time.time() - data.get("timestamp", 0)
            if age > data.get("ttl", self.ttl):
                # Expired - delete
                cache_file.unlink()
                return None
            
            return data.get("value")
        except Exception as e:
            print(f"Error retrieving from cache: {e}")
            return None
    
    def search(self, query: str, limit: int = 5) -> List[Any]:
        """
        Search cache (not implemented for LLM cache).
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            Empty list (search not supported)
        """
        return []
    
    def delete(self, key: str) -> bool:
        """
        Delete a cache entry.
        
        Args:
            key: Prompt or request identifier
            
        Returns:
            True if successful
        """
        try:
            hash_key = self._hash_key(key)
            cache_file = self.cache_dir / f"{hash_key}.json"
            if cache_file.exists():
                cache_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting from cache: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful
        """
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def clear_expired(self) -> int:
        """
        Clear expired cache entries.
        
        Returns:
            Number of entries cleared
        """
        cleared = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                age = time.time() - data.get("timestamp", 0)
                if age > data.get("ttl", self.ttl):
                    cache_file.unlink()
                    cleared += 1
            
            return cleared
        except Exception as e:
            print(f"Error clearing expired cache: {e}")
            return cleared
