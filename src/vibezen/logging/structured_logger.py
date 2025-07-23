"""
Structured Logger for VIBEZEN

Provides rich, structured logging with context tracking,
performance metrics, and integration with monitoring systems.
"""

import logging
import time
import asyncio
import json
import traceback
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from contextvars import ContextVar
from functools import wraps
import inspect

# Context variable for request tracking
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


class LogLevel(Enum):
    """Extended log levels for VIBEZEN."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    METRIC = "metric"      # For performance metrics
    AUDIT = "audit"        # For compliance/audit trails
    SECURITY = "security"  # For security events


@dataclass
class LogContext:
    """Context information for structured logging."""
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    service: Optional[str] = None
    operation: Optional[str] = None
    phase: Optional[str] = None
    workflow_id: Optional[str] = None
    thinking_step: Optional[int] = None
    circuit_breaker: Optional[str] = None
    provider: Optional[str] = None
    cache_hit: Optional[bool] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if key == 'extra' and isinstance(value, dict):
                    result.update(value)
                else:
                    result[key] = value
        return result


class StructuredLogger:
    """
    Structured logger with rich context and metrics tracking.
    
    Features:
    - Automatic context propagation
    - Performance metrics
    - Error tracking with stack traces
    - Integration with circuit breakers
    - Async-safe operations
    """
    
    def __init__(self, name: str, level: Union[str, LogLevel] = LogLevel.INFO):
        """Initialize structured logger."""
        self.name = name
        self.logger = logging.getLogger(name)
        self._set_level(level)
        self._handlers: List[logging.Handler] = []
        self._metrics: Dict[str, List[float]] = {}
        
    def _set_level(self, level: Union[str, LogLevel]):
        """Set logging level."""
        if isinstance(level, LogLevel):
            level_name = level.value.upper()
        else:
            level_name = level.upper()
        
        # Map custom levels to standard logging levels
        level_map = {
            'METRIC': logging.INFO,
            'AUDIT': logging.INFO,
            'SECURITY': logging.WARNING
        }
        
        numeric_level = level_map.get(level_name, getattr(logging, level_name, logging.INFO))
        self.logger.setLevel(numeric_level)
    
    def add_handler(self, handler: logging.Handler):
        """Add a log handler."""
        self.logger.addHandler(handler)
        self._handlers.append(handler)
    
    def get_context(self) -> LogContext:
        """Get current logging context."""
        ctx_dict = request_context.get()
        return LogContext(**ctx_dict)
    
    def set_context(self, **kwargs):
        """Set logging context values."""
        current = request_context.get()
        updated = {**current, **kwargs}
        request_context.set(updated)
    
    def clear_context(self):
        """Clear logging context."""
        request_context.set({})
    
    def _format_message(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext] = None,
        error: Optional[Exception] = None,
        duration: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Format log message with context."""
        # Get current context if not provided
        if context is None:
            context = self.get_context()
        
        # Build log entry
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.value,
            'logger': self.name,
            'message': message,
            **context.to_dict(),
            **kwargs
        }
        
        # Add error information
        if error:
            entry['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            }
        
        # Add duration if provided
        if duration is not None:
            entry['duration_ms'] = round(duration * 1000, 2)
        
        return entry
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext] = None,
        error: Optional[Exception] = None,
        duration: Optional[float] = None,
        **kwargs
    ):
        """Internal logging method."""
        entry = self._format_message(level, message, context, error, duration, **kwargs)
        
        # Convert to JSON for structured output
        json_message = json.dumps(entry, default=str)
        
        # Use appropriate logging level
        level_map = {
            LogLevel.DEBUG: self.logger.debug,
            LogLevel.INFO: self.logger.info,
            LogLevel.WARNING: self.logger.warning,
            LogLevel.ERROR: self.logger.error,
            LogLevel.CRITICAL: self.logger.critical,
            LogLevel.METRIC: self.logger.info,
            LogLevel.AUDIT: self.logger.info,
            LogLevel.SECURITY: self.logger.warning
        }
        
        log_func = level_map.get(level, self.logger.info)
        log_func(json_message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, message, error=error, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, error=error, **kwargs)
    
    def metric(self, metric_name: str, value: float, unit: str = "", **kwargs):
        """Log metric."""
        self._log(
            LogLevel.METRIC,
            f"Metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            **kwargs
        )
        
        # Track metric for aggregation
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        self._metrics[metric_name].append(value)
    
    def audit(self, action: str, resource: str, result: str, **kwargs):
        """Log audit event."""
        self._log(
            LogLevel.AUDIT,
            f"Audit: {action} on {resource}",
            audit_action=action,
            audit_resource=resource,
            audit_result=result,
            **kwargs
        )
    
    def security(self, event: str, severity: str, **kwargs):
        """Log security event."""
        self._log(
            LogLevel.SECURITY,
            f"Security: {event}",
            security_event=event,
            security_severity=severity,
            **kwargs
        )
    
    def operation(self, operation_name: str):
        """
        Context manager for logging operations with timing.
        
        Usage:
            with logger.operation("process_request"):
                # Do work
                pass
        """
        return OperationLogger(self, operation_name)
    
    def log_thinking_step(
        self,
        phase: str,
        step_number: int,
        thought: str,
        confidence: float,
        **kwargs
    ):
        """Log Sequential Thinking step."""
        self._log(
            LogLevel.INFO,
            f"Thinking step {step_number} in {phase}",
            thinking_phase=phase,
            thinking_step=step_number,
            thinking_thought=thought[:200] + "..." if len(thought) > 200 else thought,
            thinking_confidence=confidence,
            **kwargs
        )
    
    def log_circuit_breaker_event(
        self,
        breaker_name: str,
        event: str,
        state: str,
        **kwargs
    ):
        """Log circuit breaker event."""
        self._log(
            LogLevel.WARNING if event == "opened" else LogLevel.INFO,
            f"Circuit breaker {breaker_name} {event}",
            circuit_breaker=breaker_name,
            circuit_event=event,
            circuit_state=state,
            **kwargs
        )
    
    def log_cache_access(
        self,
        cache_type: str,
        key: str,
        hit: bool,
        duration: float,
        **kwargs
    ):
        """Log cache access."""
        self._log(
            LogLevel.DEBUG,
            f"Cache {'hit' if hit else 'miss'} for {cache_type}",
            cache_type=cache_type,
            cache_key=key[:50] + "..." if len(key) > 50 else key,
            cache_hit=hit,
            duration=duration,
            **kwargs
        )
    
    def log_ai_call(
        self,
        provider: str,
        model: str,
        prompt_length: int,
        response_length: int,
        duration: float,
        **kwargs
    ):
        """Log AI provider call."""
        self._log(
            LogLevel.INFO,
            f"AI call to {provider}/{model}",
            ai_provider=provider,
            ai_model=model,
            prompt_length=prompt_length,
            response_length=response_length,
            duration=duration,
            **kwargs
        )
    
    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of collected metrics."""
        summary = {}
        for metric_name, values in self._metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'sum': sum(values),
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values)
                }
        return summary


class OperationLogger:
    """Context manager for logging operations with timing."""
    
    def __init__(self, logger: StructuredLogger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
        self.context_backup = None
    
    def __enter__(self):
        """Start operation logging."""
        self.start_time = time.time()
        self.context_backup = request_context.get()
        self.logger.set_context(operation=self.operation_name)
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End operation logging."""
        duration = time.time() - self.start_time
        
        if exc_type:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                error=exc_val,
                duration=duration
            )
        else:
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                duration=duration
            )
            self.logger.metric(f"operation.{self.operation_name}.duration", duration, "seconds")
        
        # Restore context
        request_context.set(self.context_backup)
        return False  # Don't suppress exceptions


# Global logger registry
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger."""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


def configure_logging(
    level: Union[str, LogLevel] = LogLevel.INFO,
    format: str = "json",
    output: str = "console",
    **kwargs
):
    """
    Configure global logging settings.
    
    Args:
        level: Log level
        format: Output format ('json' or 'pretty')
        output: Output destination ('console', 'file', or path)
        **kwargs: Additional configuration options
    """
    from .formatters import JSONFormatter, PrettyFormatter
    
    # Create formatter
    if format == "json":
        formatter = JSONFormatter()
    else:
        formatter = PrettyFormatter()
    
    # Create handler
    if output == "console":
        handler = logging.StreamHandler()
    elif output == "file":
        handler = logging.FileHandler(kwargs.get('filename', 'vibezen.log'))
    else:
        handler = logging.FileHandler(output)
    
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.value.upper() if isinstance(level, LogLevel) else level.upper()))
    root_logger.addHandler(handler)
    
    # Configure VIBEZEN loggers
    vibezen_logger = logging.getLogger('vibezen')
    vibezen_logger.setLevel(getattr(logging, level.value.upper() if isinstance(level, LogLevel) else level.upper()))
    vibezen_logger.propagate = False
    vibezen_logger.addHandler(handler)


# Decorators for common logging patterns
def log_operation(operation_name: Optional[str] = None):
    """Decorator to log function execution."""
    def decorator(func):
        name = operation_name or func.__name__
        logger = get_logger(func.__module__)
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with logger.operation(name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with logger.operation(name):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


def log_errors(logger_name: Optional[str] = None):
    """Decorator to log function errors."""
    def decorator(func):
        logger = get_logger(logger_name or func.__module__)
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in {func.__name__}", error=e)
                    raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in {func.__name__}", error=e)
                    raise
            return sync_wrapper
    return decorator