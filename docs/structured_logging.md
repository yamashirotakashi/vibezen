# Structured Logging Documentation

## Overview

VIBEZEN's structured logging system provides comprehensive logging capabilities with rich context, performance metrics, and integration with monitoring systems. It's designed for debugging complex AI workflows and monitoring system health.

## Key Features

### 1. Structured Log Format
- JSON output for machine parsing
- Pretty format for development
- Compact format for production readability

### 2. Contextual Logging
- Request/session tracking
- Operation correlation
- Automatic context propagation

### 3. Performance Metrics
- Operation timing
- Cache hit rates
- AI call statistics
- Custom metrics

### 4. Specialized Loggers
- Sequential Thinking steps
- Circuit Breaker events
- Audit trails
- Security events

## Configuration

### Basic Setup

```python
from vibezen.logging import configure_logging, LogLevel
from vibezen.logging.config import LoggingConfig, setup_logging

# Using environment variables
config = LoggingConfig.from_env()
setup_logging(config)

# Development configuration
config = LoggingConfig.development()
setup_logging(config)

# Production configuration
config = LoggingConfig.production()
setup_logging(config)
```

### Configuration Options

```python
config = LoggingConfig(
    # General settings
    level=LogLevel.INFO,
    format="json",  # json, pretty, compact
    
    # Console output
    console_enabled=True,
    console_level=LogLevel.INFO,
    
    # File output
    file_enabled=True,
    file_path="logs/vibezen.log",
    file_async=True,  # Non-blocking writes
    file_max_bytes=100_000_000,  # 100MB
    file_backup_count=10,
    
    # Metrics
    metrics_enabled=True,
    metrics_window_size=300,  # 5 minutes
    
    # Remote logging
    remote_enabled=True,
    remote_endpoint="https://logs.example.com/api/logs",
    remote_api_key="your-api-key"
)
```

### Environment Variables

- `VIBEZEN_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)
- `VIBEZEN_LOG_FORMAT`: Output format (json, pretty, compact)
- `VIBEZEN_LOG_CONSOLE`: Enable console output (true/false)
- `VIBEZEN_LOG_FILE`: Enable file output (true/false)
- `VIBEZEN_LOG_FILE_PATH`: Log file path
- `VIBEZEN_LOG_METRICS`: Enable metrics collection (true/false)
- `VIBEZEN_LOG_REMOTE`: Enable remote logging (true/false)

## Usage

### Basic Logging

```python
from vibezen.logging import get_logger

logger = get_logger(__name__)

# Standard log levels
logger.debug("Debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error occurred", error=exception)
logger.critical("Critical failure", error=exception)
```

### Contextual Logging

```python
# Set context for all subsequent logs
logger.set_context(
    request_id="req-123",
    session_id="sess-456",
    user_id="user-789",
    service="vibezen-api"
)

# Log with context
logger.info("Processing request", operation="validate_spec")

# Clear context when done
logger.clear_context()
```

### Operation Logging

```python
# Automatic timing and error tracking
with logger.operation("process_specification"):
    # Do work
    result = await process_spec(spec)
    logger.info("Spec processed", lines=len(spec.split('\n')))
    
# Logs:
# - Operation start
# - Operation completion with duration
# - Any errors that occur
```

### Metrics Logging

```python
# Log metrics
logger.metric("api.response_time", 0.234, "seconds")
logger.metric("cache.hit_rate", 0.87)
logger.metric("ai.tokens_used", 1500)

# Convenience methods
logger.log_cache_access(
    cache_type="semantic",
    key="spec_123",
    hit=True,
    duration=0.002
)

logger.log_ai_call(
    provider="openai",
    model="gpt-4",
    prompt_length=500,
    response_length=1200,
    duration=1.5
)

# Get metrics summary
summary = logger.get_metrics_summary()
```

### Specialized Logging

#### Sequential Thinking

```python
logger.log_thinking_step(
    phase="spec_understanding",
    step_number=3,
    thought="Identified implicit requirements...",
    confidence=0.75
)
```

#### Circuit Breaker

```python
logger.log_circuit_breaker_event(
    breaker_name="ai_provider_openai",
    event="opened",
    state="open",
    failure_count=5,
    reason="threshold_exceeded"
)
```

#### Audit Trail

```python
logger.audit(
    action="UPDATE",
    resource="project/vibezen/config",
    result="success",
    user="admin",
    changes={"log_level": "DEBUG"}
)
```

#### Security Events

```python
logger.security(
    event="invalid_api_key",
    severity="medium",
    source_ip="192.168.1.100",
    api_key_prefix="sk-..."
)
```

## Log Formats

### JSON Format

```json
{
  "timestamp": "2025-01-07T12:34:56.789Z",
  "level": "info",
  "logger": "vibezen.workflow",
  "message": "Processing request",
  "request_id": "req-123",
  "operation": "validate_spec",
  "duration_ms": 234.5
}
```

### Pretty Format

```
[2025-01-07T12:34:56.789Z] INFO     vibezen.workflow - Processing request
  Context: request_id=req-123, operation=validate_spec
  Duration: 234.5ms
```

### Compact Format

```
2025-01-07T12:34:56 | INFO | workflow | Processing request | req=req-123 | op=validate_spec | 234.5ms
```

## Decorators

### Operation Decorator

```python
from vibezen.logging import log_operation

@log_operation("calculate_metrics")
async def calculate_metrics(data):
    # Automatically logs start, end, duration, and errors
    return await process_data(data)

@log_operation()  # Uses function name
def sync_operation():
    pass
```

### Error Decorator

```python
from vibezen.logging import log_errors

@log_errors()
async def risky_operation():
    # Errors are automatically logged with stack trace
    pass
```

## Handlers

### Async File Handler

- Non-blocking file writes
- Automatic rotation by size
- Buffered writes for performance
- Compression of old logs (optional)

### Metrics Handler

- Collects metrics from logs
- Calculates statistics over time windows
- Provides API for monitoring systems

### Remote Handler

- Sends logs to external services
- Batched sending for efficiency
- Retry logic with circuit breaker
- Automatic fallback to local storage

## Best Practices

### 1. Use Structured Context

```python
# Good - structured context
logger.info(
    "User action completed",
    user_id=user.id,
    action="update_profile",
    duration_ms=125
)

# Bad - unstructured string
logger.info(f"User {user.id} completed update_profile in 125ms")
```

### 2. Log at Appropriate Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning conditions that might need attention
- **ERROR**: Error conditions that were handled
- **CRITICAL**: Critical failures requiring immediate attention

### 3. Use Operations for Timing

```python
# Good - automatic timing
with logger.operation("database_query"):
    results = await db.query(sql)

# Less ideal - manual timing
start = time.time()
results = await db.query(sql)
logger.info(f"Query took {time.time() - start}s")
```

### 4. Include Relevant Context

```python
# Good - includes context
logger.error(
    "Failed to process file",
    error=e,
    filename=file.name,
    size=file.size,
    user_id=user.id
)

# Bad - minimal context
logger.error(f"Failed: {e}")
```

### 5. Use Metrics for Monitoring

```python
# Track important metrics
logger.metric("task.completion_rate", success_count / total_count)
logger.metric("queue.depth", queue.size())
logger.metric("memory.usage_mb", psutil.Process().memory_info().rss / 1024 / 1024)
```

## Integration with Monitoring

### Prometheus Integration

```python
# Expose metrics endpoint
from vibezen.logging import get_metrics_handler

@app.route("/metrics")
def metrics():
    handler = get_metrics_handler()
    if handler:
        return prometheus_format(handler.get_metrics())
```

### ELK Stack Integration

Configure file output with JSON format:

```python
config = LoggingConfig(
    format="json",
    file_enabled=True,
    file_path="/var/log/vibezen/app.log"
)
```

### CloudWatch Integration

Use remote handler with AWS endpoint:

```python
config = LoggingConfig(
    remote_enabled=True,
    remote_endpoint="https://logs.amazonaws.com/...",
    remote_api_key=aws_credentials
)
```

## Performance Considerations

1. **Async File Writing**: Use `file_async=True` for non-blocking writes
2. **Batched Remote Sending**: Logs are batched before sending to remote services
3. **Metric Aggregation**: Metrics are aggregated in-memory before persistence
4. **Context Copying**: Context is copied per-request to avoid thread safety issues

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration
2. Verify handler is added to logger
3. Check file permissions for file output
4. Ensure formatter is correctly configured

### Performance Issues

1. Enable async file handler
2. Increase batch size for remote logging
3. Reduce log level in production
4. Use compact format for high-volume logs

### Missing Context

1. Ensure context is set before logging
2. Check for context clearing in error paths
3. Use operation context manager for automatic context

### Metrics Not Collected

1. Verify metrics handler is enabled
2. Check metric name format
3. Ensure proper numeric values are logged