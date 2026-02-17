"""
Session state persistence for browser profiles and workflow state.
"""

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from .base import BaseMemory, MemoryConfig


class SessionStore(BaseMemory):
    """
    Persistent storage for browser sessions and workflow state.
    Stores session data as JSON files.
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize session store.
        
        Args:
            config: Memory configuration
        """
        super().__init__(config)
        self.session_dir = Path(self.config.persist_directory) / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """
        Store session data.
        
        Args:
            key: Session ID
            value: Session data (must be JSON-serializable)
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            session_file = self.session_dir / f"{key}.json"
            data = {
                "session_id": key,
                "data": value,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(session_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error storing session: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve session data.
        
        Args:
            key: Session ID
            
        Returns:
            Session data or None
        """
        try:
            session_file = self.session_dir / f"{key}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            return data.get("data")
        except Exception as e:
            print(f"Error retrieving session: {e}")
            return None
    
    def search(self, query: str, limit: int = 5) -> List[Any]:
        """
        Search sessions by metadata (simple substring match).
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching sessions
        """
        results = []
        try:
            for session_file in self.session_dir.glob("*.json"):
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                # Simple search in metadata
                if query.lower() in str(data.get("metadata", {})).lower():
                    results.append(data.get("data"))
                
                if len(results) >= limit:
                    break
            
            return results
        except Exception as e:
            print(f"Error searching sessions: {e}")
            return []
    
    def delete(self, key: str) -> bool:
        """
        Delete a session.
        
        Args:
            key: Session ID
            
        Returns:
            True if successful
        """
        try:
            session_file = self.session_dir / f"{key}.json"
            if session_file.exists():
                session_file.unlink()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all sessions.
        
        Returns:
            True if successful
        """
        try:
            for session_file in self.session_dir.glob("*.json"):
                session_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing sessions: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """
        List all session IDs.
        
        Returns:
            List of session IDs
        """
        return [f.stem for f in self.session_dir.glob("*.json")]
