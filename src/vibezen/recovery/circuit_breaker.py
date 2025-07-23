"""
Circuit Breaker pattern implementation for VIBEZEN
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta
import json
from ..logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failure threshold reached, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 2          # Successes in half-open before closing
    timeout: float = 60.0              # Seconds before trying half-open
    failure_rate_threshold: float = 0.5  # Failure rate to open circuit
    min_calls: int = 10                # Minimum calls before rate calculation
    reset_timeout: float = 120.0       # Full reset after this time of no calls


class CircuitBreaker:
    """
    Circuit Breaker implementation
    
    Prevents cascading failures by blocking calls to failing services
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_call_time: Optional[float] = None
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = []
        
        # Call history for rate calculation
        self.recent_calls = []  # List of (timestamp, success) tuples
        
    def _change_state(self, new_state: CircuitState):
        """Change circuit state and log"""
        old_state = self.state
        self.state = new_state
        self.state_changes.append({
            'from': old_state.value,
            'to': new_state.value,
            'timestamp': time.time(),
            'failure_count': self.failure_count,
            'success_count': self.success_count
        })
        logger.log_circuit_breaker_event(
            breaker_name=self.name,
            event="state_changed",
            state=new_state.value,
            from_state=old_state.value,
            failure_count=self.failure_count,
            success_count=self.success_count
        )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.timeout
    
    def _calculate_failure_rate(self) -> float:
        """Calculate recent failure rate"""
        if not self.recent_calls:
            return 0.0
        
        # Clean old calls (keep last min_calls * 2)
        if len(self.recent_calls) > self.config.min_calls * 2:
            self.recent_calls = self.recent_calls[-self.config.min_calls * 2:]
        
        # Calculate rate from recent calls
        failures = sum(1 for _, success in self.recent_calls if not success)
        return failures / len(self.recent_calls) if self.recent_calls else 0.0
    
    def _reset_if_idle(self):
        """Reset circuit if idle for too long"""
        if self.last_call_time and time.time() - self.last_call_time > self.config.reset_timeout:
            if self.state != CircuitState.CLOSED:
                logger.info(f"Circuit breaker '{self.name}' reset due to inactivity")
                self._change_state(CircuitState.CLOSED)
                self.failure_count = 0
                self.success_count = 0
                self.recent_calls.clear()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        
        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        self._reset_if_idle()
        self.last_call_time = time.time()
        self.total_calls += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._change_state(CircuitState.HALF_OPEN)
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self.config.timeout - (time.time() - self.last_failure_time):.1f}s"
                )
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Record success
            self._on_success()
            return result
            
        except Exception as e:
            # Record failure
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.total_successes += 1
        self.recent_calls.append((time.time(), True))
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self.failure_count = 0  # Reset failure count on success
            
            if self.success_count >= self.config.success_threshold:
                # Enough successes, close the circuit
                self._change_state(CircuitState.CLOSED)
                self.success_count = 0
                logger.log_circuit_breaker_event(
                    breaker_name=self.name,
                    event="recovered",
                    state=CircuitState.CLOSED.value,
                    success_count=self.success_count
                )
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success in closed state
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.recent_calls.append((time.time(), False))
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open state, immediately open
            self._change_state(CircuitState.OPEN)
            self.success_count = 0
            logger.log_circuit_breaker_event(
                breaker_name=self.name,
                event="opened",
                state=CircuitState.OPEN.value,
                reason="failure_in_half_open",
                failure_count=self.failure_count
            )
        
        elif self.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            should_open = False
            
            # Check absolute failure threshold
            if self.failure_count >= self.config.failure_threshold:
                should_open = True
                logger.log_circuit_breaker_event(
                    breaker_name=self.name,
                    event="opened",
                    state=CircuitState.OPEN.value,
                    reason="failure_threshold_exceeded",
                    failure_count=self.failure_count,
                    threshold=self.config.failure_threshold
                )
            
            # Check failure rate
            elif len(self.recent_calls) >= self.config.min_calls:
                failure_rate = self._calculate_failure_rate()
                if failure_rate >= self.config.failure_rate_threshold:
                    should_open = True
                    logger.log_circuit_breaker_event(
                        breaker_name=self.name,
                        event="opened",
                        state=CircuitState.OPEN.value,
                        reason="failure_rate_exceeded",
                        failure_rate=failure_rate,
                        rate_threshold=self.config.failure_rate_threshold
                    )
            
            if should_open:
                self._change_state(CircuitState.OPEN)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        success_rate = (
            self.total_successes / self.total_calls 
            if self.total_calls > 0 else 0.0
        )
        
        return {
            'name': self.name,
            'state': self.state.value,
            'total_calls': self.total_calls,
            'total_successes': self.total_successes,
            'total_failures': self.total_failures,
            'success_rate': success_rate,
            'failure_count': self.failure_count,
            'recent_failure_rate': self._calculate_failure_rate(),
            'state_changes': len(self.state_changes),
            'last_state_change': self.state_changes[-1] if self.state_changes else None
        }
    
    def reset(self):
        """Manually reset the circuit breaker"""
        logger.log_circuit_breaker_event(
            breaker_name=self.name,
            event="manual_reset",
            state=CircuitState.CLOSED.value
        )
        self._change_state(CircuitState.CLOSED)
        self.failure_count = 0
        self.success_count = 0
        self.recent_calls.clear()
        self.last_failure_time = None


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers
    """
    
    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        self.default_config = default_config or CircuitBreakerConfig()
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(
                name, 
                config or self.default_config
            )
        return self.breakers[name]
    
    async def call(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Call function through named circuit breaker"""
        breaker = self.get_breaker(name)
        return await breaker.call(func, *args, **kwargs)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {
            name: breaker.get_stats() 
            for name, breaker in self.breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()
    
    def get_open_circuits(self) -> List[str]:
        """Get list of open circuit breakers"""
        return [
            name for name, breaker in self.breakers.items()
            if breaker.state == CircuitState.OPEN
        ]
    
    def get_half_open_circuits(self) -> List[str]:
        """Get list of half-open circuit breakers"""
        return [
            name for name, breaker in self.breakers.items()
            if breaker.state == CircuitState.HALF_OPEN
        ]
    
    def get_circuit_health(self) -> Dict[str, Any]:
        """Get overall health of all circuits"""
        total_circuits = len(self.breakers)
        open_circuits = self.get_open_circuits()
        half_open_circuits = self.get_half_open_circuits()
        
        if total_circuits == 0:
            health_score = 1.0
        else:
            # Calculate health score: 1.0 = all closed, 0.0 = all open
            closed_count = total_circuits - len(open_circuits) - len(half_open_circuits)
            health_score = (
                closed_count * 1.0 + 
                len(half_open_circuits) * 0.5 + 
                len(open_circuits) * 0.0
            ) / total_circuits
        
        return {
            'total_circuits': total_circuits,
            'closed_count': total_circuits - len(open_circuits) - len(half_open_circuits),
            'open_count': len(open_circuits),
            'half_open_count': len(half_open_circuits),
            'health_score': health_score,
            'open_circuits': open_circuits,
            'half_open_circuits': half_open_circuits,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_stats(self, filepath: Optional[str] = None) -> str:
        """Export all circuit breaker statistics to JSON"""
        stats = {
            'manager_stats': {
                'total_breakers': len(self.breakers),
                'health': self.get_circuit_health()
            },
            'breaker_stats': self.get_all_stats(),
            'timestamp': datetime.now().isoformat()
        }
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2)
            logger.info(f"Circuit breaker stats exported to {filepath}")
        
        return json.dumps(stats, indent=2)