"""
VIBEZEN Introspection module.

Provides trigger-based introspection and quality metrics for AI-generated code.
"""

from vibezen.introspection.triggers import (
    TriggerPriority,
    TriggerType,
    TriggerMatch,
    TriggerPattern,
    HardcodeTrigger,
    ComplexityTrigger,
    SpecificationViolationTrigger,
    TriggerManager,
    IntrospectionEngine,
)

from vibezen.introspection.quality_metrics import (
    QualityGrade,
    ThinkingMetrics,
    CodeQualityMetrics,
    OverallQualityReport,
    ThinkingQualityAnalyzer,
    CodeQualityAnalyzer,
    QualityMetricsEngine,
)

from vibezen.introspection.interactive import (
    IntrospectionState,
    IntrospectionSession,
    IntrospectionDialogue,
    InteractiveIntrospectionSystem,
)

__all__ = [
    # Triggers
    "TriggerPriority",
    "TriggerType",
    "TriggerMatch",
    "TriggerPattern",
    "HardcodeTrigger",
    "ComplexityTrigger",
    "SpecificationViolationTrigger",
    "TriggerManager",
    "IntrospectionEngine",
    
    # Quality Metrics
    "QualityGrade",
    "ThinkingMetrics", 
    "CodeQualityMetrics",
    "OverallQualityReport",
    "ThinkingQualityAnalyzer",
    "CodeQualityAnalyzer",
    "QualityMetricsEngine",
    
    # Interactive System
    "IntrospectionState",
    "IntrospectionSession",
    "IntrospectionDialogue",
    "InteractiveIntrospectionSystem",
]