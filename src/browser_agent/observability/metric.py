"""
Performance metrics collection.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Metric:
    """Single metric data point."""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and aggregates performance metrics.
    Tracks agent execution times, API calls, errors, etc.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: List[Metric] = []
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, float] = {}
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for grouping
        """
        metric = Metric(name=name, value=value, tags=tags or {})
        self.metrics.append(metric)
    
    def increment(self, counter_name: str, amount: int = 1):
        """
        Increment a counter.
        
        Args:
            counter_name: Counter name
            amount: Amount to increment
        """
        self._counters[counter_name] = self._counters.get(counter_name, 0) + amount
    
    def start_timer(self, timer_name: str):
        """
        Start a timer.
        
        Args:
            timer_name: Timer identifier
        """
        self._timers[timer_name] = time.time()
    
    def stop_timer(self, timer_name: str, record_as: Optional[str] = None) -> float:
        """
        Stop a timer and optionally record duration.
        
        Args:
            timer_name: Timer identifier
            record_as: Optional metric name to record duration
            
        Returns:
            Duration in seconds
        """
        if timer_name not in self._timers:
            return 0.0
        
        start_time = self._timers.pop(timer_name)
        duration = time.time() - start_time
        
        if record_as:
            self.record(record_as, duration * 1000, tags={"unit": "ms"})
        
        return duration
    
    def get_counter(self, counter_name: str) -> int:
        """Get counter value."""
        return self._counters.get(counter_name, 0)
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get metrics summary.
        
        Returns:
            Dict with counters and aggregated metrics
        """
        summary = {
            "counters": self._counters.copy(),
            "total_metrics": len(self.metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        # Aggregate metrics by name
        aggregated = {}
        for metric in self.metrics:
            if metric.name not in aggregated:
                aggregated[metric.name] = []
            aggregated[metric.name].append(metric.value)
        
        # Calculate stats
        stats = {}
        for name, values in aggregated.items():
            stats[name] = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0
            }
        
        summary["metrics"] = stats
        return summary
    
    def reset(self):
        """Clear all metrics and counters."""
        self.metrics.clear()
        self._counters.clear()
        self._timers.clear()


# Global metrics instance
_global_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """
    Get or create global metrics collector.
    
    Returns:
        MetricsCollector instance
    """
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics
