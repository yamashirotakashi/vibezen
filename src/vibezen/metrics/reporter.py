"""
Metrics reporting and visualization for VIBEZEN
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

from .models import MetricType, MetricPeriod, AggregatedMetric
from .storage import MetricsStorage


logger = logging.getLogger(__name__)


class MetricsReporter:
    """Generates reports and visualizations from collected metrics"""
    
    def __init__(self, storage: MetricsStorage):
        self.storage = storage
        
    async def generate_learning_report(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive learning progress report"""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
            
        report = {
            'user_id': user_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {},
            'daily_progress': [],
            'word_performance': {},
            'practice_stats': {}
        }
        
        # Get accuracy metrics
        accuracy_metrics = await self.storage.aggregate_metrics(
            MetricType.ACCURACY,
            MetricPeriod.DAILY,
            start_date,
            end_date,
            user_id
        )
        
        # Get speed metrics
        speed_metrics = await self.storage.aggregate_metrics(
            MetricType.SPEED,
            MetricPeriod.DAILY,
            start_date,
            end_date,
            user_id
        )
        
        # Get practice session metrics
        session_metrics = await self.storage.aggregate_metrics(
            MetricType.SESSION_DURATION,
            MetricPeriod.DAILY,
            start_date,
            end_date,
            user_id
        )
        
        # Build summary
        if accuracy_metrics:
            report['summary']['average_accuracy'] = sum(m.average for m in accuracy_metrics) / len(accuracy_metrics)
            report['summary']['best_accuracy'] = max(m.maximum for m in accuracy_metrics)
            
        if speed_metrics:
            report['summary']['average_speed'] = sum(m.average for m in speed_metrics) / len(speed_metrics)
            
        if session_metrics:
            report['summary']['total_practice_time'] = sum(m.sum for m in session_metrics)
            report['summary']['average_session_duration'] = sum(m.average for m in session_metrics) / len(session_metrics)
            
        # Build daily progress
        dates = set()
        for metrics in [accuracy_metrics, speed_metrics, session_metrics]:
            for m in metrics:
                dates.add(m.start_time.date())
                
        for date in sorted(dates):
            daily_data = {
                'date': date.isoformat(),
                'accuracy': None,
                'speed': None,
                'practice_time': None
            }
            
            # Find metrics for this date
            for m in accuracy_metrics:
                if m.start_time.date() == date:
                    daily_data['accuracy'] = m.average
                    
            for m in speed_metrics:
                if m.start_time.date() == date:
                    daily_data['speed'] = m.average
                    
            for m in session_metrics:
                if m.start_time.date() == date:
                    daily_data['practice_time'] = m.sum
                    
            report['daily_progress'].append(daily_data)
            
        return report
        
    async def generate_system_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate a system performance report"""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(hours=24)
            
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'performance': {},
            'errors': [],
            'api_usage': {}
        }
        
        # Get response time metrics
        response_metrics = await self.storage.aggregate_metrics(
            MetricType.RESPONSE_TIME,
            MetricPeriod.HOURLY,
            start_date,
            end_date
        )
        
        # Get error rate metrics
        error_metrics = await self.storage.aggregate_metrics(
            MetricType.ERROR_RATE,
            MetricPeriod.HOURLY,
            start_date,
            end_date
        )
        
        # Get API call metrics
        api_metrics = await self.storage.aggregate_metrics(
            MetricType.API_CALLS,
            MetricPeriod.HOURLY,
            start_date,
            end_date
        )
        
        # Build performance summary
        if response_metrics:
            report['performance']['average_response_time'] = sum(m.average for m in response_metrics) / len(response_metrics)
            report['performance']['p95_response_time'] = self._calculate_percentile([m.maximum for m in response_metrics], 95)
            
        if error_metrics:
            report['performance']['error_rate'] = sum(m.average for m in error_metrics) / len(error_metrics)
            
        if api_metrics:
            report['api_usage']['total_calls'] = sum(m.sum for m in api_metrics)
            report['api_usage']['calls_per_hour'] = sum(m.sum for m in api_metrics) / len(api_metrics)
            
        return report
        
    async def generate_weekly_summary(
        self,
        user_id: str,
        week_offset: int = 0
    ) -> Dict[str, Any]:
        """Generate a weekly summary for a user"""
        # Calculate week boundaries
        today = datetime.now().date()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday + (week_offset * 7))
        week_end = week_start + timedelta(days=6)
        
        # Convert to datetime
        start_date = datetime.combine(week_start, datetime.min.time())
        end_date = datetime.combine(week_end, datetime.max.time())
        
        summary = {
            'user_id': user_id,
            'week': {
                'start': week_start.isoformat(),
                'end': week_end.isoformat(),
                'number': week_start.isocalendar()[1]
            },
            'achievements': [],
            'statistics': {},
            'recommendations': []
        }
        
        # Get various metrics for the week
        metrics_to_fetch = [
            (MetricType.ACCURACY, 'accuracy'),
            (MetricType.SPEED, 'speed'),
            (MetricType.WORDS_PRACTICED, 'words_practiced'),
            (MetricType.SESSION_DURATION, 'practice_time'),
            (MetricType.STREAK_DAYS, 'streak')
        ]
        
        for metric_type, key in metrics_to_fetch:
            aggregated = await self.storage.aggregate_metrics(
                metric_type,
                MetricPeriod.WEEKLY,
                start_date,
                end_date,
                user_id
            )
            
            if aggregated:
                summary['statistics'][key] = {
                    'total': aggregated[0].sum,
                    'average': aggregated[0].average,
                    'best': aggregated[0].maximum
                }
                
        # Generate achievements
        if 'accuracy' in summary['statistics']:
            if summary['statistics']['accuracy']['average'] > 0.9:
                summary['achievements'].append({
                    'type': 'accuracy',
                    'title': 'Accuracy Master',
                    'description': 'Maintained over 90% accuracy this week!'
                })
                
        if 'practice_time' in summary['statistics']:
            total_minutes = summary['statistics']['practice_time']['total']
            if total_minutes > 300:  # 5 hours
                summary['achievements'].append({
                    'type': 'dedication',
                    'title': 'Dedicated Learner',
                    'description': f'Practiced for {total_minutes:.0f} minutes this week!'
                })
                
        # Generate recommendations
        if 'accuracy' in summary['statistics'] and summary['statistics']['accuracy']['average'] < 0.7:
            summary['recommendations'].append({
                'type': 'practice',
                'title': 'Focus on Accuracy',
                'description': 'Try slowing down and focusing on getting words right'
            })
            
        if 'practice_time' in summary['statistics'] and summary['statistics']['practice_time']['total'] < 60:
            summary['recommendations'].append({
                'type': 'frequency',
                'title': 'Practice More Often',
                'description': 'Try to practice at least 15 minutes per day'
            })
            
        return summary
        
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value from a list"""
        if not values:
            return 0.0
            
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        
        if index >= len(sorted_values):
            return sorted_values[-1]
            
        return sorted_values[index]
        
    async def export_metrics(
        self,
        output_path: Path,
        metric_types: Optional[List[MetricType]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = 'json'
    ):
        """Export metrics to a file"""
        # Query metrics
        metrics = await self.storage.query_metrics(
            metric_types=metric_types,
            start_time=start_date,
            end_time=end_date
        )
        
        if format == 'json':
            # Convert metrics to JSON
            data = []
            for metric in metrics:
                metric_dict = {
                    'type': type(metric).__name__,
                    'metric_type': metric.metric_type.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'value': metric.value,
                    'metadata': metric.metadata
                }
                data.append(metric_dict)
                
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        elif format == 'csv':
            # Export as CSV
            import csv
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['timestamp', 'type', 'metric_type', 'value', 'user_id'])
                
                # Write data
                for metric in metrics:
                    writer.writerow([
                        metric.timestamp.isoformat(),
                        type(metric).__name__,
                        metric.metric_type.value,
                        metric.value,
                        metric.user_id or ''
                    ])
                    
        logger.info(f"Exported {len(metrics)} metrics to {output_path}")