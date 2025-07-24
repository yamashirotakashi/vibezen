# zen-MCP Integration

## Overview

The zen-MCP integration enhances VIBEZEN's quality assurance capabilities by leveraging advanced AI assistance tools. zen-MCP provides deep thinking, code review, challenge mode, and consensus building features that complement VIBEZEN's introspection system.

## Features

### 1. Deep Thinking (thinkdeep)
- Multi-step reasoning for complex problems
- Configurable thinking depth (minimal to max)
- Web search integration for best practices
- Backtracking and revision capabilities

### 2. Code Review (codeview)
- Comprehensive code quality analysis
- Focus area customization (security, performance, maintainability)
- Severity-based issue detection
- Actionable improvement suggestions

### 3. Challenge Mode
- Critical analysis of implementation decisions
- Automatic triggering on low confidence
- Alternative approach suggestions
- Assumption validation

### 4. Consensus Building
- Multi-model evaluation
- Stance-based analysis (for/against/neutral)
- Aggregated recommendations
- Confidence scoring

## Configuration

```python
from vibezen.external.zen_mcp import ZenMCPConfig

config = ZenMCPConfig(
    # Connection settings
    base_url="http://localhost:8080",
    timeout=300,  # 5 minutes for deep thinking
    
    # Model settings
    default_model="gemini-2.5-pro",
    thinking_mode="high",
    temperature=0.7,
    
    # Feature toggles
    enable_challenge=True,
    enable_consensus=True,
    enable_websearch=True,
    
    # Tool-specific settings
    codeview_config={
        "model": "gemini-2.5-pro",
        "focus_areas": ["security", "performance", "maintainability"],
    },
    
    # Cache settings
    enable_cache=True,
    cache_ttl=3600  # 1 hour
)
```

## Usage

### Basic Client Usage

```python
from vibezen.external.zen_mcp import ZenMCPClient

async with ZenMCPClient(config) as client:
    # Code review
    review = await client.codeview(
        code="def process(): return 'result'",
        focus_areas=["security", "performance"]
    )
    
    # Deep thinking
    analysis = await client.thinkdeep(
        problem="How to optimize this algorithm?",
        thinking_mode="high"
    )
    
    # Challenge mode
    challenge = await client.challenge(
        prompt="This is the best approach",
        context="Performance-critical code"
    )
    
    # Consensus building
    consensus = await client.consensus(
        proposal="Should we refactor this module?",
        models=[
            {"model": "gemini-2.5-pro", "stance": "neutral"},
            {"model": "o3-mini", "stance": "neutral"}
        ]
    )
```

### Integration with VIBEZEN

```python
from vibezen.external.zen_mcp import ZenMCPIntegration
from vibezen.core.guard_v2_introspection import VIBEZENGuardV2WithIntrospection

# Create integration
integration = ZenMCPIntegration(config)

# Use with VIBEZEN guard
guard = VIBEZENGuardV2WithIntrospection(
    enable_introspection=True,
    quality_threshold=80.0
)

async with integration:
    # Enhance specification analysis
    enhanced_analysis = await integration.enhance_specification_analysis(
        specification, initial_analysis
    )
    
    # Generate thinking steps
    thinking_steps = await integration.generate_thinking_steps(
        context, min_steps=4
    )
    
    # Review code quality
    quality_report = await integration.review_code_quality(
        code, specification, triggers
    )
    
    # Generate improvement strategy
    strategy = await integration.generate_improvement_strategy(
        code, triggers, quality_score
    )
```

## Integration Points

### 1. Specification Analysis Enhancement
- Augments VIBEZEN's analysis with deep thinking
- Identifies ambiguities and implementation challenges
- Provides implementation recommendations
- Adjusts confidence based on zen-MCP insights

### 2. Thinking Step Generation
- Creates structured thinking steps for Sequential Thinking Engine
- Ensures minimum thinking depth
- Tracks confidence progression
- Integrates with VIBEZEN's thinking trace

### 3. Code Quality Review
- Combines VIBEZEN triggers with zen-MCP analysis
- Provides comprehensive quality assessment
- Generates actionable improvement plans
- Supports consensus building for disputed assessments

### 4. Interactive Improvement
- Generates context-aware improvement prompts
- Challenges low-confidence implementations
- Builds consensus on quality standards
- Tracks improvement progress

## Best Practices

### 1. Model Selection
- Use `gemini-2.5-pro` for deep analysis
- Use `o3-mini` for quick validations
- Configure multiple models for consensus

### 2. Thinking Modes
- `minimal`: Quick checks (0.5% of model capacity)
- `low`: Basic analysis (8%)
- `medium`: Standard analysis (33%)
- `high`: Deep analysis (67%)
- `max`: Exhaustive analysis (100%)

### 3. Caching Strategy
- Enable caching for repeated analyses
- Set appropriate TTL based on code volatility
- Clear cache when specifications change

### 4. Error Handling
- Implement retry logic for network failures
- Fall back to local analysis on zen-MCP errors
- Log all zen-MCP interactions for debugging

## Troubleshooting

### Connection Issues
```python
# Check zen-MCP server status
client = ZenMCPClient(config)
try:
    await client.connect()
    print("Connected successfully")
except ZenMCPConnectionError as e:
    print(f"Connection failed: {e}")
```

### Timeout Errors
- Increase `timeout` in configuration
- Use lower thinking modes for faster response
- Enable caching to avoid repeated analysis

### Low Confidence Results
- Enable challenge mode
- Use consensus with multiple models
- Increase thinking mode depth
- Provide more context in requests

## Performance Considerations

### Latency
- Deep thinking can take 30-60 seconds
- Use caching for repeated analyses
- Batch related requests when possible

### Resource Usage
- Higher thinking modes consume more resources
- Monitor zen-MCP server load
- Implement rate limiting if needed

### Optimization Tips
1. Cache frequently analyzed code patterns
2. Use appropriate thinking modes for each task
3. Batch similar analyses together
4. Enable web search only when needed
5. Configure model-specific optimizations