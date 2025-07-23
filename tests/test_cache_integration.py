"""
Test cache integration with AI proxy.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from vibezen.proxy.ai_proxy import AIProxy, ProxyConfig, AIRequest, AIResponse
from vibezen.core.models import ThinkingContext, ThinkingPhase


@pytest.mark.asyncio
async def test_cache_hit():
    """Test that cached responses are returned on subsequent calls."""
    # Create proxy with caching enabled
    config = ProxyConfig(
        cache_prompts=True,
        cache_ttl_seconds=60,
        cache_max_size=100
    )
    proxy = AIProxy(config)
    
    # Make first call
    response1 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Make second call with same parameters
    response2 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Check that response was cached
    assert response2.metadata.get("from_cache") is True
    assert response1.content == response2.content
    
    # Check cache stats
    stats = await proxy.get_cache_stats()
    assert stats["total_hits"] == 1
    assert stats["total_misses"] == 1
    assert stats["hit_rate"] == 0.5


@pytest.mark.asyncio
async def test_cache_miss_different_params():
    """Test that different parameters result in cache miss."""
    config = ProxyConfig(cache_prompts=True)
    proxy = AIProxy(config)
    
    # Make first call
    response1 = await proxy.call(
        prompt="Test prompt 1",
        provider="mock",
        model="test-model"
    )
    
    # Make second call with different prompt
    response2 = await proxy.call(
        prompt="Test prompt 2",
        provider="mock",
        model="test-model"
    )
    
    # Check that response was not cached
    assert response2.metadata.get("from_cache") is False
    assert response1.content != response2.content


@pytest.mark.asyncio
async def test_cache_disabled():
    """Test that caching can be disabled."""
    config = ProxyConfig(cache_prompts=False)
    proxy = AIProxy(config)
    
    # Make first call
    response1 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Make second call with same parameters
    response2 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Check that response was not cached
    assert response2.metadata.get("from_cache") is False


@pytest.mark.asyncio
async def test_cache_with_context():
    """Test caching with thinking context."""
    config = ProxyConfig(
        cache_prompts=True,
        enable_interception=True,
        enable_thinking_prompts=True
    )
    proxy = AIProxy(config)
    
    # Create context
    context = ThinkingContext(
        phase=ThinkingPhase.GUIDE_UNDERSTANDING,
        specification={"feature": "test feature"},
        confidence=0.8
    )
    
    # Make first call
    response1 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model",
        context=context
    )
    
    # Make second call with same context
    response2 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model",
        context=context
    )
    
    # Check that response was cached
    assert response2.metadata.get("from_cache") is True


@pytest.mark.asyncio
async def test_cache_clear():
    """Test clearing the cache."""
    config = ProxyConfig(cache_prompts=True)
    proxy = AIProxy(config)
    
    # Make a call to populate cache
    await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Clear cache
    await proxy.clear_cache()
    
    # Make same call again
    response = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Check that response was not cached
    assert response.metadata.get("from_cache") is False


@pytest.mark.asyncio
async def test_cache_ttl():
    """Test cache entry expiration."""
    # Create proxy with very short TTL
    config = ProxyConfig(
        cache_prompts=True,
        cache_ttl_seconds=1  # 1 second TTL
    )
    proxy = AIProxy(config)
    
    # Make first call
    response1 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Wait for TTL to expire
    await asyncio.sleep(1.5)
    
    # Make second call
    response2 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Check that response was not cached (expired)
    assert response2.metadata.get("from_cache") is False


@pytest.mark.asyncio
async def test_cache_stats():
    """Test cache statistics."""
    config = ProxyConfig(cache_prompts=True)
    proxy = AIProxy(config)
    
    # Make several calls
    prompts = ["Prompt 1", "Prompt 2", "Prompt 1", "Prompt 3", "Prompt 1"]
    
    for prompt in prompts:
        await proxy.call(
            prompt=prompt,
            provider="mock",
            model="test-model"
        )
    
    # Get cache stats
    stats = await proxy.get_cache_stats()
    
    # Verify stats
    assert stats["enabled"] is True
    assert stats["total_hits"] == 2  # "Prompt 1" hit twice
    assert stats["total_misses"] == 3  # Three unique prompts
    assert stats["hit_rate"] == 0.4  # 2 hits out of 5 requests
    assert stats["size"] == 3  # Three unique entries cached


@pytest.mark.asyncio
async def test_cache_with_parameters():
    """Test caching with different parameters."""
    config = ProxyConfig(cache_prompts=True)
    proxy = AIProxy(config)
    
    # Make calls with different parameters
    response1 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model",
        temperature=0.7
    )
    
    response2 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model",
        temperature=0.9
    )
    
    response3 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model",
        temperature=0.7
    )
    
    # Check caching behavior
    assert response2.metadata.get("from_cache") is False  # Different temperature
    assert response3.metadata.get("from_cache") is True   # Same as response1


@pytest.mark.asyncio
async def test_cache_error_handling():
    """Test that errors are not cached."""
    config = ProxyConfig(cache_prompts=True)
    proxy = AIProxy(config)
    
    # Make a call that will fail (invalid provider)
    with pytest.raises(ValueError):
        await proxy.call(
            prompt="Test prompt",
            provider="invalid_provider",
            model="test-model"
        )
    
    # Register the provider and try again
    from vibezen.proxy.ai_proxy import MockAIProvider
    proxy.register_provider("invalid_provider", MockAIProvider())
    
    # This should work and not be cached
    response = await proxy.call(
        prompt="Test prompt",
        provider="invalid_provider",
        model="test-model"
    )
    
    assert response.metadata.get("from_cache") is False