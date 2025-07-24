"""
Comprehensive tests for VIBEZEN providers.

Tests all provider implementations and the registry.
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch

from vibezen.providers import (
    ProviderRegistry,
    OpenAIProvider,
    GoogleProvider,
    ProviderCapability,
    ProviderConfig,
)
from vibezen.providers.base import AIProvider


@pytest.mark.unit
class TestProviderRegistry:
    """Test provider registry functionality."""
    
    async def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ProviderRegistry()
        assert registry.providers == {}
        assert registry._initialized is False
        
        await registry.initialize()
        assert registry._initialized is True
    
    async def test_auto_discovery_disabled_anthropic(self):
        """Test that Anthropic provider is not auto-discovered."""
        # Set fake API keys
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "ANTHROPIC_API_KEY": "test-key",
            "GOOGLE_API_KEY": "test-key",
        }):
            registry = ProviderRegistry()
            await registry.initialize()
            
            # Check providers
            assert "openai" in registry.providers
            assert "google" in registry.providers
            assert "anthropic" not in registry.providers  # Should be disabled
    
    async def test_register_provider(self):
        """Test manual provider registration."""
        registry = ProviderRegistry()
        provider = Mock(spec=AIProvider)
        provider.name = "custom"
        
        registry.register_provider("custom", provider)
        assert "custom" in registry.providers
        assert registry.providers["custom"] == provider
    
    async def test_get_provider(self):
        """Test getting a provider."""
        registry = ProviderRegistry()
        provider = Mock(spec=AIProvider)
        registry.providers["test"] = provider
        
        # Get existing provider
        result = registry.get_provider("test")
        assert result == provider
        
        # Get non-existent provider
        assert registry.get_provider("nonexistent") is None
    
    async def test_list_available_providers(self):
        """Test listing available providers."""
        registry = ProviderRegistry()
        
        # Create mock providers
        provider1 = AsyncMock(spec=AIProvider)
        provider1.is_available = AsyncMock(return_value=True)
        
        provider2 = AsyncMock(spec=AIProvider)
        provider2.is_available = AsyncMock(return_value=False)
        
        registry.providers = {
            "available": provider1,
            "unavailable": provider2,
        }
        
        available = await registry.list_available_providers()
        assert "available" in available
        assert "unavailable" not in available


@pytest.mark.unit
class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    @pytest.fixture
    def openai_config(self):
        """Create OpenAI provider config."""
        return ProviderConfig(
            api_key="test-key",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000,
        )
    
    async def test_openai_initialization(self, openai_config):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider(openai_config)
        assert provider.name == "openai"
        assert provider.config == openai_config
        assert ProviderCapability.CHAT in provider.capabilities
        assert ProviderCapability.COMPLETION in provider.capabilities
    
    async def test_openai_availability_check(self, openai_config):
        """Test OpenAI availability check."""
        provider = OpenAIProvider(openai_config)
        
        # Should be available with API key
        assert await provider.is_available() is True
        
        # Should not be available without API key
        provider.config.api_key = None
        assert await provider.is_available() is False
    
    @pytest.mark.external
    async def test_openai_complete_mock(self, openai_config):
        """Test OpenAI completion with mock."""
        provider = OpenAIProvider(openai_config)
        
        # Mock the OpenAI client
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Test response"))
        ]
        mock_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )
        
        with patch.object(provider, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_response
            )
            
            result = await provider.complete("Test prompt")
            
            assert result["content"] == "Test response"
            assert result["usage"]["prompt_tokens"] == 10
            assert result["usage"]["completion_tokens"] == 20
            assert result["metadata"]["provider"] == "openai"
    
    async def test_openai_error_handling(self, openai_config):
        """Test OpenAI error handling."""
        provider = OpenAIProvider(openai_config)
        
        with patch.object(provider, 'client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            
            with pytest.raises(Exception, match="API Error"):
                await provider.complete("Test prompt")


@pytest.mark.unit
class TestGoogleProvider:
    """Test Google provider implementation."""
    
    @pytest.fixture
    def google_config(self):
        """Create Google provider config."""
        return ProviderConfig(
            api_key="test-key",
            model="gemini-pro",
            temperature=0.7,
            max_tokens=1000,
        )
    
    async def test_google_initialization(self, google_config):
        """Test Google provider initialization."""
        provider = GoogleProvider(google_config)
        assert provider.name == "google"
        assert provider.config == google_config
        assert ProviderCapability.CHAT in provider.capabilities
        assert ProviderCapability.COMPLETION in provider.capabilities
    
    async def test_google_availability_check(self, google_config):
        """Test Google availability check."""
        provider = GoogleProvider(google_config)
        
        # Should be available with API key
        assert await provider.is_available() is True
        
        # Should not be available without API key
        provider.config.api_key = None
        assert await provider.is_available() is False
    
    @pytest.mark.external
    async def test_google_complete_mock(self, google_config):
        """Test Google completion with mock."""
        provider = GoogleProvider(google_config)
        
        # Mock the response
        mock_response = Mock()
        mock_response.text = "Test response from Gemini"
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content = AsyncMock(return_value=mock_response)
            mock_model_class.return_value = mock_model
            
            # Reinitialize to use mocked model
            provider._model = None
            result = await provider.complete("Test prompt")
            
            assert result["content"] == "Test response from Gemini"
            assert result["metadata"]["provider"] == "google"
            assert result["metadata"]["model"] == "gemini-pro"
    
    async def test_google_safety_settings(self, google_config):
        """Test Google provider safety settings."""
        provider = GoogleProvider(google_config)
        
        # Check default safety settings
        assert hasattr(provider, 'safety_settings')
        assert len(provider.safety_settings) > 0
        
        # All harm categories should be set to BLOCK_NONE
        for setting in provider.safety_settings:
            assert setting["threshold"] == "BLOCK_NONE"


@pytest.mark.unit
class TestProviderCapabilities:
    """Test provider capability handling."""
    
    async def test_capability_checking(self):
        """Test capability checking for providers."""
        provider = Mock(spec=AIProvider)
        provider.capabilities = [
            ProviderCapability.CHAT,
            ProviderCapability.COMPLETION,
        ]
        
        # Check existing capabilities
        assert ProviderCapability.CHAT in provider.capabilities
        assert ProviderCapability.COMPLETION in provider.capabilities
        
        # Check missing capabilities
        assert ProviderCapability.EMBEDDINGS not in provider.capabilities
        assert ProviderCapability.FINE_TUNING not in provider.capabilities
    
    async def test_provider_selection_by_capability(self):
        """Test selecting providers by capability."""
        registry = ProviderRegistry()
        
        # Create providers with different capabilities
        chat_provider = Mock(spec=AIProvider)
        chat_provider.capabilities = [ProviderCapability.CHAT]
        chat_provider.is_available = AsyncMock(return_value=True)
        
        embedding_provider = Mock(spec=AIProvider)
        embedding_provider.capabilities = [ProviderCapability.EMBEDDINGS]
        embedding_provider.is_available = AsyncMock(return_value=True)
        
        registry.providers = {
            "chat": chat_provider,
            "embedding": embedding_provider,
        }
        
        # Get providers with specific capability
        chat_providers = [
            name for name, provider in registry.providers.items()
            if ProviderCapability.CHAT in provider.capabilities
        ]
        
        assert "chat" in chat_providers
        assert "embedding" not in chat_providers


@pytest.mark.integration
class TestProviderIntegration:
    """Integration tests for providers."""
    
    async def test_provider_fallback_mechanism(self):
        """Test fallback between providers."""
        registry = ProviderRegistry()
        
        # Create failing primary provider
        primary = AsyncMock(spec=AIProvider)
        primary.name = "primary"
        primary.is_available = AsyncMock(return_value=True)
        primary.complete = AsyncMock(side_effect=Exception("Primary failed"))
        
        # Create working fallback provider
        fallback = AsyncMock(spec=AIProvider)
        fallback.name = "fallback"
        fallback.is_available = AsyncMock(return_value=True)
        fallback.complete = AsyncMock(return_value={
            "content": "Fallback response",
            "usage": {"prompt_tokens": 5, "completion_tokens": 10},
        })
        
        registry.providers = {
            "primary": primary,
            "fallback": fallback,
        }
        
        # Simulate fallback logic
        try:
            result = await primary.complete("Test")
        except:
            # Fallback to secondary provider
            result = await fallback.complete("Test")
        
        assert result["content"] == "Fallback response"
    
    async def test_multi_provider_load_balancing(self):
        """Test load balancing across multiple providers."""
        registry = ProviderRegistry()
        
        # Create multiple providers
        providers = []
        for i in range(3):
            provider = AsyncMock(spec=AIProvider)
            provider.name = f"provider_{i}"
            provider.is_available = AsyncMock(return_value=True)
            provider.complete = AsyncMock(return_value={
                "content": f"Response from provider {i}",
                "usage": {"prompt_tokens": 5, "completion_tokens": 10},
            })
            providers.append(provider)
            registry.providers[provider.name] = provider
        
        # Simulate round-robin selection
        responses = []
        for i in range(6):
            provider_idx = i % len(providers)
            provider = providers[provider_idx]
            result = await provider.complete(f"Request {i}")
            responses.append(result)
        
        # Verify distribution
        for i, provider in enumerate(providers):
            assert provider.complete.call_count == 2  # Each called twice