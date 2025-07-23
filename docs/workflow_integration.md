# VIBEZEN Workflow Integration Guide

## Overview

This guide explains how to integrate VIBEZEN with the spec-to-implementation workflow to provide AI coding quality assurance throughout the development process.

## Integration Architecture

```
spec_to_implementation_workflow
           │
           ├── Phase 1: Spec Reading
           │      └── VIBEZEN: Pre-validation
           │
           ├── Phase 2: Task Planning  
           │      └── VIBEZEN: Semantic Understanding
           │
           ├── Phase 3: Implementation
           │      └── VIBEZEN: Real-time Monitoring
           │
           ├── Phase 4: Testing
           │      └── VIBEZEN: Quality Verification
           │
           └── Phase 5: Documentation
                  └── VIBEZEN: Report Generation
```

## Quick Start

### 1. Import the Adapter

```python
from vibezen.integration.workflow_adapter import create_vibezen_adapter
```

### 2. Create VIBEZEN Instance

```python
# Create with default configuration
vibezen = create_vibezen_adapter(enable=True)

# Or with custom configuration
vibezen = create_vibezen_adapter(
    enable=True,
    enable_semantic_cache=True,
    enable_sanitization=True,
    cache_ttl=7200,
    similarity_threshold=0.85,
    primary_provider="openai",
    fallback_providers=["google", "anthropic"]
)
```

### 3. Enhance Workflow Phases

```python
# Original phase function
async def phase_1_read_spec(spec_path):
    # Read specification
    return spec

# Enhanced with VIBEZEN
spec = await vibezen.enhance_phase(1, phase_1_read_spec, spec_path)
```

### 4. Use Protected AI Calls

```python
# Call AI with all VIBEZEN protections
response = await vibezen.call_ai_with_protection(
    prompt="Generate implementation for user authentication",
    provider="openai",
    model="gpt-4"
)
```

## Integration with spec_to_implementation_workflow.py

### Minimal Changes Required

1. **Import VIBEZEN**:
```python
from vibezen.integration.workflow_adapter import create_vibezen_adapter
```

2. **Initialize in main()**:
```python
# Add after argument parsing
vibezen = None
if args.enable_vibezen:
    vibezen = create_vibezen_adapter(enable=True)
```

3. **Wrap Phase Functions**:
```python
# Original
spec = await read_specification(spec_path)

# With VIBEZEN
if vibezen:
    spec = await vibezen.enhance_phase(1, read_specification, spec_path)
else:
    spec = await read_specification(spec_path)
```

4. **Replace AI Calls**:
```python
# Original
response = await call_ai_provider(prompt, provider="openai")

# With VIBEZEN
if vibezen:
    response = await vibezen.call_ai_with_protection(prompt, provider="openai")
else:
    response = await call_ai_provider(prompt, provider="openai")
```

## Features by Phase

### Phase 1: Specification Reading
- **Pre-validation**: Analyzes spec for completeness
- **Context**: Adds validation flags and spec analysis

### Phase 2: Task Planning
- **Semantic Understanding**: Enables semantic caching for similar tasks
- **Context**: Adds task complexity analysis

### Phase 3: Implementation
- **Real-time Monitoring**: Tracks code quality during generation
- **Context**: Enables quality checks (hardcode detection, spec compliance)

### Phase 4: Testing
- **Quality Verification**: Ensures meaningful test generation
- **Context**: Sets coverage targets and test quality checks

### Phase 5: Documentation
- **Report Generation**: Creates comprehensive quality reports
- **Context**: Enables metrics collection

## Configuration Options

### Core Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_caching` | bool | True | Enable response caching |
| `enable_semantic_cache` | bool | True | Enable semantic similarity matching |
| `cache_ttl` | int | 3600 | Cache time-to-live in seconds |
| `similarity_threshold` | float | 0.85 | Minimum similarity for cache hits |

### Error Recovery

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_retry` | bool | True | Enable automatic retries |
| `enable_circuit_breaker` | bool | True | Enable circuit breaker pattern |
| `enable_fallback` | bool | True | Enable provider fallback |
| `max_retries` | int | 3 | Maximum retry attempts |

### Sanitization

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_sanitization` | bool | True | Enable prompt sanitization |
| `block_on_critical_pattern` | bool | True | Block critical injection patterns |
| `pattern_severity_threshold` | float | 0.7 | Minimum severity to trigger action |

### Providers

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `primary_provider` | str | "openai" | Primary AI provider |
| `fallback_providers` | List[str] | ["google", "bedrock"] | Fallback provider order |

## Metrics and Monitoring

### Collecting Metrics

```python
metrics = await vibezen.get_metrics()
print(f"Cache hit rate: {metrics['cache_stats']['hit_rate']}")
print(f"Retry count: {metrics['error_recovery_stats']['retries']}")
print(f"Sanitization blocks: {metrics['sanitization_stats']['blocks']}")
```

### Available Metrics

- **Cache Statistics**:
  - Hit rate
  - Total lookups
  - Evictions
  - Entry count

- **Error Recovery**:
  - Retry attempts
  - Circuit breaker state
  - Fallback usage

- **Sanitization**:
  - Patterns detected
  - Prompts blocked
  - Severity distribution

## Best Practices

1. **Enable Semantic Caching** for repetitive tasks to reduce API calls
2. **Configure Fallback Providers** for high availability
3. **Monitor Metrics** to optimize configuration
4. **Use Validation** at the end of implementation phase
5. **Review Quality Reports** to identify improvement areas

## Troubleshooting

### Cache Not Working
- Check if caching is enabled
- Verify TTL settings
- Monitor cache hit rate

### Fallback Not Triggering
- Ensure fallback providers are configured
- Check circuit breaker state
- Verify provider availability

### Sanitization Too Strict
- Adjust `pattern_severity_threshold`
- Review blocked patterns in metrics
- Consider disabling `block_on_critical_pattern` for testing

## Future Enhancements

As VIBEZEN develops through phases 1-4, additional features will be integrated:

- **Phase 1**: Sequential Thinking Engine for deeper analysis
- **Phase 2**: 3-layer defense system with o3-search integration
- **Phase 3**: Full traceability matrix for spec-implementation-test
- **Phase 4**: Interactive introspection triggers

## Example Integration

See `examples/workflow_integration_example.py` for a complete working example of VIBEZEN integration with mock workflow phases.