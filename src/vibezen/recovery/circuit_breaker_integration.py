"""
Circuit Breaker Integration for VIBEZEN workflow.

This module provides integration points for circuit breakers throughout
the VIBEZEN quality assurance workflow.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import timedelta

from .circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerConfig, 
    CircuitBreakerManager,
    CircuitBreakerOpenError
)

logger = logging.getLogger(__name__)


@dataclass
class VIBEZENCircuitBreakerPresets:
    """Preset configurations for different VIBEZEN services."""
    
    # For external API calls (AI providers)
    AI_PROVIDER = CircuitBreakerConfig(
        failure_threshold=3,          # Open after 3 failures
        success_threshold=2,          # Close after 2 successes
        timeout=30.0,                 # Try recovery after 30 seconds
        failure_rate_threshold=0.5,   # Open if 50% failures
        min_calls=5,                  # Need 5 calls for rate calculation
        reset_timeout=300.0          # Full reset after 5 minutes idle
    )
    
    # For cache operations
    CACHE_SERVICE = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=1,
        timeout=10.0,
        failure_rate_threshold=0.7,
        min_calls=10,
        reset_timeout=120.0
    )
    
    # For external search services (o3-search)
    SEARCH_SERVICE = CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=2,
        timeout=60.0,
        failure_rate_threshold=0.4,
        min_calls=3,
        reset_timeout=180.0
    )
    
    # For Knowledge Graph operations
    KNOWLEDGE_GRAPH = CircuitBreakerConfig(
        failure_threshold=4,
        success_threshold=2,
        timeout=20.0,
        failure_rate_threshold=0.6,
        min_calls=8,
        reset_timeout=240.0
    )
    
    # For sequential thinking operations
    THINKING_ENGINE = CircuitBreakerConfig(
        failure_threshold=2,         # Thinking is expensive, fail fast
        success_threshold=1,
        timeout=45.0,
        failure_rate_threshold=0.3,
        min_calls=2,
        reset_timeout=150.0
    )


class VIBEZENCircuitBreakerIntegration:
    """
    Integration layer for circuit breakers in VIBEZEN workflow.
    
    Provides:
    - Preset configurations for different services
    - Monitoring and alerting
    - Graceful degradation strategies
    - Recovery coordination
    """
    
    def __init__(self):
        """Initialize circuit breaker integration."""
        self.manager = CircuitBreakerManager()
        self.presets = VIBEZENCircuitBreakerPresets()
        self._degradation_handlers: Dict[str, Callable] = {}
        self._recovery_handlers: Dict[str, Callable] = {}
        
    def setup_default_breakers(self):
        """Setup circuit breakers for all VIBEZEN services."""
        # AI Provider breakers
        for provider in ["openai", "google", "bedrock"]:
            self.manager.get_breaker(
                f"ai_provider_{provider}",
                self.presets.AI_PROVIDER
            )
        
        # Cache breakers
        self.manager.get_breaker("cache_exact", self.presets.CACHE_SERVICE)
        self.manager.get_breaker("cache_semantic", self.presets.CACHE_SERVICE)
        
        # External service breakers
        self.manager.get_breaker("o3_search", self.presets.SEARCH_SERVICE)
        self.manager.get_breaker("knowledge_graph", self.presets.KNOWLEDGE_GRAPH)
        
        # Thinking engine breaker
        self.manager.get_breaker("thinking_engine", self.presets.THINKING_ENGINE)
        
        logger.info("Default circuit breakers configured for VIBEZEN services")
    
    def register_degradation_handler(self, breaker_name: str, handler: Callable):
        """
        Register a handler for graceful degradation when circuit opens.
        
        Args:
            breaker_name: Name of the circuit breaker
            handler: Async function to call when circuit opens
        """
        self._degradation_handlers[breaker_name] = handler
        
    def register_recovery_handler(self, breaker_name: str, handler: Callable):
        """
        Register a handler for recovery actions when circuit closes.
        
        Args:
            breaker_name: Name of the circuit breaker
            handler: Async function to call when circuit recovers
        """
        self._recovery_handlers[breaker_name] = handler
    
    async def protected_call(
        self,
        breaker_name: str,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            breaker_name: Name of the circuit breaker to use
            func: Async function to protect
            *args: Function arguments
            fallback: Optional fallback function if circuit is open
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or fallback result
        """
        breaker = self.manager.get_breaker(breaker_name)
        
        try:
            # Try to execute through circuit breaker
            result = await breaker.call(func, *args, **kwargs)
            
            # Check if we're recovering (was open, now closed)
            if breaker_name in self._recovery_handlers:
                stats = breaker.get_stats()
                if stats['state_changes'] and stats['state_changes'][-1]['to'] == 'closed':
                    await self._recovery_handlers[breaker_name]()
            
            return result
            
        except CircuitBreakerOpenError as e:
            logger.warning(f"Circuit breaker '{breaker_name}' is open: {e}")
            
            # Call degradation handler if registered
            if breaker_name in self._degradation_handlers:
                await self._degradation_handlers[breaker_name]()
            
            # Use fallback if provided
            if fallback:
                logger.info(f"Using fallback for '{breaker_name}'")
                return await fallback(*args, **kwargs)
            
            # Re-raise if no fallback
            raise
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report of all circuit breakers.
        
        Returns:
            Health report with status and recommendations
        """
        health = self.manager.get_circuit_health()
        all_stats = self.manager.get_all_stats()
        
        # Analyze patterns
        recommendations = []
        critical_services = []
        
        for name, stats in all_stats.items():
            if stats['state'] == 'open':
                critical_services.append(name)
                
                # Service-specific recommendations
                if 'ai_provider' in name:
                    recommendations.append(
                        f"AI provider '{name}' is down. Consider using fallback providers."
                    )
                elif name == 'thinking_engine':
                    recommendations.append(
                        "Sequential Thinking is unavailable. Quality checks may be degraded."
                    )
                elif name == 'o3_search':
                    recommendations.append(
                        "External search is down. Relying on local knowledge only."
                    )
            
            elif stats['state'] == 'half_open':
                recommendations.append(
                    f"Service '{name}' is recovering. Monitor closely."
                )
            
            # Check failure rates even for closed circuits
            elif stats['recent_failure_rate'] > 0.3:
                recommendations.append(
                    f"Service '{name}' showing high failure rate ({stats['recent_failure_rate']:.1%}). "
                    "Consider investigation."
                )
        
        # Overall system recommendations
        if health['health_score'] < 0.5:
            recommendations.insert(0, 
                "CRITICAL: System health is poor. Consider pausing non-critical operations."
            )
        elif health['health_score'] < 0.8:
            recommendations.insert(0,
                "WARNING: System health is degraded. Some features may be unavailable."
            )
        
        return {
            'health': health,
            'critical_services': critical_services,
            'recommendations': recommendations,
            'detailed_stats': all_stats
        }
    
    def should_continue_workflow(self) -> bool:
        """
        Determine if workflow should continue based on circuit health.
        
        Returns:
            True if safe to continue, False if should pause
        """
        health = self.manager.get_circuit_health()
        
        # Don't continue if core services are down
        critical_circuits = ['thinking_engine', 'ai_provider_openai']
        open_critical = [
            c for c in self.manager.get_open_circuits() 
            if c in critical_circuits
        ]
        
        if open_critical:
            logger.error(f"Critical services down: {open_critical}")
            return False
        
        # Warn but continue if health is degraded
        if health['health_score'] < 0.5:
            logger.warning("System health is poor but no critical services down")
        
        return True
    
    async def coordinate_recovery(self):
        """
        Coordinate recovery actions across all circuit breakers.
        
        This method should be called periodically to:
        - Check for services ready to recover
        - Test recovered services
        - Update system state
        """
        half_open = self.manager.get_half_open_circuits()
        
        if half_open:
            logger.info(f"Services attempting recovery: {half_open}")
            
            # For each half-open circuit, we're already testing
            # The circuit breaker will handle state transitions
            # We just log and monitor
            
        # Export stats periodically for monitoring
        if logger.isEnabledFor(logging.DEBUG):
            stats = self.manager.export_stats()
            logger.debug(f"Circuit breaker stats: {stats}")


# Example degradation handlers
async def ai_provider_degradation_handler():
    """Handle AI provider circuit open."""
    logger.warning("AI provider circuit opened - switching to fallback mode")
    # Could switch to a simpler model, use cached responses, etc.


async def thinking_engine_degradation_handler():
    """Handle thinking engine circuit open."""
    logger.warning("Thinking engine unavailable - using simplified validation")
    # Could fall back to rule-based validation


async def cache_degradation_handler():
    """Handle cache circuit open."""
    logger.warning("Cache unavailable - operating without cache")
    # Just proceed without caching


# Example recovery handlers
async def ai_provider_recovery_handler():
    """Handle AI provider recovery."""
    logger.info("AI provider recovered - resuming normal operations")
    # Could warm up caches, re-enable features, etc.


async def thinking_engine_recovery_handler():
    """Handle thinking engine recovery."""
    logger.info("Thinking engine recovered - re-enabling deep analysis")
    # Could re-process recent validations