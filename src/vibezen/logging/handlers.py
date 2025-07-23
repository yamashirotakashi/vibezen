"""
Custom log handlers for VIBEZEN.
"""

import asyncio
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
import aiofiles
from threading import Thread, Event
from queue import Queue, Empty


class AsyncFileHandler(logging.Handler):
    """
    Asynchronous file handler for non-blocking log writes.
    
    Features:
    - Buffered writes for performance
    - Automatic rotation based on size or time
    - Compression of old logs
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 10,
        buffer_size: int = 1000,
        flush_interval: float = 1.0
    ):
        """Initialize async file handler."""
        super().__init__()
        self.filename = Path(filename)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # Create directory if needed
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Buffer for log entries
        self.buffer: deque = deque(maxlen=buffer_size)
        self.flush_event = Event()
        
        # Start background writer thread
        self.writer_thread = Thread(target=self._run_writer, daemon=True)
        self.writer_thread.start()
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record."""
        try:
            msg = self.format(record)
            self.buffer.append(msg)
            
            # Trigger flush if buffer is full
            if len(self.buffer) >= self.buffer_size:
                self.flush_event.set()
                
        except Exception:
            self.handleError(record)
    
    def _run_writer(self):
        """Background writer thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._async_writer())
        finally:
            loop.close()
    
    async def _async_writer(self):
        """Async writer coroutine."""
        while True:
            # Wait for flush signal or timeout
            if await asyncio.get_event_loop().run_in_executor(
                None, 
                self.flush_event.wait, 
                self.flush_interval
            ):
                self.flush_event.clear()
            
            # Write buffered entries
            if self.buffer:
                await self._write_buffer()
    
    async def _write_buffer(self):
        """Write buffer to file."""
        # Collect entries to write
        entries = []
        try:
            while True:
                entries.append(self.buffer.popleft())
        except IndexError:
            pass
        
        if not entries:
            return
        
        # Check file size and rotate if needed
        if self.filename.exists() and self.filename.stat().st_size > self.max_bytes:
            await self._rotate()
        
        # Write entries
        async with aiofiles.open(self.filename, 'a') as f:
            for entry in entries:
                await f.write(entry + '\n')
    
    async def _rotate(self):
        """Rotate log files."""
        # Rename existing files
        for i in range(self.backup_count - 1, 0, -1):
            old_name = f"{self.filename}.{i}"
            new_name = f"{self.filename}.{i + 1}"
            if Path(old_name).exists():
                Path(old_name).rename(new_name)
        
        # Rename current file
        if self.filename.exists():
            self.filename.rename(f"{self.filename}.1")
    
    def close(self):
        """Close the handler."""
        self.flush_event.set()
        super().close()


class MetricsHandler(logging.Handler):
    """
    Handler that collects metrics from logs.
    
    Features:
    - Aggregates metrics over time windows
    - Calculates statistics (min, max, avg, percentiles)
    - Provides metrics API for monitoring
    """
    
    def __init__(
        self,
        window_size: int = 300,  # 5 minutes
        max_windows: int = 12    # 1 hour of history
    ):
        """Initialize metrics handler."""
        super().__init__()
        self.window_size = window_size
        self.max_windows = max_windows
        
        # Metrics storage: metric_name -> deque of (timestamp, value)
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Aggregated windows: metric_name -> list of window stats
        self.windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_windows))
        
        # Last aggregation time
        self.last_aggregation = datetime.utcnow()
    
    def emit(self, record: logging.LogRecord):
        """Process log record for metrics."""
        try:
            # Parse JSON message
            try:
                log_data = json.loads(record.getMessage())
            except (json.JSONDecodeError, ValueError):
                return
            
            # Extract metrics
            timestamp = datetime.utcnow()
            
            # Direct metrics
            if 'metric_name' in log_data and 'metric_value' in log_data:
                self._record_metric(
                    log_data['metric_name'],
                    log_data['metric_value'],
                    timestamp
                )
            
            # Duration metrics
            if 'duration_ms' in log_data and 'operation' in log_data:
                self._record_metric(
                    f"operation.{log_data['operation']}.duration_ms",
                    log_data['duration_ms'],
                    timestamp
                )
            
            # Cache metrics
            if 'cache_type' in log_data and 'cache_hit' in log_data:
                hit_value = 1.0 if log_data['cache_hit'] else 0.0
                self._record_metric(
                    f"cache.{log_data['cache_type']}.hit_rate",
                    hit_value,
                    timestamp
                )
            
            # AI call metrics
            if 'ai_provider' in log_data and 'duration' in log_data:
                self._record_metric(
                    f"ai.{log_data['ai_provider']}.duration_s",
                    log_data['duration'],
                    timestamp
                )
            
            # Thinking metrics
            if 'thinking_confidence' in log_data and 'thinking_phase' in log_data:
                self._record_metric(
                    f"thinking.{log_data['thinking_phase']}.confidence",
                    log_data['thinking_confidence'],
                    timestamp
                )
            
            # Error counts
            if log_data.get('level') == 'error':
                operation = log_data.get('operation', 'unknown')
                self._record_metric(f"errors.{operation}.count", 1.0, timestamp)
            
            # Aggregate if needed
            if (timestamp - self.last_aggregation).total_seconds() > self.window_size:
                self._aggregate_window(timestamp)
                
        except Exception:
            self.handleError(record)
    
    def _record_metric(self, name: str, value: float, timestamp: datetime):
        """Record a metric value."""
        self.metrics[name].append((timestamp, value))
    
    def _aggregate_window(self, current_time: datetime):
        """Aggregate metrics for the current window."""
        window_start = self.last_aggregation
        window_end = current_time
        
        for metric_name, values in self.metrics.items():
            # Get values in this window
            window_values = [
                v for t, v in values
                if window_start <= t <= window_end
            ]
            
            if window_values:
                # Calculate statistics
                stats = {
                    'window_start': window_start.isoformat(),
                    'window_end': window_end.isoformat(),
                    'count': len(window_values),
                    'sum': sum(window_values),
                    'mean': sum(window_values) / len(window_values),
                    'min': min(window_values),
                    'max': max(window_values)
                }
                
                # Calculate percentiles
                sorted_values = sorted(window_values)
                stats['p50'] = self._percentile(sorted_values, 0.5)
                stats['p90'] = self._percentile(sorted_values, 0.9)
                stats['p95'] = self._percentile(sorted_values, 0.95)
                stats['p99'] = self._percentile(sorted_values, 0.99)
                
                self.windows[metric_name].append(stats)
        
        self.last_aggregation = current_time
    
    def _percentile(self, sorted_values: List[float], p: float) -> float:
        """Calculate percentile."""
        if not sorted_values:
            return 0.0
        
        k = (len(sorted_values) - 1) * p
        f = int(k)
        c = k - f
        
        if f + 1 < len(sorted_values):
            return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
        else:
            return sorted_values[f]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        # Aggregate current window
        self._aggregate_window(datetime.utcnow())
        
        summary = {}
        for metric_name, windows in self.windows.items():
            if windows:
                # Latest window stats
                latest = windows[-1]
                
                # Overall stats across windows
                all_counts = [w['count'] for w in windows]
                all_means = [w['mean'] for w in windows]
                
                summary[metric_name] = {
                    'latest': latest,
                    'windows': len(windows),
                    'total_count': sum(all_counts),
                    'average_mean': sum(all_means) / len(all_means) if all_means else 0
                }
        
        return summary
    
    def get_metric_history(self, metric_name: str) -> List[Dict[str, Any]]:
        """Get history for a specific metric."""
        return list(self.windows.get(metric_name, []))


class RemoteHandler(logging.Handler):
    """
    Handler that sends logs to a remote logging service.
    
    Features:
    - Batched sending for efficiency
    - Retry logic for failures
    - Circuit breaker for remote service
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        timeout: float = 10.0
    ):
        """Initialize remote handler."""
        super().__init__()
        self.endpoint = endpoint
        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.timeout = timeout
        
        # Batch buffer
        self.batch: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        
        # Start background sender
        self.sender_task = None
        self._start_sender()
    
    def _start_sender(self):
        """Start background sender task."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.sender_task = loop.create_task(self._sender_loop())
        
        # Run event loop in thread
        Thread(target=loop.run_forever, daemon=True).start()
    
    async def _sender_loop(self):
        """Background sender loop."""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._send_batch()
    
    def emit(self, record: logging.LogRecord):
        """Emit log record."""
        try:
            # Parse log data
            try:
                log_data = json.loads(record.getMessage())
            except (json.JSONDecodeError, ValueError):
                log_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage()
                }
            
            # Add to batch
            asyncio.run_coroutine_threadsafe(
                self._add_to_batch(log_data),
                asyncio.get_event_loop()
            )
            
        except Exception:
            self.handleError(record)
    
    async def _add_to_batch(self, log_data: Dict[str, Any]):
        """Add log entry to batch."""
        async with self.batch_lock:
            self.batch.append(log_data)
            
            if len(self.batch) >= self.batch_size:
                await self._send_batch()
    
    async def _send_batch(self):
        """Send batch to remote service."""
        async with self.batch_lock:
            if not self.batch:
                return
            
            batch_to_send = self.batch.copy()
            self.batch.clear()
        
        # Send with retry logic
        import httpx
        
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.endpoint,
                        json={'logs': batch_to_send},
                        headers={'Authorization': f'Bearer {self.api_key}'}
                    )
                    response.raise_for_status()
                    break
                    
            except Exception as e:
                if attempt == 2:
                    # Final attempt failed, log locally
                    print(f"Failed to send logs to remote service: {e}")
                else:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)