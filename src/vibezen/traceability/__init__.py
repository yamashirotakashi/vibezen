"""
VIBEZEN Traceability Management System.

Provides complete tracking of specification-implementation-test relationships.
"""

from vibezen.traceability.models import (
    SpecificationItem,
    ImplementationItem,
    TestItem,
    TraceLink,
    TraceLinkType,
    TraceabilityStatus,
    TraceabilityMatrix,
)
from vibezen.traceability.tracker import TraceabilityTracker
from vibezen.traceability.analyzer import (
    TraceabilityAnalyzer,
    CoverageReport,
    ImpactAnalysis,
)
from vibezen.traceability.visualizer import TraceabilityVisualizer

__all__ = [
    # Models
    "SpecificationItem",
    "ImplementationItem",
    "TestItem",
    "TraceLink",
    "TraceLinkType",
    "TraceabilityStatus",
    "TraceabilityMatrix",
    # Core components
    "TraceabilityTracker",
    "TraceabilityAnalyzer",
    "TraceabilityVisualizer",
    # Reports
    "CoverageReport",
    "ImpactAnalysis",
]