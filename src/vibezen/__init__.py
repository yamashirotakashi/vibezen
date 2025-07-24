"""
VIBEZEN - VIBEcoding Enhancement Zen

AI coding quality assurance system for preventing common AI coding failures.
"""

__version__ = "0.1.0"
__author__ = "VIBEZEN Team"

from vibezen.core.config import VIBEZENConfig
from vibezen.core.guard import VIBEZENGuard

# Sequential Thinking
try:
    from vibezen.thinking.sequential_thinking import SequentialThinkingEngine
    from vibezen.thinking.thinking_types import ThinkingContext, ThinkingPhase
except ImportError:
    pass

# Circuit Breaker
try:
    from vibezen.recovery.circuit_breaker import (
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitBreakerManager,
        CircuitBreakerOpenError
    )
    from vibezen.recovery.circuit_breaker_integration import (
        VIBEZENCircuitBreakerIntegration,
        VIBEZENCircuitBreakerPresets
    )
except ImportError:
    pass

# Workflow Integration
try:
    from vibezen.integration.workflow_integration import VIBEZENWorkflowIntegration
except ImportError:
    pass

# Performance Optimization
try:
    from vibezen.core.optimized_guard import OptimizedVIBEZENGuard
    from vibezen.performance import (
        ConnectionPool,
        BatchProcessor,
        SmartBatchProcessor,
        ResourceManager,
        ResourceLimit,
        PerformanceProfiler,
    )
    from vibezen.cache.semantic_cache_optimized import OptimizedSemanticCache
except ImportError:
    pass

__all__ = [
    "VIBEZENConfig",
    "VIBEZENGuard",
    # Sequential Thinking
    "SequentialThinkingEngine",
    "ThinkingContext",
    "ThinkingPhase",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerManager",
    "CircuitBreakerOpenError",
    "VIBEZENCircuitBreakerIntegration",
    "VIBEZENCircuitBreakerPresets",
    # Integration
    "VIBEZENWorkflowIntegration",
    # Performance Optimization
    "OptimizedVIBEZENGuard",
    "ConnectionPool",
    "BatchProcessor",
    "SmartBatchProcessor",
    "ResourceManager",
    "ResourceLimit",
    "PerformanceProfiler",
    "OptimizedSemanticCache",
]