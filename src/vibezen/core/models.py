"""
Core data models for VIBEZEN.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ConfidenceLevel(float, Enum):
    """Confidence levels for thinking steps."""
    EXPLORING = 0.0
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.85
    ALMOST_CERTAIN = 0.95
    CERTAIN = 1.0


class ThinkingPhase(str, Enum):
    """Phases of thinking process."""
    SPEC_UNDERSTANDING = "spec_understanding"
    IMPLEMENTATION_CHOICE = "implementation_choice"
    IMPLEMENTATION = "implementation"  # Added for backward compatibility
    TEST_DESIGN = "test_design"
    QUALITY_REVIEW = "quality_review"
    OPTIMIZATION = "optimization"
    GUIDE_UNDERSTANDING = "guide_understanding"  # For guide parsing


class ViolationType(str, Enum):
    """Types of specification violations."""
    UNIMPLEMENTED = "unimplemented"
    OVER_IMPLEMENTED = "over_implemented"
    DEVIATION = "deviation"
    HARDCODE = "hardcode"
    COMPLEXITY = "complexity"
    QUALITY = "quality"  # For "moving code" patterns


class Severity(str, Enum):
    """Severity levels for violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ThinkingStep:
    """Represents a single step in the thinking process."""
    step_number: int
    phase: ThinkingPhase
    thought: str
    confidence: float
    revision_of: Optional[int] = None
    branch_from: Optional[int] = None
    branch_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_revision(self) -> bool:
        """Check if this step is a revision of a previous step."""
        return self.revision_of is not None

    def is_branch(self) -> bool:
        """Check if this step is a branch from a previous step."""
        return self.branch_from is not None


@dataclass
class Revision:
    """Represents a revision in the thinking process."""
    original_step: int
    revised_step: int
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Branch:
    """Represents a branch in the thinking process."""
    branch_id: str
    from_step: int
    description: str
    steps: List[ThinkingStep] = field(default_factory=list)
    selected: bool = False


@dataclass
class QualityMetrics:
    """Quality metrics for thinking process."""
    depth_score: float  # 0.0-1.0, based on number of steps
    revision_score: float  # 0.0-1.0, based on self-correction
    branch_score: float  # 0.0-1.0, based on alternatives explored
    confidence_progression: List[float]
    quality_grade: str  # A-F
    thinking_time: float  # seconds
    total_steps: int
    revision_count: int
    branch_count: int

    @property
    def overall_score(self) -> float:
        """Calculate overall quality score."""
        return (
            self.depth_score * 0.3 +
            self.revision_score * 0.3 +
            self.branch_score * 0.4
        )

    def get_grade(self) -> str:
        """Get letter grade based on overall score."""
        score = self.overall_score
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        return "F"


@dataclass
class ThinkingTrace:
    """Complete trace of a thinking process."""
    id: str
    problem: str
    phase: ThinkingPhase
    steps: List[ThinkingStep]
    revisions: List[Revision] = field(default_factory=list)
    branches: List[Branch] = field(default_factory=list)
    final_decision: Optional[str] = None
    confidence: float = 0.0
    quality_metrics: Optional[QualityMetrics] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_final_confidence(self) -> float:
        """Get confidence of the final step."""
        if self.steps:
            return self.steps[-1].confidence
        return 0.0

    def get_step_count(self) -> int:
        """Get total number of steps including branches."""
        count = len(self.steps)
        for branch in self.branches:
            count += len(branch.steps)
        return count


class CodeReference(BaseModel):
    """Reference to a specific location in code."""
    model_config = ConfigDict(extra="forbid")
    
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None

    def __str__(self) -> str:
        if self.line_end and self.line_end != self.line_start:
            return f"{self.file_path}:{self.line_start}-{self.line_end}"
        return f"{self.file_path}:{self.line_start}"


class TestReference(BaseModel):
    """Reference to a test case."""
    model_config = ConfigDict(extra="forbid")
    
    test_file: str
    test_name: str
    test_class: Optional[str] = None


class SpecViolation(BaseModel):
    """Represents a specification violation."""
    model_config = ConfigDict(extra="forbid")
    
    type: ViolationType
    requirement_id: Optional[str] = None
    code_reference: Optional[CodeReference] = None
    description: str
    severity: Severity
    suggested_action: str
    detected_at: datetime = Field(default_factory=datetime.now)


class ThinkingResult(BaseModel):
    """Result of a thinking process."""
    model_config = ConfigDict(extra="forbid")
    
    trace: ThinkingTrace
    violations: List[SpecViolation] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ThinkingContext:
    """Context for thinking process."""
    phase: ThinkingPhase
    specification: Dict[str, Any]
    code: Optional[str] = None
    previous_violations: List[SpecViolation] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptMetadata:
    """Metadata for generated prompts."""
    template_name: str
    phase: ThinkingPhase
    variables_used: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    context_hash: Optional[str] = None