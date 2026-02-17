"""
Vector store memory using ChromaDB for RAG.
Currently implemented directly in orchestration.py via get_vector_db().
This module provides a cleaner interface for future refactoring.
"""

from typing import List, Optional, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from .base import BaseMemory, MemoryConfig


class VectorStoreMemory(BaseMemory):
    """
    Vector store for semantic search and RAG.
    Wraps ChromaDB with HuggingFace embeddings.
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize vector store.
        
        Args:
            config: Memory configuration
        """
        super().__init__(config)
        self._vector_db = None
    
    def _get_db(self):
        """Lazy load vector database."""
        if self._vector_db is None:
            print(">>> Initializing ChromaDB vector store...")
            embeddings = HuggingFaceEmbeddings(model_name=self.config.embedding_model)
            self._vector_db = Chroma(
                persist_directory=self.config.persist_directory,
                embedding_function=embeddings,
                collection_name=self.config.collection_name
            )
        return self._vector_db
    
    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """
        Store a document in vector store.
        
        Args:
            key: Document ID (used as page_content if value is string)
            value: Document content
            metadata: Document metadata
            
        Returns:
            True if successful
        """
        try:
            db = self._get_db()
            doc = Document(
                page_content=str(value),
                metadata=metadata or {"id": key}
            )
            db.add_documents([doc])
            return True
        except Exception as e:
            print(f"Error storing in vector DB: {e}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve by exact metadata match.
        
        Args:
            key: Document ID
            
        Returns:
            Document content or None
        """
        try:
            results = self.search(query=key, limit=1)
            return results[0] if results else None
        except Exception as e:
            print(f"Error retrieving from vector DB: {e}")
            return None
    
    def search(self, query: str, limit: int = 5, filter_metadata: Optional[Dict] = None) -> List[Document]:
        """
        Semantic search for similar documents.
        
        Args:
            query: Search query
            limit: Maximum results
            filter_metadata: Optional metadata filter
            
        Returns:
            List of matching documents
        """
        try:
            db = self._get_db()
            if filter_metadata:
                results = db.similarity_search(query, k=limit, filter=filter_metadata)
            else:
                results = db.similarity_search(query, k=limit)
            return results
        except Exception as e:
            print(f"Error searching vector DB: {e}")
            return []
    
    def delete(self, key: str) -> bool:
        """
        Delete a document.
        
        Args:
            key: Document ID
            
        Returns:
            True if successful
        """
        try:
            db = self._get_db()
            db.delete(ids=[key])
            return True
        except Exception as e:
            print(f"Error deleting from vector DB: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all documents.
        
        Returns:
            True if successful
        """
        try:
            if self._vector_db:
                self._vector_db = None
            return True
        except Exception as e:
            print(f"Error clearing vector DB: {e}")
            return False
