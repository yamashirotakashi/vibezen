# VIBEZEN Introspection System

## Overview

The VIBEZEN Introspection System is a comprehensive quality improvement framework that detects code issues and guides AI through interactive dialogue to produce higher quality implementations. It combines pattern-based trigger detection, quality metrics analysis, and iterative improvement cycles.

## Key Components

### 1. Trigger System
Pattern-based detection of common code quality issues:

- **Hardcode Detection**: Identifies hardcoded values that should be configurable
- **Complexity Analysis**: Detects overly complex code structures
- **Specification Violations**: Finds mismatches between code and specifications
- **Custom Triggers**: Extensible framework for adding new patterns

### 2. Quality Metrics
Comprehensive quality assessment covering:

- **Thinking Quality**: Depth, revisions, confidence progression
- **Code Quality**: Maintainability, documentation, complexity
- **Overall Grade**: S/A/B/C/D/F rating system

### 3. Interactive Improvement
Dialogue-based refinement process:

- Generates contextual prompts based on detected issues
- Tracks improvement across iterations
- Validates that changes actually improve quality

## Architecture

```
┌─────────────────────┐
│   Code Context      │
│  - Implementation   │
│  - Specification    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Trigger Manager    │
│  - Hardcode         │
│  - Complexity       │
│  - Spec Violations  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Quality Analysis    │
│  - Thinking Metrics │
│  - Code Metrics     │
│  - Overall Score    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Interactive System  │
│  - Prompt Gen       │
│  - AI Dialogue      │
│  - Validation       │
└─────────────────────┘
```

## Usage

### Basic Trigger Detection

```python
from vibezen.introspection import IntrospectionEngine
from vibezen.core.types import CodeContext

# Initialize engine
engine = IntrospectionEngine()

# Analyze code
context = CodeContext(
    code="""
    def process():
        api_key = "sk-1234"  # Hardcoded!
        timeout = 30         # Magic number!
    """
)

triggers = await engine.analyze(context)
for trigger in triggers:
    print(f"{trigger.severity}: {trigger.message}")
```

### Quality Metrics Analysis

```python
from vibezen.introspection import QualityMetricsEngine
from vibezen.core.types import ThinkingStep

# Analyze thinking and code quality
engine = QualityMetricsEngine()

thinking_steps = [
    ThinkingStep(step_number=1, thought="Initial approach", confidence=0.6),
    ThinkingStep(step_number=2, thought="Refined approach", confidence=0.8),
]

report = engine.calculate_overall_quality(thinking_steps, context)
print(f"Grade: {report.quality_grade.value}")
print(f"Score: {report.overall_score}/100")
```

### Interactive Improvement

```python
from vibezen.introspection import InteractiveIntrospectionSystem

# Define AI callback
async def ai_callback(prompt: str) -> str:
    # Your AI integration here
    return improved_code

# Run introspection
system = InteractiveIntrospectionSystem(
    prompt_callback=ai_callback,
    quality_threshold=80.0
)

final_code, report = await system.run_full_introspection(context)
```

### Integration with VIBEZENGuard

```python
from vibezen.core.guard_v2_introspection import VIBEZENGuardV2WithIntrospection

# Initialize guard with introspection
guard = VIBEZENGuardV2WithIntrospection(
    enable_introspection=True,
    introspection_callback=ai_callback,
    quality_threshold=85.0
)

# Guide implementation with automatic improvement
result = await guard.guide_implementation_with_introspection(
    specification, analysis
)

print(f"Final code quality: {result['quality_report'].overall_score}")
```

## Trigger Types

### Hardcode Triggers
Detects various types of hardcoded values:

- **URLs**: `https://example.com`, `localhost:8080`
- **Credentials**: API keys, passwords, secrets
- **Paths**: `/home/user`, `C:\\Windows`
- **Magic Numbers**: Unexplained numeric constants
- **Timeouts**: Hardcoded durations

### Complexity Triggers
Identifies overly complex code:

- **High Cyclomatic Complexity**: Too many decision points
- **Deep Nesting**: Multiple levels of conditionals
- **Long Functions**: Functions doing too much

### Specification Violations
Finds mismatches with requirements:

- **Missing Functionality**: Required features not implemented
- **Extra Functionality**: Unspecified features added
- **Naming Mismatches**: Inconsistent with specification

## Quality Metrics

### Thinking Metrics
- **Total Steps**: Number of thinking iterations
- **Max Depth**: Deepest level of reasoning
- **Revision Count**: How often approach was reconsidered
- **Confidence Progression**: How confidence evolved

### Code Metrics
- **Maintainability Index**: Overall code health (0-100)
- **Documentation Coverage**: Ratio of documented code
- **Cyclomatic Complexity**: Decision complexity
- **Test Coverage**: Percentage of tested code

### Quality Grades
- **S (95+)**: Exceptional quality
- **A (85-94)**: Excellent quality
- **B (75-84)**: Good quality
- **C (65-74)**: Acceptable quality
- **D (50-64)**: Poor quality
- **F (<50)**: Failing quality

## Customization

### Adding Custom Triggers

```python
from vibezen.introspection import TriggerPattern, TriggerType

class SecurityTrigger(TriggerPattern):
    def __init__(self):
        super().__init__(
            pattern_id="security_checker",
            description="Detects security issues",
            priority=TriggerPriority.CRITICAL
        )
    
    async def check(self, context: CodeContext):
        # Your detection logic
        return matches

# Register custom trigger
engine.trigger_manager.register_trigger(SecurityTrigger())
```

### Configuring Quality Thresholds

```python
system = InteractiveIntrospectionSystem(
    quality_threshold=90.0,      # Require 90+ score
    min_improvement=10.0         # Each iteration must improve by 10+
)
```

### Custom Prompt Generation

```python
async def custom_prompt_generator(triggers, context):
    # Your custom prompt logic
    return custom_prompt

system.generate_prompt = custom_prompt_generator
```

## Best Practices

### 1. Start with High Priority Issues
Focus on critical and high severity triggers first:
- Security vulnerabilities
- Hardcoded credentials
- Major specification violations

### 2. Iterative Improvement
Don't try to fix everything at once:
- Address 2-3 issues per iteration
- Validate improvements before continuing
- Stop when quality threshold is met

### 3. Context-Aware Suggestions
Provide specific, actionable feedback:
- ❌ "Code is too complex"
- ✅ "Extract lines 15-30 into a separate function called `validate_user_input`"

### 4. Balance Quality vs Time
Set reasonable thresholds:
- Mission-critical code: 85-90
- Standard features: 75-80
- Prototypes: 65-70

## Examples

See the `examples/introspection` directory for complete examples:

- `quality_improvement.py`: Interactive improvement demo
- `trigger_detection.py`: Custom trigger patterns
- `metrics_analysis.py`: Quality metrics calculation

## Troubleshooting

### Low Quality Scores
- Check thinking depth (aim for 3+ steps)
- Ensure adequate documentation
- Reduce cyclomatic complexity
- Add test coverage

### No Triggers Detected
- Verify code context is properly set
- Check trigger enabled status
- Lower confidence thresholds
- Add custom triggers for domain-specific issues

### Improvement Stagnation
- Increase min_improvement threshold
- Provide more specific prompts
- Check if AI is actually making changes
- Consider different trigger types