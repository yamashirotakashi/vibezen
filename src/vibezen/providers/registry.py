"""
Provider Registry for managing AI providers.
"""

from typing import Dict, List, Optional, Type
import os
import logging

from vibezen.providers.base import AIProvider, ProviderConfig, ModelInfo, MockProvider


logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for managing AI providers."""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.provider_classes: Dict[str, Type[AIProvider]] = {
            "mock": MockProvider,
        }
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all providers."""
        if self._initialized:
            return
        
        # Auto-discover and initialize providers based on environment
        await self._auto_discover_providers()
        
        # Initialize all registered providers
        for provider in self.providers.values():
            try:
                await provider.initialize()
                logger.info(f"Initialized provider: {provider.config.name}")
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider.config.name}: {e}")
        
        self._initialized = True
    
    async def _auto_discover_providers(self) -> None:
        """Auto-discover providers based on environment variables."""
        # Always include mock provider
        self.register_provider("mock", MockProvider(ProviderConfig(
            name="mock",
            default_model="mock-fast",
        )))
        
        # Check for OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                from vibezen.providers.openai_provider import OpenAIProvider
                self.provider_classes["openai"] = OpenAIProvider
                self.register_provider("openai", OpenAIProvider(ProviderConfig(
                    name="openai",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    organization=os.getenv("OPENAI_ORGANIZATION"),
                    default_model="gpt-4",
                )))
            except ImportError:
                logger.warning("OpenAI API key found but provider not available")
        
        # Anthropic provider is disabled in VIBEZEN
        # This is a deliberate design decision to avoid self-referential usage
        # and ensure VIBEZEN uses alternative providers for AI operations
        if os.getenv("ANTHROPIC_API_KEY"):
            logger.info("Anthropic API key found but provider is disabled in VIBEZEN")
        
        # Check for Google
        if os.getenv("GOOGLE_API_KEY"):
            try:
                from vibezen.providers.google_provider import GoogleProvider
                self.provider_classes["google"] = GoogleProvider
                self.register_provider("google", GoogleProvider(ProviderConfig(
                    name="google",
                    api_key=os.getenv("GOOGLE_API_KEY"),
                    default_model="gemini-pro",
                )))
            except ImportError:
                logger.warning("Google API key found but provider not available")
    
    def register_provider(self, name: str, provider: AIProvider) -> None:
        """Register a provider."""
        self.providers[name] = provider
        logger.info(f"Registered provider: {name}")
    
    def get_provider(self, name: str) -> Optional[AIProvider]:
        """Get a provider by name."""
        return self.providers.get(name)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [
            name for name, provider in self.providers.items()
            if provider.is_available()
        ]
    
    def get_all_models(self) -> List[ModelInfo]:
        """Get all available models across providers."""
        models = []
        for provider in self.providers.values():
            if provider.is_available():
                models.extend(provider.get_models())
        return models
    
    def find_model(self, model_name: str) -> Optional[tuple[str, ModelInfo]]:
        """Find a model by name across all providers."""
        for provider_name, provider in self.providers.items():
            model_info = provider.get_model_info(model_name)
            if model_info:
                return provider_name, model_info
        return None
    
    def get_provider_for_model(self, model_name: str) -> Optional[AIProvider]:
        """Get the provider that supports a specific model."""
        result = self.find_model(model_name)
        if result:
            provider_name, _ = result
            return self.providers.get(provider_name)
        return None
    
    async def create_provider(self, provider_type: str, config: ProviderConfig) -> AIProvider:
        """Create and initialize a new provider."""
        provider_class = self.provider_classes.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        provider = provider_class(config)
        await provider.initialize()
        
        return provider
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        stats = {}
        
        for name, provider in self.providers.items():
            models = provider.get_models()
            stats[name] = {
                "available": provider.is_available(),
                "model_count": len(models),
                "models": [m.name for m in models],
                "capabilities": [c.name for c in provider.config.capabilities],
            }
        
        return stats