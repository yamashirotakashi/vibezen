"""
VIBEZEN AI Provider Abstraction Layer.

Supports multiple AI providers with a unified interface.
"""

from vibezen.providers.base import AIProvider, ProviderConfig, ProviderCapability
from vibezen.providers.openai_provider import OpenAIProvider
# AnthropicProvider is deliberately excluded from VIBEZEN to avoid self-referential usage
from vibezen.providers.google_provider import GoogleProvider
from vibezen.providers.registry import ProviderRegistry

__all__ = [
    "AIProvider",
    "ProviderConfig",
    "ProviderCapability",
    "OpenAIProvider",
    # "AnthropicProvider",  # Disabled in VIBEZEN
    "GoogleProvider",
    "ProviderRegistry",
]