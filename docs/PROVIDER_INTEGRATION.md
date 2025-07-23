# VIBEZEN Provider Integration Guide

## Overview

VIBEZEN V2 supports multiple AI providers through a unified interface, allowing you to leverage the best capabilities of each provider while maintaining consistent quality assurance.

## Supported Providers

### OpenAI
- **Models**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo, o1-preview
- **API Key**: Set `OPENAI_API_KEY` environment variable
- **Best For**: General purpose, function calling, wide availability
- **Installation**: `pip install openai`

### Anthropic (Disabled)
- **Status**: Anthropic provider is deliberately disabled in VIBEZEN
- **Reason**: To avoid self-referential usage and ensure VIBEZEN uses alternative providers
- **Alternative**: Use OpenAI (GPT-4) or Google (Gemini Pro) for similar capabilities

### Google
- **Models**: Gemini Pro, Gemini Pro Vision, Gemini 1.5 Pro
- **API Key**: Set `GOOGLE_API_KEY` environment variable
- **Best For**: Multi-modal (vision), extremely large context (1M tokens)
- **Installation**: `pip install google-generativeai`

## Configuration

### Environment Setup
```bash
# Set API keys
export OPENAI_API_KEY="your-openai-key"
# export ANTHROPIC_API_KEY="your-anthropic-key"  # Not used in VIBEZEN
export GOOGLE_API_KEY="your-google-key"

# Install provider packages
pip install openai google-generativeai  # anthropic not needed
```

### Using Providers in Code

```python
from vibezen.core.guard_v2 import VIBEZENGuardV2

# Initialize VIBEZEN
guard = VIBEZENGuardV2()
await guard.initialize()

# Use specific provider
result = await guard.guide_implementation(
    specification=spec,
    approach=approach,
    provider="openai",      # or "anthropic", "google"
    model="gpt-4"          # provider-specific model
)
```

## Provider Selection Guide

### When to Use Each Provider

**OpenAI**:
- ✅ Rapid prototyping with GPT-3.5 Turbo
- ✅ Production code generation with GPT-4
- ✅ Function calling and tool use
- ✅ Wide language support

**Anthropic**:
- ✅ Security-critical implementations
- ✅ Complex reasoning tasks
- ✅ Ethical considerations important
- ✅ Large document processing (200K context)

**Google**:
- ✅ Multi-modal tasks (code + images)
- ✅ Extremely large codebases (1M context)
- ✅ Cost-effective at scale
- ✅ Latest Gemini capabilities

### Model Recommendations by Task

| Task | Recommended Model | Provider | Rationale |
|------|------------------|----------|-----------|
| Quick prototyping | gpt-3.5-turbo | OpenAI | Fast, cheap, good enough |
| Production code | gpt-4 | OpenAI | Best code quality |
| Security review | claude-3-opus | Anthropic | Safety-focused |
| Large codebase | gemini-1.5-pro | Google | 1M token context |
| Budget-conscious | claude-3-haiku | Anthropic | Cheapest quality option |

## Multi-Provider Strategies

### 1. Consensus Building
Get multiple perspectives on critical decisions:

```python
# Get approaches from multiple providers
approaches = []

# OpenAI perspective
openai_result = await guard.guide_implementation_choice(
    specification=spec,
    understanding=understanding,
    provider="openai",
    model="gpt-4"
)
approaches.extend(openai_result["approaches"])

# Anthropic perspective
anthropic_result = await guard.guide_implementation_choice(
    specification=spec,
    understanding=understanding,
    provider="anthropic",
    model="claude-3-sonnet"
)
approaches.extend(anthropic_result["approaches"])

# Choose best approach from combined options
```

### 2. Provider Failover
Ensure reliability with automatic failover:

```python
providers = [
    ("openai", "gpt-4"),
    ("anthropic", "claude-3-sonnet"),
    ("google", "gemini-pro")
]

for provider, model in providers:
    try:
        result = await guard.guide_implementation(
            specification=spec,
            approach=approach,
            provider=provider,
            model=model
        )
        if result["success"]:
            break
    except Exception as e:
        logger.warning(f"Provider {provider} failed: {e}")
        continue
```

### 3. Task-Specific Routing
Route different phases to optimal providers:

```python
# Understanding phase - use model with best reasoning
understanding = await guard.guide_specification_understanding(
    specification=spec,
    provider="anthropic",
    model="claude-3-opus"  # Best for deep understanding
)

# Implementation - use model with best code generation
implementation = await guard.guide_implementation(
    specification=spec,
    approach=approach,
    provider="openai",
    model="gpt-4"  # Best for code quality
)

# Test generation - use cost-effective model
tests = await guard.guide_test_design(
    specification=spec,
    code=implementation["code"],
    provider="google",
    model="gemini-pro"  # Good balance of cost/quality
)
```

## Thinking Trace Extraction

VIBEZEN automatically extracts thinking traces from all providers:

### OpenAI Format
```
Thinking Steps:
1. First, I need to understand...
2. Looking at the requirements...
3. I should consider edge cases...
```

### Anthropic Format
```
<thinking>
Let me break this down step by step...
First consideration...
Second consideration...
</thinking>
```

### Extraction Example
```python
result = await guard.guide_implementation(spec, approach, provider="openai")

if result["thinking_trace"]:
    print(f"AI thought through {len(result['thinking_trace'].steps)} steps")
    for step in result["thinking_trace"].steps:
        print(f"{step.number}. {step.thought}")
```

## Cost Optimization

### Estimated Costs per 1K Tokens

| Model | Input Cost | Output Cost | Best Use Case |
|-------|------------|-------------|---------------|
| gpt-3.5-turbo | $0.001 | $0.002 | Development |
| gpt-4 | $0.03 | $0.06 | Production |
| claude-3-haiku | $0.00025 | $0.00125 | High volume |
| claude-3-sonnet | $0.003 | $0.015 | Balanced |
| claude-3-opus | $0.015 | $0.075 | Critical tasks |
| gemini-pro | $0.0005 | $0.0015 | Large context |

### Cost Reduction Strategies

1. **Use cheaper models for non-critical tasks**:
   ```python
   # Development/testing
   provider="openai", model="gpt-3.5-turbo"
   
   # Production
   provider="openai", model="gpt-4"
   ```

2. **Cache responses for similar specifications**:
   ```python
   # VIBEZEN could implement response caching
   # (Future enhancement)
   ```

3. **Batch similar requests**:
   ```python
   # Process multiple specifications together
   # to reduce overhead
   ```

## Troubleshooting

### Common Issues

**"Provider not initialized"**:
- Check API key is set in environment
- Verify provider package is installed
- Check network connectivity

**"Unknown model"**:
- Verify model name matches exactly
- Check model is available in your region
- Ensure you have access to the model

**"Rate limit exceeded"**:
- Implement exponential backoff
- Use provider failover
- Consider upgrading API tier

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed provider interactions
result = await guard.guide_implementation(...)
```

## Best Practices

1. **Always set temperature appropriately**:
   - Lower (0.0-0.3): Deterministic, production code
   - Medium (0.4-0.7): Balanced creativity
   - Higher (0.8-1.0): Exploratory, diverse options

2. **Use appropriate max_tokens**:
   - Don't set too low (truncated responses)
   - Don't set too high (unnecessary cost)
   - Let VIBEZEN handle defaults

3. **Monitor usage and costs**:
   - Track tokens used per request
   - Set up billing alerts
   - Use cheaper models where appropriate

4. **Handle provider-specific features**:
   - OpenAI: Function calling
   - Anthropic: Constitutional AI
   - Google: Multi-modal inputs

## Example: Production Setup

```python
import os
from vibezen.core.guard_v2 import VIBEZENGuardV2

class ProductionVIBEZEN:
    def __init__(self):
        self.guard = None
        self.primary_provider = ("openai", "gpt-4")
        self.fallback_provider = ("anthropic", "claude-3-sonnet")
        
    async def initialize(self):
        """Initialize with provider validation."""
        self.guard = VIBEZENGuardV2()
        await self.guard.initialize()
        
        # Validate providers
        available = self.guard.provider_registry.get_available_providers()
        if self.primary_provider[0] not in available:
            print(f"Warning: Primary provider {self.primary_provider[0]} not available")
    
    async def generate_with_fallback(self, specification):
        """Generate implementation with automatic fallback."""
        providers = [self.primary_provider, self.fallback_provider]
        
        for provider, model in providers:
            try:
                # Full VIBEZEN workflow
                understanding = await self.guard.guide_specification_understanding(
                    specification, provider=provider, model=model
                )
                
                approach = await self.guard.guide_implementation_choice(
                    specification, understanding["understanding"],
                    provider=provider, model=model
                )
                
                implementation = await self.guard.guide_implementation(
                    specification, approach["selected_approach"],
                    provider=provider, model=model
                )
                
                return implementation
                
            except Exception as e:
                print(f"Provider {provider} failed: {e}")
                if provider == providers[-1][0]:
                    raise
                print(f"Falling back to {providers[1][0]}")

# Usage
vibezen = ProductionVIBEZEN()
await vibezen.initialize()
result = await vibezen.generate_with_fallback(spec)
```

## Future Enhancements

1. **Response Caching**: Cache similar prompts to reduce API calls
2. **Load Balancing**: Distribute requests across multiple API keys
3. **Custom Providers**: Plugin architecture for private LLMs
4. **Usage Analytics**: Built-in tracking and reporting
5. **Streaming Support**: Real-time response streaming