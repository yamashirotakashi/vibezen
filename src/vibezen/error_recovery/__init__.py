"""
Error recovery module for VIBEZEN.

Provides retry logic, circuit breaker pattern, and fallback mechanisms.
"""

from .retry_handler import RetryHandler, RetryConfig
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitOpenError
from .fallback_manager import FallbackManager, FallbackStrategy

__all__ = [
    "RetryHandler",
    "RetryConfig",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitOpenError",
    "FallbackManager",
    "FallbackStrategy",
]