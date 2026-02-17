"""
Custom exceptions for the browser agent.
"""


class BrowserAgentError(Exception):
    """Base exception for all browser agent errors."""
    pass


class BrowserNotOpenError(BrowserAgentError):
    """Raised when browser operation is attempted but browser is not open."""
    pass


class ElementNotFoundError(BrowserAgentError):
    """Raised when a UI element cannot be found on the page."""
    pass


class NavigationError(BrowserAgentError):
    """Raised when navigation to a URL fails."""
    pass


class ExtractionError(BrowserAgentError):
    """Raised when data extraction from a page fails."""
    pass


class LLMError(BrowserAgentError):
    """Raised when LLM API call fails (non-rate-limit)."""
    pass


class RateLimitError(LLMError):
    """Raised when API rate limit is hit."""
    def __init__(self, provider: str, message: str = "Rate limit exceeded"):
        self.provider = provider
        super().__init__(f"{provider}: {message}")


class AllKeysExhaustedError(LLMError):
    """Raised when all API keys have been exhausted due to rate limits."""
    pass


class PlanningError(BrowserAgentError):
    """Raised when the planning agent fails to generate a valid plan."""
    pass


class ExecutionError(BrowserAgentError):
    """Raised when the execution agent fails to complete a step."""
    pass


class ValidationError(BrowserAgentError):
    """Raised when result validation fails."""
    pass


class RAGError(BrowserAgentError):
    """Raised when RAG operations (store/retrieve) fail."""
    pass


class StateError(BrowserAgentError):
    """Raised when there's an issue with the agent state."""
    pass
