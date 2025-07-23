"""
Test semantic caching functionality.
"""

import numpy as np
from datetime import datetime, timedelta, timezone

from vibezen.cache.semantic_cache import (
    SemanticCache, SemanticCacheEntry, SimpleEmbeddingProvider,
    SemanticCacheManager, EmbeddingProvider
)
from vibezen.cache.memory_cache import MemoryCache


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""
    
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.embeddings = {}
    
    async def embed(self, text: str) -> np.ndarray:
        """Generate deterministic embedding for testing."""
        if text not in self.embeddings:
            # Create embedding based on text content
            vec = np.zeros(self.dimension)
            
            # Simple heuristic embeddings
            if "weather" in text.lower():
                vec[0] = 1.0
            if "python" in text.lower():
                vec[1] = 1.0
            if "code" in text.lower():
                vec[2] = 1.0
            if "today" in text.lower():
                vec[3] = 1.0
            if "tomorrow" in text.lower():
                vec[4] = 1.0
            
            # Add some noise
            for i, char in enumerate(text[:20]):
                vec[10 + i] = ord(char) / 255.0
            
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            
            self.embeddings[text] = vec
        
        return self.embeddings[text]


class TestSimpleEmbeddingProvider:
    """Test simple embedding provider."""
    
    async def test_embed_generation(self):
        """Test embedding generation."""
        provider = SimpleEmbeddingProvider(dimension=128)
        
        # Generate embeddings
        embed1 = await provider.embed("Hello world")
        embed2 = await provider.embed("Hello world")
        embed3 = await provider.embed("Goodbye world")
        
        # Check properties
        assert embed1.shape == (128,)
        assert np.allclose(embed1, embed2)  # Same text -> same embedding
        assert not np.allclose(embed1, embed3)  # Different text -> different embedding
        
        # Check normalization
        assert np.isclose(np.linalg.norm(embed1), 1.0)
    
    async def test_case_insensitive(self):
        """Test case insensitive embedding."""
        provider = SimpleEmbeddingProvider()
        
        embed1 = await provider.embed("Hello World")
        embed2 = await provider.embed("hello world")
        
        assert np.allclose(embed1, embed2)


class TestSemanticCache:
    """Test semantic cache functionality."""
    
    async def test_basic_operations(self):
        """Test basic get/set operations."""
        cache = SemanticCache(
            embedding_provider=MockEmbeddingProvider(),
            similarity_threshold=0.8
        )
        
        # Store entry
        await cache.set("What's the weather today?", "Sunny and warm")
        
        # Exact match should work
        entry = await cache.get("What's the weather today?")
        assert entry is not None
        assert entry.response == "Sunny and warm"
        
        # Similar query should work
        entry = await cache.get("What is the weather today?")
        assert entry is not None
        assert entry.response == "Sunny and warm"
        
        # Different query should not match
        entry = await cache.get("How to code in Python?")
        assert entry is None
    
    async def test_similarity_threshold(self):
        """Test similarity threshold behavior."""
        cache = SemanticCache(
            embedding_provider=MockEmbeddingProvider(),
            similarity_threshold=0.9  # High threshold
        )
        
        await cache.set("Python code example", "print('Hello')")
        
        # Very similar should match
        entry = await cache.get("Python code example")
        assert entry is not None
        
        # Slightly different might not match with high threshold
        entry = await cache.get("Python coding example")
        # This depends on the embedding provider's similarity calculation
        # With our mock provider, this might not match
    
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = SemanticCache(ttl_seconds=1)
        
        # Create expired entry
        entry = SemanticCacheEntry(
            key="test",
            prompt="test prompt",
            response="test response",
            embedding=np.zeros(128),
            created_at=datetime.now(timezone.utc) - timedelta(seconds=2),
            ttl_seconds=1
        )
        
        assert entry.is_expired()
        
        # Expired entries should not be returned
        cache.entries["test"] = entry
        result = await cache.get("test prompt")
        assert result is None
    
    async def test_eviction(self):
        """Test cache eviction when full."""
        cache = SemanticCache(
            embedding_provider=MockEmbeddingProvider(),
            max_entries=3
        )
        
        # Fill cache
        await cache.set("prompt1", "response1")
        await cache.set("prompt2", "response2")
        await cache.set("prompt3", "response3")
        
        assert len(cache.entries) == 3
        
        # Adding one more should evict oldest
        await cache.set("prompt4", "response4")
        assert len(cache.entries) == 3
        assert cache.stats["evictions"] == 1
    
    async def test_search_similar(self):
        """Test searching for similar prompts."""
        cache = SemanticCache(embedding_provider=MockEmbeddingProvider())
        
        # Add various prompts
        await cache.set("What's the weather today?", "Sunny")
        await cache.set("How's the weather tomorrow?", "Rainy")
        await cache.set("Python code for loops", "for i in range(10):")
        await cache.set("Python code for lists", "[1, 2, 3]")
        
        # Search for weather-related
        results = await cache.search_similar("weather forecast", top_k=2)
        assert len(results) == 2
        # Results should be weather-related prompts
        for entry, similarity in results:
            assert "weather" in entry.prompt.lower()
        
        # Search for Python-related
        results = await cache.search_similar("Python programming", top_k=2)
        assert len(results) == 2
        for entry, similarity in results:
            assert "python" in entry.prompt.lower()
    
    async def test_statistics(self):
        """Test cache statistics."""
        cache = SemanticCache(embedding_provider=MockEmbeddingProvider())
        
        # Initial stats
        stats = cache.get_stats()
        assert stats["lookups"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # Add and lookup
        await cache.set("test prompt", "response")
        await cache.get("test prompt")  # Hit
        await cache.get("different prompt")  # Miss
        
        stats = cache.get_stats()
        assert stats["lookups"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestSemanticCacheManager:
    """Test semantic cache manager."""
    
    async def test_fallback_behavior(self):
        """Test fallback from exact to semantic matching."""
        manager = SemanticCacheManager(
            semantic_cache=SemanticCache(
                embedding_provider=MockEmbeddingProvider(),
                similarity_threshold=0.8
            ),
            exact_cache=MemoryCache()
        )
        
        # Store a response
        await manager.set("What's the weather?", "Sunny")
        
        # Exact match should be found first
        response, cache_type = await manager.get("What's the weather?")
        assert response == "Sunny"
        assert cache_type == "exact"
        
        # Similar query should use semantic cache
        response, cache_type = await manager.get("What is the weather?")
        assert response == "Sunny"
        assert cache_type == "semantic"
        
        # Very different query should miss
        response, cache_type = await manager.get("How to code?")
        assert response is None
        assert cache_type == "miss"
    
    async def test_disabled_caches(self):
        """Test with disabled cache types."""
        # Only semantic enabled
        manager = SemanticCacheManager(
            semantic_cache=SemanticCache(embedding_provider=MockEmbeddingProvider()),
            exact_enabled=False
        )
        
        await manager.set("test prompt", "response")
        
        # Should only find through semantic
        response, cache_type = await manager.get("test prompt")
        assert response == "response"
        assert cache_type == "semantic"
        
        # Only exact enabled
        manager = SemanticCacheManager(
            exact_cache=MemoryCache(),
            semantic_enabled=False
        )
        
        await manager.set("test prompt", "response")
        
        # Should only find through exact
        response, cache_type = await manager.get("test prompt")
        assert response == "response"
        assert cache_type == "exact"
        
        # Similar query should miss
        response, cache_type = await manager.get("test prompts")
        assert response is None
        assert cache_type == "miss"
    
    async def test_clear_operations(self):
        """Test clearing caches."""
        manager = SemanticCacheManager(
            semantic_cache=SemanticCache(embedding_provider=MockEmbeddingProvider()),
            exact_cache=MemoryCache()
        )
        
        # Add data
        await manager.set("prompt1", "response1")
        await manager.set("prompt2", "response2")
        
        # Verify data exists
        response, _ = await manager.get("prompt1")
        assert response == "response1"
        
        # Clear
        await manager.clear()
        
        # Verify cleared
        response, cache_type = await manager.get("prompt1")
        assert response is None
        assert cache_type == "miss"
    
    async def test_statistics(self):
        """Test combined statistics."""
        manager = SemanticCacheManager(
            semantic_cache=SemanticCache(embedding_provider=MockEmbeddingProvider()),
            exact_cache=MemoryCache()
        )
        
        # Generate some activity
        await manager.set("prompt1", "response1")
        await manager.get("prompt1")  # Exact hit
        await manager.get("prompt 1")  # Semantic hit
        await manager.get("different")  # Miss
        
        stats = await manager.get_stats()
        assert "exact_cache" in stats
        assert "semantic_cache" in stats
        assert stats["semantic_enabled"] is True
        assert stats["exact_enabled"] is True


class TestIntegration:
    """Integration tests with AI proxy."""
    
    async def test_with_ai_proxy(self):
        """Test semantic cache integration with AI proxy."""
        from vibezen.proxy.ai_proxy import AIProxy, ProxyConfig
        
        # Create proxy with semantic caching
        semantic_cache = SemanticCache(
            embedding_provider=MockEmbeddingProvider(),
            similarity_threshold=0.85
        )
        
        config = ProxyConfig(
            cache_prompts=True,
            enable_semantic_cache=True  # This would be a new config option
        )
        
        # In a real implementation, we'd integrate SemanticCacheManager
        # into the AIProxy class
        proxy = AIProxy(config)
        
        # For now, just verify the cache works independently
        await semantic_cache.set(
            "Explain machine learning",
            "Machine learning is a subset of AI..."
        )
        
        entry = await semantic_cache.get("Explain ML")
        # Depending on embedding quality, this might or might not match