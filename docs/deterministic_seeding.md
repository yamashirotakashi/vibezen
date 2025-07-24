# Deterministic Seeding in VIBEZEN

## Overview

VIBEZEN implements deterministic seeding to ensure reproducible AI operations across runs. This addresses the critical issue identified in our o3-search analysis where "same commit may pass/fail depending on time of day."

## Why Deterministic Seeding?

Without deterministic seeding:
- 🎲 Challenge/consensus results vary between runs
- 😕 Non-technical users can't trust quality assessments
- 🐛 Debugging becomes difficult when results aren't reproducible
- 📊 Quality metrics become unreliable

With deterministic seeding:
- ✅ Same code + same specification = same quality assessment
- 🔍 Issues are consistently detected across runs
- 📈 Quality improvements can be reliably measured
- 🤝 Non-technical users get consistent feedback

## How It Works

### 1. Seed Generation

Seeds are generated based on:
- **Base seed**: Daily by default, or custom
- **Operation type**: challenge, consensus, thinkdeep, etc.
- **Context**: Code content, specification, parameters

```python
# Daily seed (default)
manager = DeterministicSeedManager()  # Uses today's date

# Custom seed
manager = DeterministicSeedManager(base_seed="my-project-v1")
```

### 2. Automatic Application

When enabled, seeds are automatically applied to all zen-MCP operations:

```python
# Seeds are added to parameters
{
    "_vibezen_seed": 123456789,
    "_vibezen_deterministic": True,
    "temperature": 0.0,  # Set to 0 for determinism
    # ... other parameters
}
```

### 3. Model Ordering

For consensus operations, models are sorted deterministically:

```python
# Before: Random order
models = ["o3-mini", "gemini-2.5-pro", "gpt-4"]

# After: Consistent order
models = ["gemini-2.5-pro", "gpt-4", "o3-mini"]
```

## Configuration

### In vibezen.yaml

```yaml
vibezen:
  integrations:
    zen_mcp:
      deterministic:
        enabled: true              # Enable/disable deterministic mode
        base_seed: null           # null = daily seed, or specify custom
        cache_deterministic_results: true
```

### In Code

```python
from vibezen.external.zen_mcp import ZenMCPClient, ZenMCPConfig

# Enable deterministic mode (default)
config = ZenMCPConfig(
    enable_deterministic=True,
    deterministic_base_seed="my-seed"  # Optional
)
client = ZenMCPClient(config)

# Disable for exploration
client = ZenMCPClient(config, enable_deterministic=False)
```

## Use Cases

### 1. Daily Consistency (Default)

```python
# All runs today get same results
manager = DeterministicSeedManager()
# Base seed: "vibezen_2025-07-24"
```

### 2. Version-Specific Seeds

```python
# Different seeds for different versions
manager = DeterministicSeedManager(base_seed="v1.0.0")
# All v1.0.0 runs get consistent results
```

### 3. Test Reproducibility

```python
# Fixed seed for tests
manager = DeterministicSeedManager(base_seed="test-suite")
# Tests always get same AI responses
```

### 4. Debugging Mode

```python
# Use specific seed to reproduce issue
manager = DeterministicSeedManager(base_seed="debug-issue-123")
```

## Impact on Quality Assessment

### Before (Non-deterministic)
```
Run 1: Quality Score: 72% ✅ "Code looks good"
Run 2: Quality Score: 58% ❌ "Has serious issues"
Run 3: Quality Score: 81% ✅ "Excellent quality"
```

### After (Deterministic)
```
Run 1: Quality Score: 72% ✅ "Code looks good"
Run 2: Quality Score: 72% ✅ "Code looks good"
Run 3: Quality Score: 72% ✅ "Code looks good"
```

## Caching Behavior

Deterministic results are cached for performance:

```python
# First run: Executes AI operation
result1 = await client.challenge("Check this code")  # 2 seconds

# Second run: Uses cache
result2 = await client.challenge("Check this code")  # 0.01 seconds
```

## Testing

Run the deterministic seed tests:

```bash
pytest tests/test_deterministic_seed.py -v
```

Key test scenarios:
- ✅ Same inputs → same seeds
- ✅ Different operations → different seeds
- ✅ Seed caching works correctly
- ✅ Model ordering is consistent
- ✅ Async operations maintain consistency

## Best Practices

1. **Use daily seeds for development** - Balances consistency with freshness
2. **Use fixed seeds for tests** - Ensures test reliability
3. **Document seed usage** - Include seed info in bug reports
4. **Cache deterministic results** - Improves performance
5. **Disable for exploration** - When you want varied perspectives

## Troubleshooting

### Results still vary?

1. Check if deterministic mode is enabled:
```python
print(client.enable_deterministic)  # Should be True
```

2. Verify seed is being applied:
```python
# Enable debug logging
import logging
logging.getLogger("vibezen.core.deterministic_seed").setLevel(logging.DEBUG)
```

3. Check cache status:
```python
stats = manager.get_cache_stats()
print(f"Cache size: {stats['cache_size']}")
print(f"Cached operations: {stats['cached_operations']}")
```

### Need different results?

1. Change the base seed:
```python
manager = DeterministicSeedManager(base_seed="experiment-2")
```

2. Or disable deterministic mode:
```python
client = ZenMCPClient(config, enable_deterministic=False)
```

## Future Enhancements

- [ ] Per-operation seed overrides
- [ ] Seed rotation strategies
- [ ] Deterministic sampling for model selection
- [ ] Seed-based A/B testing support