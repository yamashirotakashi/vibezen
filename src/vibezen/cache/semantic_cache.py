"""
Semantic caching for AI responses using embeddings and similarity search.
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
try:
    import numpy as np
except ImportError:
    # Fallback implementation without numpy
    np = None
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging

from .cache_interface import CacheInterface, CacheEntry
from .memory_cache import MemoryCache

logger = logging.getLogger(__name__)


@dataclass
class SemanticCacheEntry:
    """Entry in semantic cache with embedding."""
    key: str
    prompt: str
    response: Any
    embedding: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = 3600
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        age = datetime.now(timezone.utc) - self.created_at
        return age.total_seconds() > self.ttl_seconds


class EmbeddingProvider:
    """Abstract base class for embedding providers."""
    
    async def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        raise NotImplementedError


class SimpleEmbeddingProvider(EmbeddingProvider):
    """Simple embedding provider using hash-based vectors for testing."""
    
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
    
    async def embed(self, text: str) -> np.ndarray:
        """Generate pseudo-embedding using hash."""
        # Normalize text
        normalized = text.lower().strip()
        
        # Create multiple hashes for different dimensions
        embeddings = []
        for i in range(self.dimension):
            hash_obj = hashlib.sha256(f"{normalized}:{i}".encode())
            hash_bytes = hash_obj.digest()
            # Convert bytes to float between -1 and 1
            value = (int.from_bytes(hash_bytes[:4], 'big') / (2**32 - 1)) * 2 - 1
            embeddings.append(value)
        
        # Normalize vector
        vec = np.array(embeddings)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        return vec


class SemanticCache:
    """Semantic cache using embeddings for similarity search."""
    
    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        similarity_threshold: float = 0.85,
        max_entries: int = 1000,
        ttl_seconds: int = 3600
    ):
        """
        Initialize semantic cache.
        
        Args:
            embedding_provider: Provider for generating embeddings
            similarity_threshold: Minimum similarity for cache hit
            max_entries: Maximum number of entries to store
            ttl_seconds: Default TTL for entries
        """
        self.embedding_provider = embedding_provider or SimpleEmbeddingProvider()
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        
        # Storage
        self.entries: Dict[str, SemanticCacheEntry] = {}
        self.embeddings_matrix: Optional[np.ndarray] = None
        self.entry_keys: List[str] = []
        
        # Stats
        self.stats = {
            "lookups": 0,
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _update_embeddings_matrix(self):
        """Update the embeddings matrix for efficient search."""
        if not self.entries:
            self.embeddings_matrix = None
            self.entry_keys = []
            return
        
        # Remove expired entries
        self._cleanup_expired()
        
        # Check again after cleanup
        if not self.entries:
            self.embeddings_matrix = None
            self.entry_keys = []
            return
        
        # Build matrix
        embeddings = []
        keys = []
        
        for key, entry in self.entries.items():
            embeddings.append(entry.embedding)
            keys.append(key)
        
        self.embeddings_matrix = np.array(embeddings)
        self.entry_keys = keys
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self.entries.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.entries[key]
            self.stats["evictions"] += 1
    
    def _evict_oldest(self):
        """Evict oldest entry if cache is full."""
        if len(self.entries) >= self.max_entries:
            # Find oldest entry
            oldest_key = min(
                self.entries.keys(),
                key=lambda k: self.entries[k].created_at
            )
            del self.entries[oldest_key]
            self.stats["evictions"] += 1
    
    async def get(self, prompt: str, top_k: int = 1) -> Optional[SemanticCacheEntry]:
        """
        Get cached response for similar prompt.
        
        Args:
            prompt: The prompt to look up
            top_k: Number of top similar entries to consider
            
        Returns:
            Most similar cache entry if above threshold, None otherwise
        """
        self.stats["lookups"] += 1
        
        if not self.entries:
            self.stats["misses"] += 1
            return None
        
        # Generate embedding for query
        query_embedding = await self.embedding_provider.embed(prompt)
        
        # Update embeddings matrix
        self._update_embeddings_matrix()
        
        if self.embeddings_matrix is None:
            self.stats["misses"] += 1
            return None
        
        # Calculate similarities
        similarities = np.dot(self.embeddings_matrix, query_embedding)
        
        # Get top-k most similar
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Check if best match is above threshold
        best_idx = top_indices[0]
        best_similarity = similarities[best_idx]
        
        if best_similarity >= self.similarity_threshold:
            best_key = self.entry_keys[best_idx]
            entry = self.entries[best_key]
            
            # Check if expired
            if not entry.is_expired():
                self.stats["hits"] += 1
                logger.info(f"Semantic cache hit with similarity {best_similarity:.3f}")
                return entry
        
        self.stats["misses"] += 1
        return None
    
    async def set(
        self,
        prompt: str,
        response: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store response in semantic cache.
        
        Args:
            prompt: The prompt
            response: The response to cache
            ttl_seconds: Optional TTL override
            metadata: Optional metadata
            
        Returns:
            Cache key
        """
        # Generate key
        key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        
        # Generate embedding
        embedding = await self.embedding_provider.embed(prompt)
        
        # Evict if necessary
        self._evict_oldest()
        
        # Create entry
        entry = SemanticCacheEntry(
            key=key,
            prompt=prompt,
            response=response,
            embedding=embedding,
            metadata=metadata or {},
            ttl_seconds=ttl_seconds or self.ttl_seconds
        )
        
        # Store
        self.entries[key] = entry
        
        logger.info(f"Stored in semantic cache: {key}")
        return key
    
    async def clear(self):
        """Clear all cache entries."""
        self.entries.clear()
        self.embeddings_matrix = None
        self.entry_keys = []
        logger.info("Cleared semantic cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_lookups = self.stats["lookups"]
        hit_rate = (
            self.stats["hits"] / total_lookups if total_lookups > 0 else 0.0
        )
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "entries": len(self.entries),
            "max_entries": self.max_entries,
            "similarity_threshold": self.similarity_threshold,
        }
    
    async def search_similar(
        self,
        prompt: str,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Tuple[SemanticCacheEntry, float]]:
        """
        Search for similar prompts in cache.
        
        Args:
            prompt: Query prompt
            top_k: Number of results to return
            min_similarity: Minimum similarity score
            
        Returns:
            List of (entry, similarity) tuples
        """
        if not self.entries:
            return []
        
        # Generate embedding
        query_embedding = await self.embedding_provider.embed(prompt)
        
        # Update embeddings matrix
        self._update_embeddings_matrix()
        
        if self.embeddings_matrix is None:
            return []
        
        # Calculate similarities
        similarities = np.dot(self.embeddings_matrix, query_embedding)
        
        # Get top-k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Build results
        results = []
        for idx in top_indices:
            similarity = similarities[idx]
            if similarity >= min_similarity:
                key = self.entry_keys[idx]
                entry = self.entries[key]
                if not entry.is_expired():
                    results.append((entry, float(similarity)))
        
        return results


class SemanticCacheManager:
    """Manager for semantic caching with fallback to exact match."""
    
    def __init__(
        self,
        semantic_cache: Optional[SemanticCache] = None,
        exact_cache: Optional[CacheInterface] = None,
        semantic_enabled: bool = True,
        exact_enabled: bool = True
    ):
        """
        Initialize semantic cache manager.
        
        Args:
            semantic_cache: Semantic cache instance
            exact_cache: Exact match cache instance
            semantic_enabled: Whether semantic caching is enabled
            exact_enabled: Whether exact caching is enabled
        """
        self.semantic_cache = semantic_cache or SemanticCache()
        self.exact_cache = exact_cache or MemoryCache()
        self.semantic_enabled = semantic_enabled
        self.exact_enabled = exact_enabled
    
    async def get(self, prompt: str) -> Tuple[Optional[Any], str]:
        """
        Get cached response using semantic or exact matching.
        
        Args:
            prompt: The prompt to look up
            
        Returns:
            Tuple of (response, cache_type) where cache_type is
            "semantic", "exact", or "miss"
        """
        # Try exact match first if enabled
        if self.exact_enabled:
            key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
            entry = await self.exact_cache.get(key)
            if entry is not None:
                return entry.value, "exact"
        
        # Try semantic match if enabled
        if self.semantic_enabled:
            semantic_entry = await self.semantic_cache.get(prompt)
            if semantic_entry is not None:
                return semantic_entry.response, "semantic"
        
        return None, "miss"
    
    async def set(
        self,
        prompt: str,
        response: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store response in both caches.
        
        Args:
            prompt: The prompt
            response: The response to cache
            ttl_seconds: Optional TTL
            metadata: Optional metadata
        """
        # Store in exact cache
        if self.exact_enabled:
            key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
            await self.exact_cache.set(
                key=key,
                value=response,
                ttl_seconds=ttl_seconds,
                metadata=metadata
            )
        
        # Store in semantic cache
        if self.semantic_enabled:
            await self.semantic_cache.set(
                prompt=prompt,
                response=response,
                ttl_seconds=ttl_seconds,
                metadata=metadata
            )
    
    async def clear(self):
        """Clear both caches."""
        if self.exact_enabled:
            await self.exact_cache.clear()
        if self.semantic_enabled:
            await self.semantic_cache.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics."""
        stats = {}
        
        if self.exact_enabled:
            stats["exact_cache"] = await self.exact_cache.stats()
        
        if self.semantic_enabled:
            stats["semantic_cache"] = self.semantic_cache.get_stats()
        
        stats["semantic_enabled"] = self.semantic_enabled
        stats["exact_enabled"] = self.exact_enabled
        
        return stats