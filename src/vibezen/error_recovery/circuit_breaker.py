"""
Circuit breaker pattern implementation for fault tolerance.
"""

import asyncio
import logging
from typing import TypeVar, Callable, Optional, Any, Tuple, Type
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: timedelta = timedelta(seconds=60)
    half_open_max_calls: int = 3
    
    # Exceptions that count as failures
    failure_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (Exception,)
    )
    
    # Exceptions to always allow through
    exclude_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=tuple
    )


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
        
        # Statistics
        self.total_calls = 0
        self.total_successes = 0
        self.total_failures = 0
        self.state_changes = []
        self.recent_calls = []  # List of (timestamp, success) tuples
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call function through circuit breaker.
        
        Args:
            func: Async function to call
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: If circuit is open
            Original exception: If function fails
        """
        async with self._lock:
            # Check circuit state
            await self._check_state()
            
            if self.state == CircuitState.OPEN:
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Last failure: {self.last_failure_time}"
                )
            
            # Track half-open calls
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitOpenError(
                        f"Circuit breaker '{self.name}' half-open call limit reached"
                    )
                self.half_open_calls += 1
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except Exception as e:
            # Check if exception should be counted
            if self._should_count_failure(e):
                await self._on_failure(e)
            raise
    
    async def _check_state(self):
        """Check and update circuit state."""
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time
                if time_since_failure >= self.config.timeout:
                    logger.info(
                        f"Circuit breaker '{self.name}' moving to HALF_OPEN"
                    )
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
    
    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                
                if self.success_count >= self.config.success_threshold:
                    logger.info(
                        f"Circuit breaker '{self.name}' recovered, moving to CLOSED"
                    )
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.half_open_calls = 0
                    
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    async def _on_failure(self, exception: Exception):
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            logger.warning(
                f"Circuit breaker '{self.name}' failure {self.failure_count}: {exception}"
            )
            
            if self.state == CircuitState.HALF_OPEN:
                # Failed during recovery, go back to OPEN
                logger.error(
                    f"Circuit breaker '{self.name}' recovery failed, moving to OPEN"
                )
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.half_open_calls = 0
                
            elif self.state == CircuitState.CLOSED:
                # Check if we've hit the failure threshold
                if self.failure_count >= self.config.failure_threshold:
                    logger.error(
                        f"Circuit breaker '{self.name}' threshold reached, moving to OPEN"
                    )
                    self.state = CircuitState.OPEN
    
    def _should_count_failure(self, exception: Exception) -> bool:
        """Check if exception should count as failure."""
        # Check excluded exceptions
        if isinstance(exception, self.config.exclude_exceptions):
            return False
        
        # Check failure exceptions
        return isinstance(exception, self.config.failure_exceptions)
    
    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "half_open_calls": self.half_open_calls,
        }
    
    async def reset(self):
        """Manually reset circuit breaker."""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.half_open_calls = 0
            logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass