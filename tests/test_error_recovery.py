"""
Test error recovery mechanisms.
"""

import pytest
import asyncio
from datetime import timedelta

from vibezen.proxy.ai_proxy import AIProxy, ProxyConfig, AIProvider, AIRequest, AIResponse
from vibezen.error_recovery import CircuitOpenError


class FailingProvider(AIProvider):
    """Provider that fails on demand for testing."""
    
    def __init__(self, fail_count: int = 0):
        self.fail_count = fail_count
        self.call_count = 0
    
    async def call(self, request: AIRequest) -> AIResponse:
        """Fail for first N calls."""
        self.call_count += 1
        
        if self.call_count <= self.fail_count:
            raise ConnectionError(f"Simulated failure {self.call_count}")
        
        return AIResponse(
            content=f"Success after {self.call_count} attempts",
            provider="failing",
            model=request.model
        )
    
    def is_available(self) -> bool:
        return True


class TimeoutProvider(AIProvider):
    """Provider that times out for testing."""
    
    def __init__(self, timeout_duration: float = 5.0):
        self.timeout_duration = timeout_duration
    
    async def call(self, request: AIRequest) -> AIResponse:
        """Simulate timeout."""
        await asyncio.sleep(self.timeout_duration)
        return AIResponse(
            content="Should not reach here",
            provider="timeout",
            model=request.model
        )
    
    def is_available(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_retry_on_failure():
    """Test retry mechanism on transient failures."""
    config = ProxyConfig(
        max_retries=3,
        retry_initial_delay=0.1,
        timeout_seconds=10
    )
    proxy = AIProxy(config)
    
    # Register provider that fails twice then succeeds
    failing_provider = FailingProvider(fail_count=2)
    proxy.register_provider("failing", failing_provider)
    
    # Should succeed after retries
    response = await proxy.call(
        prompt="Test prompt",
        provider="failing",
        model="test-model"
    )
    
    assert response.content == "Success after 3 attempts"
    assert failing_provider.call_count == 3
    
    # Check retry stats
    stats = proxy.get_error_recovery_stats()
    assert stats["retry_stats"]["failing"]["retry_count"] == 0  # Reset after success


@pytest.mark.asyncio
async def test_retry_exhaustion():
    """Test when all retries are exhausted."""
    config = ProxyConfig(
        max_retries=2,
        retry_initial_delay=0.1,
        enable_fallback=False  # Disable fallback to test retry exhaustion
    )
    proxy = AIProxy(config)
    
    # Register provider that always fails
    failing_provider = FailingProvider(fail_count=10)
    proxy.register_provider("failing", failing_provider)
    
    # Should fail after exhausting retries
    with pytest.raises(ConnectionError):
        await proxy.call(
            prompt="Test prompt",
            provider="failing",
            model="test-model"
        )
    
    # Should have made max_retries + 1 attempts
    assert failing_provider.call_count == 3
    
    # Check retry stats
    stats = proxy.get_error_recovery_stats()
    assert stats["retry_stats"]["failing"]["retry_count"] == 3


@pytest.mark.asyncio
async def test_timeout_retry():
    """Test retry on timeout."""
    config = ProxyConfig(
        max_retries=2,
        retry_initial_delay=0.1,
        timeout_seconds=0.5,
        enable_fallback=False  # Disable fallback to test timeout behavior
    )
    proxy = AIProxy(config)
    
    # Register provider that times out
    timeout_provider = TimeoutProvider(timeout_duration=1.0)
    proxy.register_provider("timeout", timeout_provider)
    
    # Should fail with timeout
    with pytest.raises(asyncio.TimeoutError):
        await proxy.call(
            prompt="Test prompt",
            provider="timeout",
            model="test-model"
        )


@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    """Test circuit breaker opening after failures."""
    config = ProxyConfig(
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_timeout_seconds=1,
        max_retries=0,  # No retries to test circuit breaker
        enable_fallback=False  # Disable fallback to test circuit breaker
    )
    proxy = AIProxy(config)
    
    # Register provider that always fails
    failing_provider = FailingProvider(fail_count=10)
    proxy.register_provider("failing", failing_provider)
    
    # Make calls until circuit opens
    for i in range(3):
        with pytest.raises(ConnectionError):
            await proxy.call(
                prompt=f"Test prompt {i}",
                provider="failing",
                model="test-model"
            )
    
    # Next call should fail with circuit open
    with pytest.raises(CircuitOpenError):
        await proxy.call(
            prompt="Test prompt",
            provider="failing",
            model="test-model"
        )
    
    # Check circuit breaker state
    stats = proxy.get_error_recovery_stats()
    assert stats["circuit_breaker_states"]["failing"]["state"] == "open"
    assert stats["circuit_breaker_states"]["failing"]["failure_count"] == 3


@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    """Test circuit breaker recovery."""
    config = ProxyConfig(
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=2,
        circuit_breaker_timeout_seconds=1,
        max_retries=0,
        enable_fallback=False  # Disable fallback to test circuit breaker recovery
    )
    proxy = AIProxy(config)
    
    # Register provider that fails then recovers
    failing_provider = FailingProvider(fail_count=2)
    proxy.register_provider("failing", failing_provider)
    
    # Open circuit
    for i in range(2):
        with pytest.raises(ConnectionError):
            await proxy.call(
                prompt=f"Test prompt {i}",
                provider="failing",
                model="test-model"
            )
    
    # Circuit should be open
    with pytest.raises(CircuitOpenError):
        await proxy.call(
            prompt="Test prompt",
            provider="failing",
            model="test-model"
        )
    
    # Wait for timeout
    await asyncio.sleep(1.1)
    
    # Should succeed now (provider recovered)
    # Need to make success_threshold (2) successful calls to close circuit
    response1 = await proxy.call(
        prompt="Test prompt 1",
        provider="failing",
        model="test-model"
    )
    assert "Success" in response1.content
    
    # Second successful call to meet success threshold
    response2 = await proxy.call(
        prompt="Test prompt 2",
        provider="failing",
        model="test-model"
    )
    assert "Success" in response2.content
    
    # Circuit should be closed again after meeting success threshold
    stats = proxy.get_error_recovery_stats()
    assert stats["circuit_breaker_states"]["failing"]["state"] == "closed"


@pytest.mark.asyncio
async def test_fallback_to_cache():
    """Test fallback to cached value."""
    config = ProxyConfig(
        enable_fallback=True,
        cache_prompts=True,
        max_retries=0
    )
    proxy = AIProxy(config)
    
    # First, make a successful call to populate cache
    proxy.register_provider("mock", proxy.providers["mock"])  # Use built-in mock
    
    response1 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Replace with failing provider
    failing_provider = FailingProvider(fail_count=10)
    proxy.providers["mock"] = failing_provider
    
    # Should get cached value on failure
    response2 = await proxy.call(
        prompt="Test prompt",
        provider="mock",
        model="test-model"
    )
    
    # Should be from cache
    assert response2.metadata.get("from_cache") is True
    assert response2.content == response1.content


@pytest.mark.asyncio
async def test_fallback_to_alternative_provider():
    """Test fallback to alternative provider."""
    config = ProxyConfig(
        enable_fallback=True,
        cache_prompts=False,  # Disable cache to test provider fallback
        max_retries=0
    )
    proxy = AIProxy(config)
    
    # Register multiple providers
    failing_provider = FailingProvider(fail_count=10)
    proxy.register_provider("primary", failing_provider)
    
    # Mock provider is already registered
    # Re-setup fallback chain after registering all providers
    proxy._setup_fallback_chain()
    
    # Should fallback to mock provider
    response = await proxy.call(
        prompt="Test prompt",
        provider="primary",
        model="test-model"
    )
    
    # Should have fallback content from mock provider
    # The provider field still shows "primary" but content is from mock
    assert "Mock response" in response.content  # Content from mock provider
    # Could also check for fallback metadata if it was added


@pytest.mark.asyncio
async def test_manual_circuit_reset():
    """Test manual circuit breaker reset."""
    config = ProxyConfig(
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=2,
        max_retries=0,
        enable_fallback=False  # Disable fallback to test circuit reset
    )
    proxy = AIProxy(config)
    
    # Register provider that fails initially
    failing_provider = FailingProvider(fail_count=5)
    proxy.register_provider("failing", failing_provider)
    
    # Open circuit
    for i in range(2):
        with pytest.raises(ConnectionError):
            await proxy.call(
                prompt=f"Test prompt {i}",
                provider="failing",
                model="test-model"
            )
    
    # Circuit should be open
    with pytest.raises(CircuitOpenError):
        await proxy.call(
            prompt="Test prompt",
            provider="failing",
            model="test-model"
        )
    
    # Manually reset circuit
    await proxy.reset_circuit_breaker("failing")
    
    # Should be able to call again (will fail due to provider)
    with pytest.raises(ConnectionError):
        await proxy.call(
            prompt="Test prompt",
            provider="failing",
            model="test-model"
        )
    
    # Circuit state should show it's working again
    stats = proxy.get_error_recovery_stats()
    assert stats["circuit_breaker_states"]["failing"]["failure_count"] == 1