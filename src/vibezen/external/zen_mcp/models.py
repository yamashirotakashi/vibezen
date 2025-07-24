"""
Pydantic models for zen-MCP responses.

This module defines strict type definitions for all zen-MCP responses
to ensure type safety and predictable behavior.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ThinkingStepModel(BaseModel):
    """Model for a single thinking step."""
    thought: str = Field(..., description="The thought content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")
    step_number: Optional[int] = Field(None, description="Step number in sequence")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CodeReviewIssue(BaseModel):
    """Model for a code review issue."""
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    type: str = Field(..., description="Issue type")
    message: str = Field(..., description="Issue description")
    location: Optional[str] = Field(None, description="Code location")
    suggestion: Optional[str] = Field(None, description="Fix suggestion")


class ZenMCPBaseResponse(BaseModel):
    """Base response model for all zen-MCP tools."""
    success: bool = Field(True, description="Whether the operation succeeded")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    timestamp: datetime = Field(default_factory=datetime.now)
    model_used: Optional[str] = Field(None, description="Model that generated response")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {v}")
        return v


class ThinkDeepResponse(ZenMCPBaseResponse):
    """Response model for thinkdeep tool."""
    findings: str = Field(..., description="Main findings from deep thinking")
    thinking_steps: List[ThinkingStepModel] = Field(
        default_factory=list,
        description="Detailed thinking steps"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations"
    )
    next_step_required: bool = Field(False)
    total_steps: int = Field(1, ge=1)
    
    @validator('thinking_steps')
    def validate_steps_consistency(cls, v, values):
        """Ensure thinking steps are consistent."""
        if v and len(v) > values.get('total_steps', 1):
            raise ValueError("Number of thinking steps exceeds total_steps")
        return v


class CodeReviewResponse(ZenMCPBaseResponse):
    """Response model for code review."""
    overall_assessment: str = Field(..., description="Overall code assessment")
    strengths: List[str] = Field(default_factory=list)
    issues: List[CodeReviewIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    focus_areas: List[str] = Field(default_factory=list)
    
    @validator('overall_assessment')
    def validate_assessment(cls, v):
        """Ensure assessment is valid."""
        valid_assessments = ["excellent", "good", "needs_improvement", "poor"]
        if v.lower() not in valid_assessments:
            # Allow free-form but log warning
            pass
        return v


class ChallengeResponse(ZenMCPBaseResponse):
    """Response model for challenge tool."""
    concerns: List[str] = Field(default_factory=list, description="Identified concerns")
    alternatives: List[str] = Field(default_factory=list, description="Alternative approaches")
    should_reconsider: bool = Field(False, description="Whether to reconsider the approach")
    rationale: Optional[str] = Field(None, description="Detailed rationale")


class ModelVote(BaseModel):
    """Model for a single model's vote in consensus."""
    model: str = Field(..., description="Model name")
    stance: str = Field(..., pattern="^(for|against|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = Field(None)


class ConsensusResponse(ZenMCPBaseResponse):
    """Response model for consensus tool."""
    consensus: str = Field(..., description="Overall consensus decision")
    model_responses: List[ModelVote] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence_variance: float = Field(0.0, ge=0.0, description="Variance in model confidences")
    
    @validator('consensus')
    def validate_consensus(cls, v):
        """Ensure consensus is meaningful."""
        if v.lower() in ["tie", "no_consensus", "split"]:
            # These are valid but indicate no clear decision
            pass
        return v


class SpecificationAnalysisResponse(ZenMCPBaseResponse):
    """Response model for specification analysis."""
    findings: str = Field(..., description="Analysis findings")
    ambiguities: List[str] = Field(default_factory=list, description="Identified ambiguities")
    implementation_challenges: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    challenge_insights: Optional[Dict[str, Any]] = Field(None)


class QualityMetrics(BaseModel):
    """Quality metrics for code assessment."""
    readability_score: float = Field(..., ge=0.0, le=100.0)
    maintainability_score: float = Field(..., ge=0.0, le=100.0)
    test_coverage_estimate: float = Field(..., ge=0.0, le=100.0)
    security_score: float = Field(..., ge=0.0, le=100.0)
    performance_score: float = Field(..., ge=0.0, le=100.0)
    
    @property
    def overall_score(self) -> float:
        """Calculate overall quality score."""
        scores = [
            self.readability_score,
            self.maintainability_score,
            self.test_coverage_estimate,
            self.security_score,
            self.performance_score
        ]
        return sum(scores) / len(scores)


class AutoRollbackSuggestion(BaseModel):
    """Model for automatic rollback suggestions."""
    issue_detected: str = Field(..., description="The quality issue detected")
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    rollback_strategy: str = Field(..., description="Suggested rollback approach")
    alternative_implementation: Optional[str] = Field(None, description="Alternative code suggestion")
    confidence: float = Field(..., ge=0.0, le=1.0)


class QualityAssessmentResponse(ZenMCPBaseResponse):
    """Comprehensive quality assessment response."""
    quality_metrics: QualityMetrics
    detected_patterns: List[str] = Field(
        default_factory=list,
        description="Detected code patterns (good and bad)"
    )
    auto_rollback_suggestions: List[AutoRollbackSuggestion] = Field(
        default_factory=list,
        description="Automatic rollback suggestions for quality issues"
    )
    human_readable_summary: str = Field(
        ...,
        description="Non-technical summary for non-developers"
    )
    technical_debt_estimate: str = Field(
        "low",
        pattern="^(none|low|medium|high|critical)$"
    )
    
    def should_trigger_rollback(self, threshold: float = 60.0) -> bool:
        """Determine if automatic rollback should be triggered."""
        return (
            self.quality_metrics.overall_score < threshold or
            any(s.severity == "critical" for s in self.auto_rollback_suggestions)
        )