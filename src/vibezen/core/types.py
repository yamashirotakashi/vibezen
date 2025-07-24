"""
Core type definitions for VIBEZEN.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class IntrospectionTrigger(str, Enum):
    """Triggers for introspection process."""
    HARDCODE_DETECTED = "hardcode_detected"
    COMPLEXITY_HIGH = "complexity_high"
    SPEC_VIOLATION = "spec_violation"
    QUALITY_LOW = "quality_low"
    MOVING_CODE = "moving_code"
    TEST_FOCUSED = "test_focused"


@dataclass
class QualityPattern:
    """Represents a code quality pattern."""
    name: str
    pattern: str
    description: str
    severity: str
    category: str


@dataclass
class DetectionResult:
    """Result of quality detection."""
    pattern_name: str
    file_path: str
    line_number: int
    description: str
    severity: str
    suggestion: str
    metadata: Dict[str, Any]


@dataclass
class AnalysisContext:
    """Context for code analysis."""
    file_path: str
    content: str
    metadata: Optional[Dict[str, Any]] = None