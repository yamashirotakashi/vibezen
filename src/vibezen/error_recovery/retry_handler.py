"""
Retry handler with exponential backoff and jitter.
"""

import asyncio
import random
import logging
from typing import TypeVar, Callable, Optional, Any, Union, Type, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: Tuple[float, float] = (0.8, 1.2)
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        asyncio.TimeoutError,
        ConnectionError,
        TimeoutError,
    )
    
    def should_retry(self, exception: Exception) -> bool:
        """Check if exception is retryable."""
        return isinstance(exception, self.retryable_exceptions)


class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._retry_counts = {}
        
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        # Exponential backoff
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        # Add jitter if enabled
        if self.config.jitter:
            jitter_min, jitter_max = self.config.jitter_range
            delay *= random.uniform(jitter_min, jitter_max)
        
        return delay
    
    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        operation_id: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> T:
        """
        Execute function with retry logic.
        
        Args:
            func: Async function to execute
            operation_id: Optional ID for tracking retries
            timeout: Optional timeout for each attempt
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result
            
        Raises:
            The last exception if all retries fail
        """
        last_exception = None
        operation_id = operation_id or f"{func.__name__}_{id(func)}"
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Log retry attempt
                if attempt > 0:
                    delay = self._calculate_delay(attempt - 1)
                    logger.warning(
                        f"Retry {attempt}/{self.config.max_retries} for {operation_id} "
                        f"after {delay:.2f}s delay"
                    )
                    await asyncio.sleep(delay)
                
                # Execute with optional timeout
                if timeout:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                else:
                    result = await func(*args, **kwargs)
                
                # Success - reset retry count
                self._retry_counts[operation_id] = 0
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if retryable
                if not self.config.should_retry(e):
                    logger.error(f"Non-retryable error in {operation_id}: {e}")
                    raise
                
                # Check if we have retries left
                if attempt == self.config.max_retries:
                    logger.error(
                        f"All retries exhausted for {operation_id}. "
                        f"Last error: {e}"
                    )
                    self._retry_counts[operation_id] = attempt + 1
                    raise
                
                # Log the error
                logger.warning(
                    f"Retryable error in {operation_id} (attempt {attempt + 1}): {e}"
                )
        
        # Should not reach here
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Unexpected retry handler state")
    
    def get_retry_stats(self, operation_id: str) -> dict:
        """Get retry statistics for an operation."""
        return {
            "retry_count": self._retry_counts.get(operation_id, 0),
            "max_retries": self.config.max_retries,
        }
    
    def reset_stats(self, operation_id: Optional[str] = None):
        """Reset retry statistics."""
        if operation_id:
            self._retry_counts.pop(operation_id, None)
        else:
            self._retry_counts.clear()


class RetryDecorator:
    """Decorator for adding retry logic to async functions."""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.handler = RetryHandler(retry_config)
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorate async function with retry logic."""
        async def wrapper(*args, **kwargs):
            return await self.handler.execute_with_retry(
                func,
                *args,
                operation_id=func.__name__,
                **kwargs
            )
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper


# Convenience decorator
retry = RetryDecorator()