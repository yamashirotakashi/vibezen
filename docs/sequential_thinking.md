# Sequential Thinking Engine Documentation

## Overview

The Sequential Thinking Engine is a core component of VIBEZEN that enforces step-by-step analytical thinking in AI systems. It prevents hasty conclusions and ensures thorough analysis before implementation decisions.

## Key Features

### 1. Multi-Step Thinking Process
- Enforces minimum thinking steps per phase
- Continues until confidence threshold is met
- Maximum step limit to prevent infinite loops

### 2. Phase-Based Analysis
The engine supports different thinking phases:
- **Spec Understanding**: Deep analysis of requirements
- **Implementation Choice**: Evaluation of different approaches
- **Code Design**: Architectural and design decisions
- **Quality Check**: Code quality assessment
- **Refinement**: Optimization and improvement

### 3. Confidence Tracking
- Each thinking step includes a confidence score (0.0-1.0)
- Process continues until confidence threshold is reached
- Confidence improvement is tracked across steps

## Configuration

```python
config = {
    'thinking': {
        'min_steps': {
            'spec_understanding': 5,      # Minimum steps for spec analysis
            'implementation_choice': 4,    # Minimum steps for choosing approach
            'code_design': 4,             # Minimum steps for design
            'quality_check': 3,           # Minimum steps for quality check
            'refinement': 2               # Minimum steps for refinement
        },
        'confidence_threshold': 0.7,      # Required confidence level
        'max_steps_per_phase': 10        # Maximum steps to prevent loops
    },
    'thinking_model': 'gpt-4'            # Model to use for thinking
}
```

## Usage

### Basic Usage

```python
from vibezen.thinking import SequentialThinkingEngine, ThinkingContext, ThinkingPhase

# Create engine
engine = SequentialThinkingEngine(config)

# Create context
context = ThinkingContext(
    task="Implement a REST API for user management",
    spec="Users should be able to register, login, and update profiles",
    phase=ThinkingPhase.SPEC_UNDERSTANDING,
    constraints=[
        "Must use JWT for authentication",
        "Support OAuth2 integration",
        "GDPR compliant"
    ]
)

# Execute thinking
result = await engine.think_through_task(context)

# Access results
print(f"Success: {result.success}")
print(f"Confidence: {result.final_confidence}")
print(f"Summary: {result.summary}")
for rec in result.recommendations:
    print(f"- {rec}")
```

### Quality Analysis

```python
# Analyze implementation quality
result = await engine.analyze_implementation_quality(
    spec="Create a function to calculate fibonacci numbers",
    code="""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
)

print(f"Quality confidence: {result.final_confidence}")
print(f"Issues found: {result.warnings}")
```

## Integration with Workflow

The Sequential Thinking Engine is automatically integrated into the VIBEZEN workflow:

### Phase 1: Spec Understanding
```python
# Automatically applied when spec_content is available
if context.get("spec_content"):
    thinking_result = await engine.think_through_task(
        ThinkingContext(
            task="Understand specification",
            spec=context["spec_content"],
            phase=ThinkingPhase.SPEC_UNDERSTANDING
        )
    )
```

### Phase 3: Implementation
```python
# Applied before implementation begins
thinking_result = await engine.think_through_task(
    ThinkingContext(
        task="Choose implementation approach",
        spec=spec,
        phase=ThinkingPhase.IMPLEMENTATION_CHOICE
    )
)
```

### Phase 6: Quality Assurance
```python
# Validates implementation against spec
validation = await engine.analyze_implementation_quality(
    spec=specification,
    code=implementation_code
)
```

## Thinking Step Structure

Each thinking step contains:
- **Step Number**: Sequential identifier
- **Phase**: Current thinking phase
- **Thought**: The analytical content
- **Confidence**: Current confidence level (0.0-1.0)
- **Timestamp**: When the step occurred
- **Requires More Thinking**: Whether to continue

## Metrics and Monitoring

The engine tracks:
- Total thinking sessions
- Average steps per session
- Confidence improvements
- Phase-specific statistics

```python
metrics = engine.get_metrics()
print(f"Total sessions: {metrics['thinking_stats']['total_sessions']}")
print(f"Average steps: {metrics['thinking_stats']['average_steps']}")
```

## Best Practices

1. **Set Appropriate Minimum Steps**
   - Complex tasks need more thinking steps
   - Simple tasks can have lower minimums
   - Adjust based on domain complexity

2. **Configure Confidence Thresholds**
   - Higher thresholds for critical systems (0.8-0.9)
   - Moderate for standard applications (0.7-0.8)
   - Lower for prototypes (0.6-0.7)

3. **Use Constraints Effectively**
   - Provide clear, specific constraints
   - Include both technical and business constraints
   - Constraints guide the thinking process

4. **Monitor Thinking Patterns**
   - Review thinking steps for insights
   - Identify common failure patterns
   - Adjust configuration based on results

## Performance Considerations

- Each thinking step requires an AI call
- Caching is applied to similar thinking contexts
- Balance thoroughness with API costs
- Use phase-appropriate minimum steps

## Troubleshooting

### Thinking Never Completes
- Check max_steps_per_phase setting
- Lower confidence threshold if too high
- Review task complexity

### Low Confidence Results
- Increase minimum steps
- Provide clearer task description
- Add more specific constraints

### Excessive API Calls
- Enable semantic caching
- Reduce minimum steps for simple tasks
- Use confidence threshold wisely