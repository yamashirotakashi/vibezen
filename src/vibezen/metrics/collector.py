"""
Metrics collection system for VIBEZEN
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from contextlib import asynccontextmanager

from .models import (
    MetricType, BaseMetric, LearningMetric, 
    PracticeMetric, SystemMetric
)
from .storage import MetricsStorage


logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and manages metrics from various parts of the system"""
    
    def __init__(self, storage: MetricsStorage):
        self.storage = storage
        self._buffer: List[BaseMetric] = []
        self._buffer_size = 100
        self._flush_interval = 5.0  # seconds
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the metrics collector"""
        if self._running:
            return
            
        self._running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Metrics collector started")
        
    async def stop(self):
        """Stop the metrics collector"""
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
                
        # Flush remaining metrics
        await self._flush_buffer()
        logger.info("Metrics collector stopped")
        
    async def collect_learning_metric(
        self,
        metric_type: MetricType,
        value: float,
        word_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LearningMetric:
        """Collect a learning-related metric"""
        metric = LearningMetric(
            metric_type=metric_type,
            value=value,
            word_id=word_id,
            lesson_id=lesson_id,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        await self._add_to_buffer(metric)
        return metric
        
    async def collect_practice_metric(
        self,
        metric_type: MetricType,
        value: float,
        practice_type: Optional[str] = None,
        exercises_completed: int = 0,
        accuracy_percentage: float = 0.0,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PracticeMetric:
        """Collect a practice-related metric"""
        metric = PracticeMetric(
            metric_type=metric_type,
            value=value,
            practice_type=practice_type,
            exercises_completed=exercises_completed,
            accuracy_percentage=accuracy_percentage,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        await self._add_to_buffer(metric)
        return metric
        
    async def collect_system_metric(
        self,
        metric_type: MetricType,
        value: float,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        duration_ms: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SystemMetric:
        """Collect a system performance metric"""
        metric = SystemMetric(
            metric_type=metric_type,
            value=value,
            component=component,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        await self._add_to_buffer(metric)
        return metric
        
    @asynccontextmanager
    async def measure_duration(
        self,
        metric_type: MetricType,
        component: str,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Context manager to measure operation duration"""
        start_time = datetime.now()
        error_message = None
        success = True
        
        try:
            yield
        except Exception as e:
            error_message = str(e)
            success = False
            raise
        finally:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            await self.collect_system_metric(
                metric_type=metric_type,
                value=duration_ms,
                component=component,
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata=metadata
            )
            
    async def _add_to_buffer(self, metric: BaseMetric):
        """Add metric to buffer"""
        self._buffer.append(metric)
        
        # Flush if buffer is full
        if len(self._buffer) >= self._buffer_size:
            await self._flush_buffer()
            
    async def _flush_buffer(self):
        """Flush metrics buffer to storage"""
        if not self._buffer:
            return
            
        metrics_to_store = self._buffer.copy()
        self._buffer.clear()
        
        try:
            await self.storage.store_metrics(metrics_to_store)
            logger.debug(f"Flushed {len(metrics_to_store)} metrics to storage")
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")
            # Re-add metrics to buffer on failure
            self._buffer.extend(metrics_to_store)
            
    async def _periodic_flush(self):
        """Periodically flush metrics buffer"""
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")