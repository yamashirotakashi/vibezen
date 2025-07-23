"""
Integration tests for real AI providers.

These tests require API keys to be set in environment variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_API_KEY
"""

import os
import pytest
import asyncio

from vibezen.core.guard_v2 import VIBEZENGuardV2
from vibezen.providers.registry import ProviderRegistry
from vibezen.providers.openai_provider import OpenAIProvider
from vibezen.providers.anthropic_provider import AnthropicProvider
from vibezen.providers.google_provider import GoogleProvider


# Skip tests if no API keys are available
OPENAI_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))
ANTHROPIC_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY"))
GOOGLE_AVAILABLE = bool(os.getenv("GOOGLE_API_KEY"))

# Simple specification for testing
TEST_SPEC = {
    "name": "Calculator Service",
    "description": "A simple calculator that performs basic arithmetic",
    "features": [
        "Addition of two numbers",
        "Subtraction of two numbers",
        "Input validation"
    ],
    "requirements": [
        "All operations should handle decimal numbers",
        "Error messages should be user-friendly",
        "No hardcoded values"
    ]
}


@pytest.mark.integration
@pytest.mark.skipif(not OPENAI_AVAILABLE, reason="OpenAI API key not available")
class TestOpenAIProvider:
    """Test OpenAI provider integration."""
    
    async def test_openai_basic_call(self):
        """Test basic OpenAI API call."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        # Simple prompt test
        response = await guard.ai_proxy.call(
            prompt="Write a haiku about AI",
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        assert response.content
        assert response.provider == "openai"
        assert response.model == "gpt-3.5-turbo"
        assert response.metadata.get("duration") is not None
    
    async def test_openai_thinking_injection(self):
        """Test thinking prompt injection with OpenAI."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        # Test specification understanding
        result = await guard.guide_specification_understanding(
            specification=TEST_SPEC,
            provider="openai",
            model="gpt-4"
        )
        
        assert result["success"]
        assert result["thinking_trace"] is not None
        assert len(result["thinking_trace"].steps) >= 5  # Min steps enforced
        assert result["understanding"]["requirements"]
        assert result["understanding"]["edge_cases"]
    
    async def test_openai_code_generation(self):
        """Test code generation with quality assurance."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        # First understand the spec
        understanding = await guard.guide_specification_understanding(
            specification=TEST_SPEC,
            provider="openai",
            model="gpt-3.5-turbo"
        )
        
        # Then choose approach
        approach = await guard.guide_implementation_choice(
            specification=TEST_SPEC,
            understanding=understanding["understanding"],
            provider="openai",
            model="gpt-3.5-turbo"
        )
        
        # Finally generate code
        result = await guard.guide_implementation(
            specification=TEST_SPEC,
            approach=approach["selected_approach"],
            provider="openai",
            model="gpt-3.5-turbo"
        )
        
        assert result["success"]
        assert result["code"]
        assert "hardcoded" not in result["code"].lower() or len(result["violations"]) > 0


@pytest.mark.integration
@pytest.mark.skipif(not ANTHROPIC_AVAILABLE, reason="Anthropic API key not available")
class TestAnthropicProvider:
    """Test Anthropic provider integration."""
    
    async def test_anthropic_basic_call(self):
        """Test basic Anthropic API call."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        response = await guard.ai_proxy.call(
            prompt="Explain quantum computing in one sentence",
            provider="anthropic",
            model="claude-3-haiku",
            temperature=0.5
        )
        
        assert response.content
        assert response.provider == "anthropic"
        assert response.model == "claude-3-haiku"
    
    async def test_anthropic_thinking_trace(self):
        """Test thinking trace extraction with Claude."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        # Claude is good at structured thinking
        result = await guard.guide_specification_understanding(
            specification=TEST_SPEC,
            provider="anthropic",
            model="claude-3-sonnet"
        )
        
        assert result["success"]
        assert result["thinking_trace"] is not None
        assert result["understanding"]["confidence"] > 0.5


@pytest.mark.integration
@pytest.mark.skipif(not GOOGLE_AVAILABLE, reason="Google API key not available")
class TestGoogleProvider:
    """Test Google provider integration."""
    
    async def test_google_basic_call(self):
        """Test basic Google AI API call."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        response = await guard.ai_proxy.call(
            prompt="What is machine learning?",
            provider="google",
            model="gemini-pro",
            temperature=0.3
        )
        
        assert response.content
        assert response.provider == "google"
        assert response.model == "gemini-pro"
    
    async def test_google_multi_turn(self):
        """Test multi-turn conversation with Gemini."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        # Start a conversation
        result1 = await guard.guide_specification_understanding(
            specification=TEST_SPEC,
            provider="google",
            model="gemini-pro"
        )
        
        # Continue with implementation
        result2 = await guard.guide_implementation_choice(
            specification=TEST_SPEC,
            understanding=result1["understanding"],
            provider="google",
            model="gemini-pro"
        )
        
        assert result1["success"]
        assert result2["success"]
        assert len(result2["approaches"]) > 0


@pytest.mark.integration
class TestMultiProviderConsensus:
    """Test multi-provider consensus building."""
    
    @pytest.mark.skipif(
        not (OPENAI_AVAILABLE and ANTHROPIC_AVAILABLE),
        reason="Multiple API keys required"
    )
    async def test_multi_provider_consensus(self):
        """Test getting consensus from multiple providers."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        approaches = []
        
        # Get approach from OpenAI
        if OPENAI_AVAILABLE:
            result_openai = await guard.guide_implementation_choice(
                specification=TEST_SPEC,
                understanding={"requirements": TEST_SPEC["features"]},
                provider="openai",
                model="gpt-3.5-turbo"
            )
            if result_openai["success"]:
                approaches.extend(result_openai["approaches"])
        
        # Get approach from Anthropic
        if ANTHROPIC_AVAILABLE:
            result_anthropic = await guard.guide_implementation_choice(
                specification=TEST_SPEC,
                understanding={"requirements": TEST_SPEC["features"]},
                provider="anthropic",
                model="claude-3-haiku"
            )
            if result_anthropic["success"]:
                approaches.extend(result_anthropic["approaches"])
        
        # Should have multiple approaches to choose from
        assert len(approaches) >= 2
        
        # Check that approaches are diverse
        approach_names = [a.get("name", "") for a in approaches]
        assert len(set(approach_names)) > 1  # Different approaches


@pytest.mark.integration
class TestProviderFailover:
    """Test provider failover capabilities."""
    
    async def test_provider_failover(self):
        """Test failover to available provider."""
        guard = VIBEZENGuardV2()
        await guard.initialize()
        
        # Try providers in order of preference
        providers = []
        if OPENAI_AVAILABLE:
            providers.append(("openai", "gpt-3.5-turbo"))
        if ANTHROPIC_AVAILABLE:
            providers.append(("anthropic", "claude-3-haiku"))
        if GOOGLE_AVAILABLE:
            providers.append(("google", "gemini-pro"))
        
        if not providers:
            pytest.skip("No AI providers available")
        
        # Try each provider until one works
        result = None
        for provider, model in providers:
            try:
                result = await guard.guide_specification_understanding(
                    specification=TEST_SPEC,
                    provider=provider,
                    model=model
                )
                if result["success"]:
                    break
            except Exception as e:
                print(f"Provider {provider} failed: {e}")
                continue
        
        assert result is not None
        assert result["success"]


# Utility function to run a single test
async def test_single_provider():
    """Utility to test a single provider interactively."""
    guard = VIBEZENGuardV2()
    await guard.initialize()
    
    # Check available providers
    print("Available providers:")
    if OPENAI_AVAILABLE:
        print("- OpenAI")
    if ANTHROPIC_AVAILABLE:
        print("- Anthropic")
    if GOOGLE_AVAILABLE:
        print("- Google")
    
    if not any([OPENAI_AVAILABLE, ANTHROPIC_AVAILABLE, GOOGLE_AVAILABLE]):
        print("No providers available. Set API keys in environment.")
        return
    
    # Test with first available provider
    if OPENAI_AVAILABLE:
        provider, model = "openai", "gpt-3.5-turbo"
    elif ANTHROPIC_AVAILABLE:
        provider, model = "anthropic", "claude-3-haiku"
    else:
        provider, model = "google", "gemini-pro"
    
    print(f"\nTesting with {provider} ({model})...")
    
    result = await guard.guide_specification_understanding(
        specification=TEST_SPEC,
        provider=provider,
        model=model
    )
    
    print("\nResult:")
    print(f"Success: {result['success']}")
    print(f"Thinking steps: {len(result['thinking_trace'].steps) if result['thinking_trace'] else 0}")
    print(f"Requirements found: {len(result['understanding'].get('requirements', []))}")
    print(f"Edge cases: {len(result['understanding'].get('edge_cases', []))}")
    
    if result['thinking_trace']:
        print("\nThinking trace:")
        for step in result['thinking_trace'].steps[:3]:
            print(f"  {step.number}. {step.thought[:100]}...")


if __name__ == "__main__":
    # Run the utility test
    asyncio.run(test_single_provider())