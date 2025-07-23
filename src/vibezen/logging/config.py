"""
Logging configuration for VIBEZEN.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field

from .structured_logger import LogLevel, configure_logging, get_logger
from .formatters import JSONFormatter, PrettyFormatter, CompactFormatter
from .handlers import AsyncFileHandler, MetricsHandler, RemoteHandler


@dataclass
class LoggingConfig:
    """Configuration for VIBEZEN logging."""
    
    # General settings
    level: Union[str, LogLevel] = LogLevel.INFO
    format: str = "pretty"  # json, pretty, compact
    
    # Console output
    console_enabled: bool = True
    console_level: Optional[Union[str, LogLevel]] = None
    
    # File output
    file_enabled: bool = True
    file_path: str = "logs/vibezen.log"
    file_level: Optional[Union[str, LogLevel]] = None
    file_max_bytes: int = 100 * 1024 * 1024  # 100MB
    file_backup_count: int = 10
    file_async: bool = True
    
    # Metrics collection
    metrics_enabled: bool = True
    metrics_window_size: int = 300  # 5 minutes
    metrics_max_windows: int = 12   # 1 hour
    
    # Remote logging
    remote_enabled: bool = False
    remote_endpoint: Optional[str] = None
    remote_api_key: Optional[str] = None
    remote_batch_size: int = 100
    remote_flush_interval: float = 5.0
    
    # Per-module log levels
    module_levels: Dict[str, Union[str, LogLevel]] = field(default_factory=dict)
    
    # Structured logging settings
    include_request_id: bool = True
    include_session_id: bool = True
    include_operation: bool = True
    include_metrics: bool = True
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # General settings
        if level := os.getenv('VIBEZEN_LOG_LEVEL'):
            config.level = level
        if format := os.getenv('VIBEZEN_LOG_FORMAT'):
            config.format = format
        
        # Console settings
        config.console_enabled = os.getenv('VIBEZEN_LOG_CONSOLE', 'true').lower() == 'true'
        if console_level := os.getenv('VIBEZEN_LOG_CONSOLE_LEVEL'):
            config.console_level = console_level
        
        # File settings
        config.file_enabled = os.getenv('VIBEZEN_LOG_FILE', 'true').lower() == 'true'
        if file_path := os.getenv('VIBEZEN_LOG_FILE_PATH'):
            config.file_path = file_path
        if file_level := os.getenv('VIBEZEN_LOG_FILE_LEVEL'):
            config.file_level = file_level
        
        # Metrics settings
        config.metrics_enabled = os.getenv('VIBEZEN_LOG_METRICS', 'true').lower() == 'true'
        
        # Remote settings
        config.remote_enabled = os.getenv('VIBEZEN_LOG_REMOTE', 'false').lower() == 'true'
        config.remote_endpoint = os.getenv('VIBEZEN_LOG_REMOTE_ENDPOINT')
        config.remote_api_key = os.getenv('VIBEZEN_LOG_REMOTE_API_KEY')
        
        return config
    
    @classmethod
    def development(cls) -> 'LoggingConfig':
        """Development configuration with pretty output."""
        return cls(
            level=LogLevel.DEBUG,
            format="pretty",
            console_enabled=True,
            file_enabled=True,
            file_path="logs/vibezen-dev.log",
            metrics_enabled=True,
            remote_enabled=False
        )
    
    @classmethod
    def production(cls) -> 'LoggingConfig':
        """Production configuration with JSON output."""
        return cls(
            level=LogLevel.INFO,
            format="json",
            console_enabled=True,
            file_enabled=True,
            file_path="/var/log/vibezen/vibezen.log",
            file_async=True,
            metrics_enabled=True,
            remote_enabled=True
        )
    
    @classmethod
    def testing(cls) -> 'LoggingConfig':
        """Testing configuration with minimal output."""
        return cls(
            level=LogLevel.WARNING,
            format="compact",
            console_enabled=True,
            file_enabled=False,
            metrics_enabled=False,
            remote_enabled=False
        )


def setup_logging(config: Optional[LoggingConfig] = None):
    """
    Setup VIBEZEN logging system.
    
    Args:
        config: Logging configuration (uses env if not provided)
    """
    if config is None:
        config = LoggingConfig.from_env()
    
    # Create formatters
    formatters = {
        'json': JSONFormatter(),
        'pretty': PrettyFormatter(),
        'compact': CompactFormatter()
    }
    formatter = formatters.get(config.format, PrettyFormatter())
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Let handlers filter
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # VIBEZEN logger
    vibezen_logger = logging.getLogger('vibezen')
    vibezen_logger.setLevel(
        getattr(logging, config.level.value.upper() 
                if isinstance(config.level, LogLevel) 
                else config.level.upper())
    )
    vibezen_logger.propagate = False
    vibezen_logger.handlers.clear()
    
    # Console handler
    if config.console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_level = config.console_level or config.level
        console_handler.setLevel(
            getattr(logging, console_level.value.upper() 
                    if isinstance(console_level, LogLevel) 
                    else console_level.upper())
        )
        vibezen_logger.addHandler(console_handler)
    
    # File handler
    if config.file_enabled:
        # Create log directory
        log_dir = Path(config.file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        if config.file_async:
            file_handler = AsyncFileHandler(
                config.file_path,
                max_bytes=config.file_max_bytes,
                backup_count=config.file_backup_count
            )
        else:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                config.file_path,
                maxBytes=config.file_max_bytes,
                backupCount=config.file_backup_count
            )
        
        file_handler.setFormatter(formatter)
        file_level = config.file_level or config.level
        file_handler.setLevel(
            getattr(logging, file_level.value.upper() 
                    if isinstance(file_level, LogLevel) 
                    else file_level.upper())
        )
        vibezen_logger.addHandler(file_handler)
    
    # Metrics handler
    if config.metrics_enabled:
        metrics_handler = MetricsHandler(
            window_size=config.metrics_window_size,
            max_windows=config.metrics_max_windows
        )
        metrics_handler.setLevel(logging.DEBUG)  # Capture all for metrics
        vibezen_logger.addHandler(metrics_handler)
        
        # Store reference for access
        _metrics_handlers['default'] = metrics_handler
    
    # Remote handler
    if config.remote_enabled and config.remote_endpoint and config.remote_api_key:
        remote_handler = RemoteHandler(
            endpoint=config.remote_endpoint,
            api_key=config.remote_api_key,
            batch_size=config.remote_batch_size,
            flush_interval=config.remote_flush_interval
        )
        remote_handler.setFormatter(JSONFormatter())  # Always JSON for remote
        remote_handler.setLevel(logging.INFO)  # Don't send debug to remote
        vibezen_logger.addHandler(remote_handler)
    
    # Configure module-specific levels
    for module_name, level in config.module_levels.items():
        module_logger = logging.getLogger(module_name)
        module_logger.setLevel(
            getattr(logging, level.value.upper() 
                    if isinstance(level, LogLevel) 
                    else level.upper())
        )
    
    # Log startup
    logger = get_logger('vibezen.logging')
    logger.info(
        "VIBEZEN logging initialized",
        config={
            'level': str(config.level),
            'format': config.format,
            'console': config.console_enabled,
            'file': config.file_enabled,
            'metrics': config.metrics_enabled,
            'remote': config.remote_enabled
        }
    )


# Global metrics handler registry
_metrics_handlers: Dict[str, MetricsHandler] = {}


def get_metrics_handler(name: str = 'default') -> Optional[MetricsHandler]:
    """Get metrics handler by name."""
    return _metrics_handlers.get(name)


def get_metrics() -> Dict[str, Any]:
    """Get metrics from all handlers."""
    metrics = {}
    for name, handler in _metrics_handlers.items():
        metrics[name] = handler.get_metrics()
    return metrics


# Convenience functions for common logging patterns
def log_operation_metric(operation: str, duration: float, success: bool = True):
    """Log an operation metric."""
    logger = get_logger('vibezen.metrics')
    logger.metric(f"operation.{operation}.duration", duration, "seconds")
    logger.metric(f"operation.{operation}.{'success' if success else 'failure'}", 1.0)


def log_cache_metric(cache_type: str, hit: bool, duration: float):
    """Log a cache metric."""
    logger = get_logger('vibezen.metrics')
    logger.metric(f"cache.{cache_type}.{'hit' if hit else 'miss'}", 1.0)
    logger.metric(f"cache.{cache_type}.duration", duration, "seconds")


def log_ai_metric(provider: str, model: str, duration: float, tokens: Optional[int] = None):
    """Log an AI call metric."""
    logger = get_logger('vibezen.metrics')
    logger.metric(f"ai.{provider}.{model}.duration", duration, "seconds")
    if tokens:
        logger.metric(f"ai.{provider}.{model}.tokens", float(tokens))


def log_error_metric(operation: str, error_type: str):
    """Log an error metric."""
    logger = get_logger('vibezen.metrics')
    logger.metric(f"error.{operation}.{error_type}", 1.0)