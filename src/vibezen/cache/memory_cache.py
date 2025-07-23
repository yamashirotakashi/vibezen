"""
In-memory LRU cache implementation for VIBEZEN.
"""

from typing import Optional, Any, Dict, OrderedDict
from datetime import datetime, timedelta
import asyncio
from collections import OrderedDict as ODict

from .cache_interface import CacheInterface, CacheEntry


class MemoryCache(CacheInterface):
    """In-memory LRU cache implementation."""
    
    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 3600):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries in cache
            default_ttl_seconds: Default TTL in seconds (1 hour)
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = ODict()
        self._lock = asyncio.Lock()
        self._total_hits = 0
        self._total_misses = 0
        self._total_evictions = 0
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from cache by key."""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._total_misses += 1
                return None
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._total_misses += 1
                return None
            
            # Move to end for LRU
            self._cache.move_to_end(key)
            entry.increment_hit_count()
            self._total_hits += 1
            
            return entry
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set value in cache with optional TTL."""
        async with self._lock:
            # Calculate expiration
            ttl = ttl_seconds or self.default_ttl_seconds
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            # Add to cache
            if key in self._cache:
                # Update existing entry
                self._cache[key] = entry
                self._cache.move_to_end(key)
            else:
                # Add new entry
                self._cache[key] = entry
                
                # Evict oldest if at capacity
                if len(self._cache) > self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._total_evictions += 1
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._total_hits = 0
            self._total_misses = 0
            self._total_evictions = 0
    
    async def size(self) -> int:
        """Get number of entries in cache."""
        async with self._lock:
            # Clean up expired entries
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            
            return len(self._cache)
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._total_hits + self._total_misses
            hit_rate = self._total_hits / total_requests if total_requests > 0 else 0.0
            
            # Calculate memory usage (approximate)
            total_hit_count = sum(entry.hit_count for entry in self._cache.values())
            avg_hit_count = total_hit_count / len(self._cache) if self._cache else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "total_hits": self._total_hits,
                "total_misses": self._total_misses,
                "total_evictions": self._total_evictions,
                "hit_rate": hit_rate,
                "avg_hit_count": avg_hit_count,
                "oldest_entry": min(
                    (entry.created_at for entry in self._cache.values()),
                    default=None
                ),
                "newest_entry": max(
                    (entry.created_at for entry in self._cache.values()),
                    default=None
                ),
            }