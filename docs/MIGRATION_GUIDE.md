# VIBEZEN Migration Guide: V1 to V2

## Overview

VIBEZEN V2 represents a complete architectural redesign. This guide helps you migrate from the monitoring-based V1 to the prompt-intervention-based V2.

## Key Differences

### V1 (Monitoring Approach)
- Post-generation validation
- External monitoring of AI output
- Correction attempts after issues detected
- Heavy reliance on pattern matching

### V2 (Prompt Intervention)
- Pre-generation guidance
- Prompt engineering to shape AI behavior
- Prevention through structured thinking
- Context-aware intervention

## Migration Steps

### 1. Update Your Imports

**Old (V1)**:
```python
from vibezen.core.guard import VIBEZENGuard
from vibezen.engine.sequential_thinking import SequentialThinkingEngine
```

**New (V2)**:
```python
from vibezen.core.guard_v2 import VIBEZENGuardV2
from vibezen.proxy.ai_proxy import AIProxy
from vibezen.prompts.template_engine import PromptTemplateEngine
```

### 2. Update Configuration

**Old (vibezen.yaml)**:
```yaml
vibezen:
  defense:
    post_validation:
      enabled: true
      strict_mode: true
  monitoring:
    real_time: true
```

**New (vibezen.yaml)**:
```yaml
vibezen:
  thinking:
    min_steps:
      spec_understanding: 5
      implementation_choice: 4
    confidence_threshold: 0.7
  checkpoints:
    enabled: true
  proxy:
    enable_interception: true
    enable_thinking_prompts: true
```

### 3. Update Your Code

**Old Approach**:
```python
# Initialize guard
guard = VIBEZENGuard(config_path="vibezen.yaml")

# Validate after generation
spec = {"name": "auth_service", "features": ["login", "logout"]}
code = ai_generate_code(spec)  # External AI call

# Post-validation
validation = await guard.validate_implementation(spec, code)
if validation["violations"]:
    # Attempt to fix
    fixed_code = await guard.fix_violations(code, validation["violations"])
```

**New Approach**:
```python
# Initialize guard
guard = VIBEZENGuardV2(config_path="vibezen.yaml")
await guard.initialize()

# Guide through the entire process
spec = {"name": "auth_service", "features": ["login", "logout"]}

# Step 1: Understanding (with thinking injection)
understanding = await guard.guide_specification_understanding(spec)

# Step 2: Implementation choice (with alternatives)
approach = await guard.guide_implementation_choice(spec, understanding)

# Step 3: Implementation (with quality guidelines)
result = await guard.guide_implementation(spec, approach)
code = result["code"]  # Already quality-assured!
```

### 4. Custom Prompt Templates

If you had custom validation rules in V1, convert them to prompt templates in V2:

**Old (Custom Validator)**:
```python
def validate_no_todos(code):
    if "TODO" in code:
        return SpecViolation(
            type=ViolationType.INCOMPLETE,
            description="TODO comments found"
        )
```

**New (Custom Template)**:
```python
from vibezen.prompts.template_engine import PromptTemplate, PromptSection

class NoTodoTemplate(PromptTemplate):
    def build_sections(self):
        return [
            PromptSection(
                name="requirement",
                content="""
IMPORTANT: Do not leave TODO comments in the code.
All functionality must be fully implemented.
If something cannot be implemented, explain why rather than leaving a TODO.
""",
                order=1
            )
        ]

# Register with engine
engine.register_template(NoTodoTemplate())
```

### 5. Provider Integration

V2 supports multiple AI providers through a unified interface:

```python
# Configure providers
guard = VIBEZENGuardV2()
await guard.initialize()

# Use different providers
result_openai = await guard.guide_implementation(
    spec, approach, 
    provider="openai", 
    model="gpt-4"
)

result_anthropic = await guard.guide_implementation(
    spec, approach,
    provider="anthropic", 
    model="claude-3-opus-20240229"
)
```

### 6. Checkpoint Integration

Replace validation hooks with checkpoints:

**Old**:
```python
# Manual validation points
if phase == "pre_implementation":
    if not validate_requirements():
        raise ValidationError("Requirements incomplete")
```

**New**:
```python
# Automatic checkpoint system
# Configured in vibezen.yaml or programmatically
checkpoint_manager.add_checkpoint(Checkpoint(
    name="requirements_complete",
    phase=ThinkingPhase.SPEC_UNDERSTANDING,
    validator=lambda ctx: len(ctx.get("requirements", [])) > 0,
    failure_action="prompt"  # AI will be prompted to complete requirements
))
```

## Testing the Migration

### 1. Verify Prompt Generation
```python
# Test that prompts are being generated correctly
template_engine = PromptTemplateEngine()
prompt = await template_engine.generate_prompt(
    phase=ThinkingPhase.SPEC_UNDERSTANDING,
    context={"specification": spec}
)
assert "think step-by-step" in prompt.lower()
```

### 2. Verify Interception
```python
# Test that AI calls are intercepted
proxy = AIProxy(ProxyConfig(enable_interception=True))
response = await proxy.call(
    prompt="Implement user auth",
    context=ThinkingContext(phase=ThinkingPhase.IMPLEMENTATION, specification=spec)
)
assert response.metadata.get("thinking_prompt_injected") is True
```

### 3. Compare Output Quality
Run the same specification through both V1 and V2 and compare:
- V2 should have fewer violations
- V2 should not have hardcoded values
- V2 should include thinking traces

## Rollback Plan

If you need to rollback to V1:
1. Keep V1 imports available: `from vibezen.core.guard import VIBEZENGuard as V1Guard`
2. Maintain V1 configuration separately: `vibezen-v1.yaml`
3. Use feature flags to switch between versions

## Common Issues and Solutions

### Issue: "No thinking trace in response"
**Solution**: Ensure the AI provider supports multi-step reasoning or use the mock provider for testing.

### Issue: "Prompts are too long"
**Solution**: Adjust `min_steps` in configuration or use more concise templates.

### Issue: "Checkpoints blocking progress"
**Solution**: Lower `confidence_threshold` or disable specific checkpoints during migration.

## Support

For migration support:
1. Check the examples in `/examples/` directory
2. Run integration tests: `pytest tests/integration/test_prompt_intervention.py`
3. Enable debug logging: `VIBEZEN_LOG_LEVEL=DEBUG`

## Timeline

Recommended migration timeline:
1. **Week 1**: Set up V2 in parallel with V1
2. **Week 2**: Migrate non-critical workflows
3. **Week 3**: A/B test V1 vs V2 outputs
4. **Week 4**: Full migration and V1 deprecation