"""
Real-time metrics dashboard for VIBEZEN
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import logging

from .models import MetricType
from .storage import MetricsStorage
from .reporter import MetricsReporter


logger = logging.getLogger(__name__)


class MetricsDashboard:
    """Real-time dashboard for monitoring VIBEZEN metrics"""
    
    def __init__(self, storage: MetricsStorage, reporter: MetricsReporter):
        self.storage = storage
        self.reporter = reporter
        self._subscribers: List[asyncio.Queue] = []
        self._update_interval = 5.0  # seconds
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the dashboard update loop"""
        if self._running:
            return
            
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Metrics dashboard started")
        
    async def stop(self):
        """Stop the dashboard"""
        self._running = False
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
                
        # Close all subscriber queues
        for queue in self._subscribers:
            await queue.put(None)  # Sentinel value
            
        logger.info("Metrics dashboard stopped")
        
    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to dashboard updates"""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        
        # Send initial data
        initial_data = await self.get_current_metrics()
        await queue.put(initial_data)
        
        return queue
        
    async def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from dashboard updates"""
        if queue in self._subscribers:
            self._subscribers.remove(queue)
            
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current dashboard metrics"""
        now = datetime.now()
        
        # Define time windows
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        last_week = now - timedelta(weeks=1)
        
        dashboard_data = {
            'timestamp': now.isoformat(),
            'real_time': {},
            'hourly': {},
            'daily': {},
            'weekly': {}
        }
        
        # Get real-time metrics (last 5 minutes)
        recent_metrics = await self.storage.query_metrics(
            start_time=now - timedelta(minutes=5),
            end_time=now
        )
        
        # Calculate real-time stats
        if recent_metrics:
            # Active users
            active_users = len(set(m.user_id for m in recent_metrics if m.user_id))
            dashboard_data['real_time']['active_users'] = active_users
            
            # Current accuracy
            accuracy_metrics = [m for m in recent_metrics if m.metric_type == MetricType.ACCURACY]
            if accuracy_metrics:
                dashboard_data['real_time']['current_accuracy'] = sum(m.value for m in accuracy_metrics) / len(accuracy_metrics)
                
            # System performance
            response_metrics = [m for m in recent_metrics if m.metric_type == MetricType.RESPONSE_TIME]
            if response_metrics:
                dashboard_data['real_time']['avg_response_time'] = sum(m.value for m in response_metrics) / len(response_metrics)
                
        # Get hourly aggregates
        hourly_metrics = {
            'accuracy': await self._get_metric_summary(MetricType.ACCURACY, last_hour, now),
            'sessions': await self._get_metric_summary(MetricType.SESSION_DURATION, last_hour, now),
            'errors': await self._get_metric_summary(MetricType.ERROR_RATE, last_hour, now)
        }
        dashboard_data['hourly'] = hourly_metrics
        
        # Get daily aggregates
        daily_metrics = {
            'words_practiced': await self._get_metric_summary(MetricType.WORDS_PRACTICED, last_day, now),
            'exercises_completed': await self._get_metric_summary(MetricType.EXERCISES_COMPLETED, last_day, now),
            'total_practice_time': await self._get_metric_summary(MetricType.SESSION_DURATION, last_day, now)
        }
        dashboard_data['daily'] = daily_metrics
        
        # Get weekly trends
        weekly_trends = await self._calculate_trends(last_week, now)
        dashboard_data['weekly']['trends'] = weekly_trends
        
        return dashboard_data
        
    async def _get_metric_summary(
        self,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        metrics = await self.storage.query_metrics(
            metric_types=[metric_type],
            start_time=start_time,
            end_time=end_time
        )
        
        if not metrics:
            return {
                'count': 0,
                'total': 0,
                'average': 0,
                'min': 0,
                'max': 0
            }
            
        values = [m.value for m in metrics]
        
        return {
            'count': len(values),
            'total': sum(values),
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }
        
    async def _calculate_trends(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate trend data for the dashboard"""
        trends = {}
        
        # Define metrics to track trends for
        trend_metrics = [
            (MetricType.ACCURACY, 'accuracy'),
            (MetricType.SPEED, 'speed'),
            (MetricType.SESSION_DURATION, 'engagement')
        ]
        
        for metric_type, key in trend_metrics:
            # Get daily aggregates for the period
            daily_data = await self.storage.aggregate_metrics(
                metric_type,
                MetricPeriod.DAILY,
                start_time,
                end_time
            )
            
            if len(daily_data) >= 2:
                # Calculate trend (comparing first half to second half)
                mid_point = len(daily_data) // 2
                first_half_avg = sum(d.average for d in daily_data[:mid_point]) / mid_point
                second_half_avg = sum(d.average for d in daily_data[mid_point:]) / (len(daily_data) - mid_point)
                
                change_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                
                trends[key] = {
                    'direction': 'up' if change_percent > 0 else 'down' if change_percent < 0 else 'stable',
                    'change_percent': abs(change_percent),
                    'current_value': second_half_avg
                }
            else:
                trends[key] = {
                    'direction': 'stable',
                    'change_percent': 0,
                    'current_value': daily_data[0].average if daily_data else 0
                }
                
        return trends
        
    async def _update_loop(self):
        """Continuously update dashboard data"""
        while self._running:
            try:
                # Get updated metrics
                metrics_data = await self.get_current_metrics()
                
                # Send to all subscribers
                for queue in self._subscribers[:]:  # Copy list to avoid modification during iteration
                    try:
                        # Non-blocking put with timeout
                        await asyncio.wait_for(
                            queue.put(metrics_data),
                            timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        # Remove slow subscribers
                        logger.warning("Removing slow dashboard subscriber")
                        self._subscribers.remove(queue)
                    except Exception as e:
                        logger.error(f"Error sending dashboard update: {e}")
                        
                # Wait before next update
                await asyncio.sleep(self._update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(self._update_interval)