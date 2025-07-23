"""
Cache manager for VIBEZEN that handles caching strategies.
"""

import hashlib
import json
from typing import Optional, Any, Dict, Callable
from datetime import datetime

from .cache_interface import CacheInterface, CacheEntry
from .memory_cache import MemoryCache


class CacheManager:
    """Manages caching for VIBEZEN operations."""
    
    def __init__(
        self,
        cache: Optional[CacheInterface] = None,
        enabled: bool = True,
        key_prefix: str = "vibezen",
        ttl_seconds: int = 3600
    ):
        """
        Initialize cache manager.
        
        Args:
            cache: Cache implementation to use (defaults to MemoryCache)
            enabled: Whether caching is enabled
            key_prefix: Prefix for all cache keys
            ttl_seconds: Default TTL in seconds
        """
        self.cache = cache or MemoryCache()
        self.enabled = enabled
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds
    
    def generate_key(self, operation: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key from operation and parameters.
        
        Args:
            operation: Operation name (e.g., "guide_understanding")
            params: Parameters for the operation
            
        Returns:
            Cache key string
        """
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        
        # Generate hash
        content = f"{operation}:{sorted_params}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return f"{self.key_prefix}:{operation}:{hash_digest}"
    
    async def get_or_compute(
        self,
        operation: str,
        params: Dict[str, Any],
        compute_func: Callable,
        ttl_seconds: Optional[int] = None,
        force_refresh: bool = False
    ) -> tuple[Any, bool]:
        """
        Get from cache or compute if not found.
        
        Args:
            operation: Operation name
            params: Parameters for the operation
            compute_func: Async function to compute value if not cached
            ttl_seconds: Optional TTL override
            force_refresh: Force computation even if cached
            
        Returns:
            Tuple of (value, from_cache)
        """
        if not self.enabled or force_refresh:
            value = await compute_func()
            return value, False
        
        # Generate cache key
        key = self.generate_key(operation, params)
        
        # Try to get from cache
        entry = await self.cache.get(key)
        if entry is not None:
            return entry.value, True
        
        # Compute value
        value = await compute_func()
        
        # Store in cache
        await self.cache.set(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds or self.ttl_seconds,
            metadata={
                "operation": operation,
                "params": params,
                "computed_at": datetime.now().isoformat()
            }
        )
        
        return value, False
    
    async def invalidate_operation(self, operation: str) -> int:
        """
        Invalidate all cache entries for a specific operation.
        
        Args:
            operation: Operation name to invalidate
            
        Returns:
            Number of entries invalidated
        """
        # This is a simple implementation
        # In a production system, we'd track keys by operation
        count = 0
        if hasattr(self.cache, '_cache'):
            keys_to_delete = [
                key for key in self.cache._cache.keys()
                if key.startswith(f"{self.key_prefix}:{operation}:")
            ]
            for key in keys_to_delete:
                if await self.cache.delete(key):
                    count += 1
        
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = await self.cache.stats()
        stats["enabled"] = self.enabled
        stats["key_prefix"] = self.key_prefix
        stats["default_ttl_seconds"] = self.ttl_seconds
        return stats
    
    def create_cached_method(self, operation: str, ttl_seconds: Optional[int] = None):
        """
        Create a decorator for caching method results.
        
        Args:
            operation: Operation name for cache key
            ttl_seconds: Optional TTL override
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            async def wrapper(self_or_cls, *args, **kwargs):
                # Create params dict from args and kwargs
                params = {
                    "args": args,
                    "kwargs": kwargs
                }
                
                # Create compute function
                async def compute():
                    return await func(self_or_cls, *args, **kwargs)
                
                # Get or compute
                result, from_cache = await self.get_or_compute(
                    operation=operation,
                    params=params,
                    compute_func=compute,
                    ttl_seconds=ttl_seconds
                )
                
                # Optionally add cache info to result
                if isinstance(result, dict) and "_cache_info" not in result:
                    result["_cache_info"] = {
                        "from_cache": from_cache,
                        "operation": operation
                    }
                
                return result
            
            return wrapper
        return decorator