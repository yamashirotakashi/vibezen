"""
Cache interface and models for VIBEZEN.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel


class CacheEntry(BaseModel):
    """Cache entry model."""
    
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    metadata: Dict[str, Any] = {}
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def increment_hit_count(self):
        """Increment hit count for metrics."""
        self.hit_count += 1


class CacheInterface(ABC):
    """Abstract interface for cache implementations."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from cache by key."""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def size(self) -> int:
        """Get number of entries in cache."""
        pass
    
    @abstractmethod
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass