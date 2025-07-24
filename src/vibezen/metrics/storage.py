"""
Metrics storage system for VIBEZEN
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import logging

from .models import (
    BaseMetric, LearningMetric, PracticeMetric, 
    SystemMetric, MetricType, MetricPeriod,
    AggregatedMetric
)


logger = logging.getLogger(__name__)


class MetricsStorage:
    """Handles storage and retrieval of metrics"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.metrics_dir = data_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Separate directories for different metric types
        self.learning_dir = self.metrics_dir / "learning"
        self.practice_dir = self.metrics_dir / "practice"
        self.system_dir = self.metrics_dir / "system"
        
        for dir_path in [self.learning_dir, self.practice_dir, self.system_dir]:
            dir_path.mkdir(exist_ok=True)
            
    async def store_metrics(self, metrics: List[BaseMetric]):
        """Store a batch of metrics"""
        # Group metrics by type and date
        grouped = self._group_metrics(metrics)
        
        # Store each group
        tasks = []
        for (metric_type, date_str), group_metrics in grouped.items():
            if isinstance(group_metrics[0], LearningMetric):
                dir_path = self.learning_dir
            elif isinstance(group_metrics[0], PracticeMetric):
                dir_path = self.practice_dir
            else:
                dir_path = self.system_dir
                
            file_path = dir_path / f"{date_str}.jsonl"
            tasks.append(self._append_metrics_to_file(file_path, group_metrics))
            
        await asyncio.gather(*tasks)
        
    async def query_metrics(
        self,
        metric_types: Optional[List[MetricType]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[BaseMetric]:
        """Query metrics based on filters"""
        metrics = []
        
        # Determine which directories to search
        dirs_to_search = [self.learning_dir, self.practice_dir, self.system_dir]
        
        for dir_path in dirs_to_search:
            # Get relevant files
            files = self._get_files_in_range(dir_path, start_time, end_time)
            
            for file_path in files:
                file_metrics = await self._read_metrics_from_file(
                    file_path, metric_types, user_id, limit - len(metrics)
                )
                metrics.extend(file_metrics)
                
                if len(metrics) >= limit:
                    return metrics[:limit]
                    
        return metrics
        
    async def aggregate_metrics(
        self,
        metric_type: MetricType,
        period: MetricPeriod,
        start_time: datetime,
        end_time: datetime,
        user_id: Optional[str] = None
    ) -> List[AggregatedMetric]:
        """Aggregate metrics for reporting"""
        # Query raw metrics
        metrics = await self.query_metrics(
            metric_types=[metric_type],
            start_time=start_time,
            end_time=end_time,
            user_id=user_id
        )
        
        if not metrics:
            return []
            
        # Group by period
        grouped = self._group_by_period(metrics, period)
        
        # Calculate aggregations
        aggregated = []
        for period_key, period_metrics in grouped.items():
            values = [m.value for m in period_metrics]
            
            agg = AggregatedMetric(
                metric_type=metric_type,
                period=period,
                start_time=period_metrics[0].timestamp,
                end_time=period_metrics[-1].timestamp,
                count=len(values),
                sum=sum(values),
                average=sum(values) / len(values),
                minimum=min(values),
                maximum=max(values)
            )
            
            aggregated.append(agg)
            
        return aggregated
        
    async def cleanup_old_metrics(self, days_to_keep: int = 30):
        """Remove metrics older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for dir_path in [self.learning_dir, self.practice_dir, self.system_dir]:
            for file_path in dir_path.glob("*.jsonl"):
                try:
                    # Parse date from filename
                    date_str = file_path.stem
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        file_path.unlink()
                        logger.info(f"Removed old metrics file: {file_path}")
                        
                except Exception as e:
                    logger.error(f"Error cleaning up file {file_path}: {e}")
                    
    def _group_metrics(self, metrics: List[BaseMetric]) -> Dict[tuple, List[BaseMetric]]:
        """Group metrics by type and date"""
        grouped = {}
        
        for metric in metrics:
            date_str = metric.timestamp.strftime("%Y-%m-%d")
            key = (type(metric).__name__, date_str)
            
            if key not in grouped:
                grouped[key] = []
                
            grouped[key].append(metric)
            
        return grouped
        
    def _group_by_period(
        self,
        metrics: List[BaseMetric],
        period: MetricPeriod
    ) -> Dict[str, List[BaseMetric]]:
        """Group metrics by time period"""
        grouped = {}
        
        for metric in metrics:
            if period == MetricPeriod.HOURLY:
                key = metric.timestamp.strftime("%Y-%m-%d %H:00")
            elif period == MetricPeriod.DAILY:
                key = metric.timestamp.strftime("%Y-%m-%d")
            elif period == MetricPeriod.WEEKLY:
                # Get week start date
                week_start = metric.timestamp - timedelta(days=metric.timestamp.weekday())
                key = week_start.strftime("%Y-%m-%d")
            elif period == MetricPeriod.MONTHLY:
                key = metric.timestamp.strftime("%Y-%m")
            else:
                key = metric.timestamp.strftime("%Y")
                
            if key not in grouped:
                grouped[key] = []
                
            grouped[key].append(metric)
            
        return grouped
        
    def _get_files_in_range(
        self,
        dir_path: Path,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> List[Path]:
        """Get metric files within date range"""
        files = []
        
        for file_path in sorted(dir_path.glob("*.jsonl")):
            try:
                date_str = file_path.stem
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if start_time and file_date.date() < start_time.date():
                    continue
                    
                if end_time and file_date.date() > end_time.date():
                    continue
                    
                files.append(file_path)
                
            except Exception:
                continue
                
        return files
        
    async def _append_metrics_to_file(self, file_path: Path, metrics: List[BaseMetric]):
        """Append metrics to a JSONL file"""
        async with aiofiles.open(file_path, 'a') as f:
            for metric in metrics:
                json_data = self._metric_to_json(metric)
                await f.write(json.dumps(json_data) + '\n')
                
    async def _read_metrics_from_file(
        self,
        file_path: Path,
        metric_types: Optional[List[MetricType]],
        user_id: Optional[str],
        limit: int
    ) -> List[BaseMetric]:
        """Read metrics from a JSONL file"""
        metrics = []
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                async for line in f:
                    if len(metrics) >= limit:
                        break
                        
                    try:
                        data = json.loads(line.strip())
                        metric = self._json_to_metric(data)
                        
                        # Apply filters
                        if metric_types and metric.metric_type not in metric_types:
                            continue
                            
                        if user_id and metric.user_id != user_id:
                            continue
                            
                        metrics.append(metric)
                        
                    except Exception as e:
                        logger.error(f"Error parsing metric line: {e}")
                        
        except FileNotFoundError:
            pass
            
        return metrics
        
    def _metric_to_json(self, metric: BaseMetric) -> Dict[str, Any]:
        """Convert metric to JSON-serializable dict"""
        data = {
            'type': type(metric).__name__,
            'metric_type': metric.metric_type.value,
            'timestamp': metric.timestamp.isoformat(),
            'value': metric.value,
            'metadata': metric.metadata,
            'user_id': metric.user_id,
            'session_id': metric.session_id
        }
        
        # Add type-specific fields
        if isinstance(metric, LearningMetric):
            data.update({
                'word_id': metric.word_id,
                'lesson_id': metric.lesson_id,
                'correct_attempts': metric.correct_attempts,
                'total_attempts': metric.total_attempts,
                'time_spent_seconds': metric.time_spent_seconds,
                'difficulty_level': metric.difficulty_level
            })
        elif isinstance(metric, PracticeMetric):
            data.update({
                'practice_type': metric.practice_type,
                'exercises_completed': metric.exercises_completed,
                'words_reviewed': metric.words_reviewed,
                'accuracy_percentage': metric.accuracy_percentage,
                'session_duration_minutes': metric.session_duration_minutes
            })
        elif isinstance(metric, SystemMetric):
            data.update({
                'component': metric.component,
                'operation': metric.operation,
                'duration_ms': metric.duration_ms,
                'success': metric.success,
                'error_message': metric.error_message
            })
            
        return data
        
    def _json_to_metric(self, data: Dict[str, Any]) -> BaseMetric:
        """Convert JSON dict to metric object"""
        # Common fields
        common_kwargs = {
            'metric_type': MetricType(data['metric_type']),
            'timestamp': datetime.fromisoformat(data['timestamp']),
            'value': data['value'],
            'metadata': data.get('metadata', {}),
            'user_id': data.get('user_id'),
            'session_id': data.get('session_id')
        }
        
        # Create appropriate metric type
        metric_class = data['type']
        
        if metric_class == 'LearningMetric':
            return LearningMetric(
                **common_kwargs,
                word_id=data.get('word_id'),
                lesson_id=data.get('lesson_id'),
                correct_attempts=data.get('correct_attempts', 0),
                total_attempts=data.get('total_attempts', 0),
                time_spent_seconds=data.get('time_spent_seconds', 0.0),
                difficulty_level=data.get('difficulty_level')
            )
        elif metric_class == 'PracticeMetric':
            return PracticeMetric(
                **common_kwargs,
                practice_type=data.get('practice_type'),
                exercises_completed=data.get('exercises_completed', 0),
                words_reviewed=data.get('words_reviewed', []),
                accuracy_percentage=data.get('accuracy_percentage', 0.0),
                session_duration_minutes=data.get('session_duration_minutes', 0.0)
            )
        elif metric_class == 'SystemMetric':
            return SystemMetric(
                **common_kwargs,
                component=data.get('component'),
                operation=data.get('operation'),
                duration_ms=data.get('duration_ms', 0.0),
                success=data.get('success', True),
                error_message=data.get('error_message')
            )
        else:
            return BaseMetric(**common_kwargs)