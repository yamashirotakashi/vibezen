"""
Performance optimization module for VIBEZEN.

Provides tools for improving system performance including:
- Connection pooling
- Batch processing
- Resource management
- Performance profiling
"""

from .connection_pool import ConnectionPool, PooledConnection
from .batch_processor import BatchProcessor, BatchRequest, BatchResult
from .resource_manager import ResourceManager, ResourceLimit
from .profiler import PerformanceProfiler, ProfileResult

__all__ = [
    "ConnectionPool",
    "PooledConnection",
    "BatchProcessor",
    "BatchRequest",
    "BatchResult",
    "ResourceManager",
    "ResourceLimit",
    "PerformanceProfiler",
    "ProfileResult",
]