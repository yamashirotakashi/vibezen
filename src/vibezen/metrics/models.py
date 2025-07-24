"""
Metrics data models and types for VIBEZEN
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


class MetricType(Enum):
    """Types of metrics collected by the system"""
    # Learning metrics
    ACCURACY = "accuracy"
    SPEED = "speed"
    RETENTION = "retention"
    PROGRESS = "progress"
    
    # Practice metrics
    SESSION_DURATION = "session_duration"
    WORDS_PRACTICED = "words_practiced"
    EXERCISES_COMPLETED = "exercises_completed"
    STREAK_DAYS = "streak_days"
    
    # System metrics
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    API_CALLS = "api_calls"
    CACHE_HITS = "cache_hits"


class MetricPeriod(Enum):
    """Time periods for metric aggregation"""
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class BaseMetric:
    """Base class for all metrics"""
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    value: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class LearningMetric(BaseMetric):
    """Metrics related to learning performance"""
    word_id: Optional[str] = None
    lesson_id: Optional[str] = None
    correct_attempts: int = 0
    total_attempts: int = 0
    time_spent_seconds: float = 0.0
    difficulty_level: Optional[int] = None


@dataclass
class PracticeMetric(BaseMetric):
    """Metrics related to practice sessions"""
    practice_type: Optional[str] = None
    exercises_completed: int = 0
    words_reviewed: List[str] = field(default_factory=list)
    accuracy_percentage: float = 0.0
    session_duration_minutes: float = 0.0


@dataclass
class SystemMetric(BaseMetric):
    """Metrics related to system performance"""
    component: Optional[str] = None
    operation: Optional[str] = None
    duration_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class AggregatedMetric:
    """Aggregated metric data for reporting"""
    metric_type: MetricType
    period: MetricPeriod
    start_time: datetime
    end_time: datetime
    count: int = 0
    sum: float = 0.0
    average: float = 0.0
    minimum: float = 0.0
    maximum: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)