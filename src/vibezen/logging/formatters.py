"""
Log formatters for VIBEZEN structured logging.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logs.
    
    Outputs logs as single-line JSON for easy parsing
    by log aggregation systems.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Try to parse the message as JSON first
        try:
            log_data = json.loads(record.getMessage())
        except (json.JSONDecodeError, ValueError):
            # Fallback to standard format
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname.lower(),
                'logger': record.name,
                'message': record.getMessage()
            }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 
                          'funcName', 'levelname', 'levelno', 'lineno', 
                          'module', 'msecs', 'message', 'pathname', 'process',
                          'processName', 'relativeCreated', 'thread', 'threadName',
                          'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data, default=str)


class PrettyFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    
    Formats logs in a colorful, easy-to-read format
    for console output during development.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'METRIC': '\033[34m',     # Blue
        'AUDIT': '\033[37m',      # White
        'SECURITY': '\033[91m',   # Bright Red
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for human readability."""
        # Try to parse JSON message
        try:
            log_data = json.loads(record.getMessage())
            return self._format_structured(record, log_data)
        except (json.JSONDecodeError, ValueError):
            return self._format_standard(record)
    
    def _format_structured(self, record: logging.LogRecord, log_data: Dict[str, Any]) -> str:
        """Format structured log data."""
        # Extract key fields
        timestamp = log_data.get('timestamp', datetime.utcnow().isoformat())
        level = log_data.get('level', record.levelname).upper()
        logger = log_data.get('logger', record.name)
        message = log_data.get('message', '')
        
        # Color for level
        color = self.COLORS.get(level, self.COLORS['INFO'])
        reset = self.COLORS['RESET']
        
        # Format base line
        lines = [f"{color}[{timestamp}] {level:<8}{reset} {logger} - {message}"]
        
        # Add context information
        context_fields = ['request_id', 'session_id', 'operation', 'phase', 
                         'workflow_id', 'service', 'provider']
        context_items = []
        for field in context_fields:
            if field in log_data:
                context_items.append(f"{field}={log_data[field]}")
        
        if context_items:
            lines.append(f"  Context: {', '.join(context_items)}")
        
        # Add metrics
        if 'metric_name' in log_data:
            lines.append(
                f"  Metric: {log_data['metric_name']} = "
                f"{log_data.get('metric_value', 'N/A')} "
                f"{log_data.get('metric_unit', '')}"
            )
        
        # Add duration
        if 'duration_ms' in log_data:
            lines.append(f"  Duration: {log_data['duration_ms']}ms")
        elif 'duration' in log_data:
            lines.append(f"  Duration: {log_data['duration']:.3f}s")
        
        # Add thinking information
        if 'thinking_phase' in log_data:
            lines.append(
                f"  Thinking: Phase={log_data['thinking_phase']}, "
                f"Step={log_data.get('thinking_step', 'N/A')}, "
                f"Confidence={log_data.get('thinking_confidence', 'N/A')}"
            )
        
        # Add circuit breaker info
        if 'circuit_breaker' in log_data:
            lines.append(
                f"  Circuit: {log_data['circuit_breaker']} "
                f"({log_data.get('circuit_state', 'unknown')})"
            )
        
        # Add cache info
        if 'cache_type' in log_data:
            hit_miss = "HIT" if log_data.get('cache_hit') else "MISS"
            lines.append(f"  Cache: {log_data['cache_type']} - {hit_miss}")
        
        # Add error information
        if 'error' in log_data:
            error_info = log_data['error']
            lines.append(f"  {self.COLORS['ERROR']}Error: {error_info.get('type', 'Unknown')} - {error_info.get('message', '')}{reset}")
            if 'traceback' in error_info and error_info['traceback']:
                lines.append("  Traceback:")
                for line in error_info['traceback'].strip().split('\n'):
                    lines.append(f"    {line}")
        
        # Add any additional fields
        skip_fields = {
            'timestamp', 'level', 'logger', 'message', 'request_id', 'session_id',
            'operation', 'phase', 'workflow_id', 'service', 'provider',
            'metric_name', 'metric_value', 'metric_unit', 'duration_ms', 'duration',
            'thinking_phase', 'thinking_step', 'thinking_confidence', 'thinking_thought',
            'circuit_breaker', 'circuit_state', 'circuit_event',
            'cache_type', 'cache_hit', 'cache_key',
            'error', 'ai_provider', 'ai_model', 'prompt_length', 'response_length'
        }
        
        extra_fields = {k: v for k, v in log_data.items() if k not in skip_fields}
        if extra_fields:
            lines.append(f"  Extra: {json.dumps(extra_fields, default=str)}")
        
        return '\n'.join(lines)
    
    def _format_standard(self, record: logging.LogRecord) -> str:
        """Format standard log record."""
        timestamp = datetime.utcnow().isoformat()
        level = record.levelname
        color = self.COLORS.get(level, self.COLORS['INFO'])
        reset = self.COLORS['RESET']
        
        message = f"{color}[{timestamp}] {level:<8}{reset} {record.name} - {record.getMessage()}"
        
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


class CompactFormatter(logging.Formatter):
    """
    Compact formatter for production logs.
    
    Balances between human readability and parseability.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record in compact format."""
        # Try to parse JSON message
        try:
            log_data = json.loads(record.getMessage())
            
            # Build compact format
            parts = [
                log_data.get('timestamp', datetime.utcnow().isoformat())[:19],
                log_data.get('level', record.levelname).upper()[:4],
                log_data.get('logger', record.name).split('.')[-1][:15],
                log_data.get('message', '')[:100]
            ]
            
            # Add key context
            if 'request_id' in log_data:
                parts.append(f"req={log_data['request_id'][:8]}")
            if 'operation' in log_data:
                parts.append(f"op={log_data['operation']}")
            if 'duration_ms' in log_data:
                parts.append(f"{log_data['duration_ms']}ms")
            
            return " | ".join(parts)
            
        except (json.JSONDecodeError, ValueError):
            # Fallback
            return f"{datetime.utcnow().isoformat()[:19]} | {record.levelname[:4]} | {record.name.split('.')[-1][:15]} | {record.getMessage()[:100]}"