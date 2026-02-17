"""
RAG (Retrieval-Augmented Generation) agent for storing and retrieving error solutions.
"""

from langchain_core.messages import ChatMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langgraph.types import Command


# Lazy loading to avoid startup overhead
_vector_db_instance = None


def get_vector_db():
    """
    Lazy load the vector database only when needed.
    This eliminates the startup delay from loading HuggingFaceEmbeddings and Chroma.
    """
    global _vector_db_instance
    
    if _vector_db_instance is None:
        try:
            print(">>> Initializing vector database (first use only)...")
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            _vector_db_instance = Chroma(
                persist_directory="./rag_data", 
                embedding_function=embeddings,
                collection_name="agent_memories"
            )
            print(">>> Vector database initialized successfully.")
        except Exception as e:
            print(f"Error loading vector database: {str(e)}")
            _vector_db_instance = None
    
    return _vector_db_instance


def rag(state):
    """
    RAG agent that stores error messages and solutions in a vector database.
    
    Saves execution context (URL, site, task, agent) along with error/solution
    for future retrieval and learning.
    """
    print(">>> RAG WORKING")
    rag_content = state["rag_messages"][-1]
    if hasattr(rag_content, 'content'): 
        rag_content = rag_content.content
    else:
        rag_content = str(rag_content)
    
    # Import here to avoid circular dependency
    from .planner import get_current_browser_info
    url, site_name = get_current_browser_info()
    
    plan = state.get("plan", [])
    index = state.get("step_index", 0)
    
    if index < len(plan):
        task = plan[index]['query']
        agent = plan[index]['agent']
    else:
        task = "Unknown"
        agent = "Unknown"

    doc = Document(
        page_content=str(rag_content),  
        metadata={
            "url": url,
            "site_name": site_name,
            "task": task,
            "agent": agent
        }
    )
    
    vector_db = get_vector_db()
    if vector_db:
        vector_db.add_documents([doc])
    
    return Command(
        update={"messages": [ChatMessage(role="RAG Agent", content=f"Memory Saved: '{rag_content[:50]}...'")]},
        goto="redirector"
    )


def retrieve_errors(state):
    """
    Retrieve past errors and solutions for the current sites from the vector database.
    
    Args:
        state: Current agent state containing site_names
        
    Returns:
        String containing formatted past errors and solutions
    """
    current_sites = state.get("site_names", [])
    if not current_sites:
        return "No specific sites identified yet."

    vector_db = get_vector_db()
    if not vector_db:
        return "Vector database not available."

    combined_errors = "PAST ERRORS/LESSONS:\n"
    found_any = False

    for site in current_sites:
        try:
            results = vector_db.similarity_search(
                query="error failure issue fix", 
                k=3, 
                filter={"site_name": site} 
            )
            if results:
                found_any = True
                combined_errors += f"\n--- For {site} ---\n"
                for i, doc in enumerate(results):
                    prev_task = doc.metadata.get('task', 'General Task')
                    combined_errors += f"{i+1}. [Task: {prev_task}]: {doc.page_content}\n"
        except Exception as e:
            print(f"Error retrieving for {site}: {e}")

    if not found_any:
        return "No previous errors found for these sites."
            
    return combined_errors
