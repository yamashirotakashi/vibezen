"""
Fallback manager for graceful degradation.
"""

import asyncio
import logging
from typing import TypeVar, Callable, Optional, Any, List, Dict, Union
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')


class FallbackStrategy(Enum):
    """Fallback strategies."""
    DEFAULT_VALUE = "default_value"
    CACHED_VALUE = "cached_value"
    ALTERNATIVE_PROVIDER = "alternative_provider"
    DEGRADED_FUNCTIONALITY = "degraded_functionality"
    ERROR_MESSAGE = "error_message"


class FallbackHandler(ABC):
    """Abstract base class for fallback handlers."""
    
    @abstractmethod
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Handle fallback logic."""
        pass


class DefaultValueHandler(FallbackHandler):
    """Returns a default value on failure."""
    
    def __init__(self, default_value: Any):
        self.default_value = default_value
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Return default value."""
        logger.info(f"Returning default value due to: {exception}")
        return self.default_value


class CachedValueHandler(FallbackHandler):
    """Returns cached value on failure."""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Try to get cached value."""
        cache_key = context.get("cache_key")
        if not cache_key:
            raise ValueError("No cache_key in context for cached fallback")
        
        entry = await self.cache_manager.cache.get(cache_key)
        if entry:
            logger.info(f"Returning cached value due to: {exception}")
            return entry.value
        
        raise ValueError(f"No cached value found for key: {cache_key}")


class AlternativeProviderHandler(FallbackHandler):
    """Use alternative provider on failure."""
    
    def __init__(self, providers: List[str], proxy):
        self.providers = providers
        self.proxy = proxy
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Try alternative providers."""
        current_provider = context.get("provider")
        prompt = context.get("prompt")
        
        if not prompt:
            raise ValueError("No prompt in context for provider fallback")
        
        for provider in self.providers:
            if provider == current_provider:
                continue
                
            try:
                logger.info(f"Trying alternative provider: {provider}")
                result = await self.proxy.call(
                    prompt=prompt,
                    provider=provider,
                    **context.get("kwargs", {})
                )
                return result
            except Exception as e:
                logger.warning(f"Alternative provider {provider} failed: {e}")
                continue
        
        raise ValueError("All alternative providers failed")


class DegradedFunctionalityHandler(FallbackHandler):
    """Provide degraded functionality on failure."""
    
    def __init__(self, degraded_func: Callable):
        self.degraded_func = degraded_func
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Execute degraded functionality."""
        logger.info(f"Executing degraded functionality due to: {exception}")
        return await self.degraded_func(context)


class ErrorMessageHandler(FallbackHandler):
    """Return error message on failure."""
    
    def __init__(self, message_template: str = "Service temporarily unavailable: {error}"):
        self.message_template = message_template
    
    async def handle(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Return error message."""
        message = self.message_template.format(error=str(exception))
        logger.info(f"Returning error message: {message}")
        
        # Return in expected format
        from vibezen.proxy.ai_proxy import AIResponse
        return AIResponse(
            content=message,
            provider=context.get("provider", "fallback"),
            model=context.get("model", "fallback"),
            metadata={"fallback": True, "error": str(exception)}
        )


class FallbackManager:
    """Manages fallback strategies for error recovery."""
    
    def __init__(self):
        self.handlers: Dict[FallbackStrategy, FallbackHandler] = {}
        self.strategy_chain: List[FallbackStrategy] = []
    
    def register_handler(self, strategy: FallbackStrategy, handler: FallbackHandler):
        """Register a fallback handler."""
        self.handlers[strategy] = handler
    
    def set_strategy_chain(self, strategies: List[FallbackStrategy]):
        """Set the order of fallback strategies to try."""
        self.strategy_chain = strategies
    
    async def execute_with_fallback(
        self,
        func: Callable[..., T],
        context: Dict[str, Any],
        strategies: Optional[List[FallbackStrategy]] = None,
        *args,
        **kwargs
    ) -> T:
        """
        Execute function with fallback strategies.
        
        Args:
            func: Async function to execute
            context: Context for fallback handlers
            strategies: Override strategy chain
            *args, **kwargs: Function arguments
            
        Returns:
            Function result or fallback value
        """
        # Try primary function
        try:
            return await func(*args, **kwargs)
        except Exception as primary_exception:
            logger.error(f"Primary function failed: {primary_exception}")
            
            # Try fallback strategies
            strategies = strategies or self.strategy_chain
            
            for strategy in strategies:
                handler = self.handlers.get(strategy)
                if not handler:
                    logger.warning(f"No handler registered for strategy: {strategy}")
                    continue
                
                try:
                    logger.info(f"Trying fallback strategy: {strategy.value}")
                    return await handler.handle(primary_exception, context)
                except Exception as fallback_exception:
                    logger.warning(
                        f"Fallback strategy {strategy.value} failed: {fallback_exception}"
                    )
                    continue
            
            # All fallbacks failed
            logger.error("All fallback strategies failed")
            raise primary_exception
    
    def create_ai_fallback_chain(self, cache_manager=None, proxy=None) -> List[FallbackStrategy]:
        """Create standard fallback chain for AI calls."""
        chain = []
        
        # 1. Try cached value if available
        if cache_manager:
            self.register_handler(
                FallbackStrategy.CACHED_VALUE,
                CachedValueHandler(cache_manager)
            )
            chain.append(FallbackStrategy.CACHED_VALUE)
        
        # 2. Try alternative providers
        if proxy:
            available_providers = list(proxy.providers.keys())
            if len(available_providers) > 1:
                self.register_handler(
                    FallbackStrategy.ALTERNATIVE_PROVIDER,
                    AlternativeProviderHandler(available_providers, proxy)
                )
                chain.append(FallbackStrategy.ALTERNATIVE_PROVIDER)
        
        # 3. Return error message as last resort
        self.register_handler(
            FallbackStrategy.ERROR_MESSAGE,
            ErrorMessageHandler()
        )
        chain.append(FallbackStrategy.ERROR_MESSAGE)
        
        return chain