"""
Execution tracing for debugging and monitoring workflows.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class TraceSpan:
    """
    Single span in execution trace.
    Represents one step/agent execution.
    """
    name: str
    start_time: float
    end_time: Optional[float] = None
    parent_id: Optional[str] = None
    span_id: str = field(default_factory=lambda: str(time.time_ns()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "span_id": self.span_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms(),
            "parent_id": self.parent_id,
            "metadata": self.metadata,
            "error": self.error
        }


class ExecutionTracer:
    """
    Traces workflow execution for debugging.
    Records agent calls, tool usage, and errors.
    """
    
    def __init__(self):
        """Initialize tracer."""
        self.spans: List[TraceSpan] = []
        self._active_spans: Dict[str, TraceSpan] = {}
    
    def start_span(self, name: str, parent_id: Optional[str] = None, **metadata) -> str:
        """
        Start a new trace span.
        
        Args:
            name: Span name (e.g., "planner", "executor")
            parent_id: Optional parent span ID
            **metadata: Additional metadata
            
        Returns:
            Span ID
        """
        span = TraceSpan(
            name=name,
            start_time=time.time(),
            parent_id=parent_id,
            metadata=metadata
        )
        self._active_spans[span.span_id] = span
        return span.span_id
    
    def end_span(self, span_id: str, error: Optional[str] = None):
        """
        End a trace span.
        
        Args:
            span_id: Span ID from start_span()
            error: Optional error message
        """
        if span_id in self._active_spans:
            span = self._active_spans.pop(span_id)
            span.end_time = time.time()
            span.error = error
            self.spans.append(span)
    
    def add_metadata(self, span_id: str, **metadata):
        """
        Add metadata to an active span.
        
        Args:
            span_id: Span ID
            **metadata: Metadata to add
        """
        if span_id in self._active_spans:
            self._active_spans[span_id].metadata.update(metadata)
    
    def get_trace(self) -> List[Dict[str, Any]]:
        """
        Get full trace as list of span dicts.
        
        Returns:
            List of span dictionaries
        """
        return [span.to_dict() for span in self.spans]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get trace summary.
        
        Returns:
            Summary with total duration, span count, errors
        """
        if not self.spans:
            return {"message": "No spans recorded"}
        
        total_duration = sum(span.duration_ms() for span in self.spans)
        errors = [span for span in self.spans if span.error]
        
        return {
            "total_spans": len(self.spans),
            "total_duration_ms": total_duration,
            "errors": len(errors),
            "error_spans": [{"name": s.name, "error": s.error} for s in errors],
            "timestamp": datetime.now().isoformat()
        }
    
    def export_json(self, filepath: str):
        """
        Export trace to JSON file.
        
        Args:
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump({
                "trace": self.get_trace(),
                "summary": self.get_summary()
            }, f, indent=2)
    
    def reset(self):
        """Clear all spans."""
        self.spans.clear()
        self._active_spans.clear()


# Global tracer instance
_global_tracer: Optional[ExecutionTracer] = None


def get_tracer() -> ExecutionTracer:
    """
    Get or create global execution tracer.
    
    Returns:
        ExecutionTracer instance
    """
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = ExecutionTracer()
    return _global_tracer
