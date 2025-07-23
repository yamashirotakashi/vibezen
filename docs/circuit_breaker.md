# Circuit Breaker Pattern Documentation

## Overview

The Circuit Breaker pattern in VIBEZEN provides fault tolerance and graceful degradation for external service calls. It prevents cascading failures and allows the system to continue operating even when some services are unavailable.

## Key Features

### 1. Three-State Design
- **CLOSED**: Normal operation, all calls pass through
- **OPEN**: Service is failing, calls are rejected immediately
- **HALF_OPEN**: Testing if service has recovered

### 2. Intelligent Failure Detection
- Absolute failure count threshold
- Failure rate calculation
- Configurable minimum calls for rate calculation
- Automatic timeout and recovery attempts

### 3. Statistics and Monitoring
- Real-time success/failure tracking
- State change history
- Health score calculation
- Detailed metrics per circuit

## Configuration

### Basic Configuration

```python
from vibezen.recovery import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,          # Open after 5 consecutive failures
    success_threshold=2,          # Close after 2 successes in half-open
    timeout=60.0,                # Try recovery after 60 seconds
    failure_rate_threshold=0.5,   # Open if 50% of calls fail
    min_calls=10,                # Need 10 calls before rate calculation
    reset_timeout=120.0          # Full reset after 2 minutes of inactivity
)
```

### VIBEZEN Presets

```python
from vibezen.recovery import VIBEZENCircuitBreakerPresets

presets = VIBEZENCircuitBreakerPresets()

# Available presets:
- presets.AI_PROVIDER      # For AI API calls (OpenAI, Google, etc.)
- presets.CACHE_SERVICE    # For cache operations
- presets.SEARCH_SERVICE   # For external search (o3-search)
- presets.KNOWLEDGE_GRAPH  # For Knowledge Graph operations
- presets.THINKING_ENGINE  # For Sequential Thinking calls
```

## Usage

### Basic Usage

```python
from vibezen.recovery import CircuitBreaker

# Create circuit breaker
breaker = CircuitBreaker("my_service", config)

# Make protected call
try:
    result = await breaker.call(my_async_function, arg1, arg2)
except CircuitBreakerOpenError:
    # Handle circuit open - use fallback or queue for later
    pass
```

### Manager Pattern

```python
from vibezen.recovery import CircuitBreakerManager

# Create manager
manager = CircuitBreakerManager()

# Get or create breakers
db_breaker = manager.get_breaker("database")
api_breaker = manager.get_breaker("external_api", custom_config)

# Make calls through manager
result = await manager.call("database", fetch_data, user_id)

# Get health status
health = manager.get_circuit_health()
print(f"System health: {health['health_score']:.2f}")
```

### VIBEZEN Integration

```python
from vibezen.recovery import VIBEZENCircuitBreakerIntegration

# Create integration
cb_integration = VIBEZENCircuitBreakerIntegration()
cb_integration.setup_default_breakers()

# Protected call with fallback
result = await cb_integration.protected_call(
    breaker_name="ai_provider_openai",
    func=call_openai,
    prompt="Hello",
    fallback=use_local_model  # Optional fallback function
)

# Get comprehensive health report
report = cb_integration.get_health_report()
for rec in report['recommendations']:
    print(f"- {rec}")
```

## Integration with Workflow

### Automatic Protection

When circuit breakers are enabled in VIBEZEN config, all external calls are automatically protected:

```python
config = VIBEZENConfig(
    enable_circuit_breaker=True,
    # Other settings...
)

integration = VIBEZENWorkflowIntegration(config)

# All AI calls, cache operations, etc. are now protected
```

### Graceful Degradation

Register handlers for service degradation:

```python
# Register degradation handler
async def handle_ai_degradation():
    logger.warning("AI service down, using simplified logic")
    # Switch to rule-based validation
    # Use cached responses
    # Queue for later processing

cb_integration.register_degradation_handler(
    "ai_provider_openai", 
    handle_ai_degradation
)

# Register recovery handler
async def handle_ai_recovery():
    logger.info("AI service recovered")
    # Process queued items
    # Re-enable full features

cb_integration.register_recovery_handler(
    "ai_provider_openai",
    handle_ai_recovery
)
```

## Monitoring and Alerts

### Health Monitoring

```python
# Get current health
health = cb_integration.get_health_report()

if health['health']['health_score'] < 0.8:
    send_alert("System health degraded")

# Check specific circuits
if "thinking_engine" in health['critical_services']:
    logger.error("Critical: Thinking engine is down!")
```

### Export Statistics

```python
# Export to file
manager.export_stats("/tmp/circuit_breaker_stats.json")

# Get stats as JSON
stats_json = manager.export_stats()
```

### Workflow Control

```python
# Check if safe to continue
if not cb_integration.should_continue_workflow():
    logger.error("Pausing workflow due to circuit breaker state")
    return
```

## Best Practices

### 1. Configure Appropriately
- Set thresholds based on service characteristics
- Fast-failing services need lower thresholds
- Critical services might need higher success thresholds

### 2. Always Provide Fallbacks
- Cache for read operations
- Queue for write operations
- Simplified logic for complex operations

### 3. Monitor and Tune
- Review circuit breaker statistics regularly
- Adjust thresholds based on real-world performance
- Set up alerts for circuit state changes

### 4. Test Failure Scenarios
- Simulate service failures in testing
- Verify fallback mechanisms work correctly
- Ensure system degrades gracefully

## Troubleshooting

### Circuit Stuck Open
- Check if service is actually recovered
- Manually reset if needed: `breaker.reset()`
- Review timeout settings

### Too Many False Positives
- Increase failure threshold
- Adjust failure rate threshold
- Increase min_calls for rate calculation

### Slow Recovery
- Decrease timeout duration
- Reduce success threshold
- Check if service recovery is being detected

## Performance Considerations

- Circuit breaker checks are very fast (microseconds)
- No performance impact when circuit is closed
- Failing fast when open actually improves performance
- Statistics collection has minimal overhead

## Future Enhancements

1. **Adaptive Thresholds**: Automatically adjust based on patterns
2. **Predictive Opening**: Open circuit before failures occur
3. **Distributed State**: Share circuit state across instances
4. **Advanced Metrics**: Integration with monitoring systems