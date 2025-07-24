"""
Automatic rollback system for quality issues.

This module implements the auto-rollback feature that enables AI to
automatically detect and fix quality issues without human intervention.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from vibezen.core.types import (
    CodeContext,
    QualityReport,
    IntrospectionTrigger,
)
from vibezen.external.zen_mcp import ZenMCPClient, ZenMCPConfig
from vibezen.external.zen_mcp.models import (
    QualityAssessmentResponse,
    AutoRollbackSuggestion,
)
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RollbackResult:
    """Result of an automatic rollback attempt."""
    success: bool
    original_code: str
    fixed_code: Optional[str]
    issues_found: List[str]
    fixes_applied: List[str]
    quality_before: float
    quality_after: Optional[float]
    timestamp: datetime
    rollback_reason: str
    human_summary: str


class AutoRollbackManager:
    """Manages automatic rollback for quality issues."""
    
    def __init__(
        self,
        zen_client: Optional[ZenMCPClient] = None,
        quality_threshold: float = 70.0,
        max_rollback_attempts: int = 3,
        enable_auto_fix: bool = True
    ):
        """
        Initialize auto-rollback manager.
        
        Args:
            zen_client: zen-MCP client for quality assessment
            quality_threshold: Minimum acceptable quality score
            max_rollback_attempts: Maximum rollback attempts
            enable_auto_fix: Whether to attempt automatic fixes
        """
        self.zen_client = zen_client or ZenMCPClient(ZenMCPConfig())
        self.quality_threshold = quality_threshold
        self.max_rollback_attempts = max_rollback_attempts
        self.enable_auto_fix = enable_auto_fix
        self._rollback_history: List[RollbackResult] = []
    
    async def assess_and_rollback(
        self,
        code: str,
        specification: Dict[str, Any],
        triggers: Optional[List[IntrospectionTrigger]] = None
    ) -> RollbackResult:
        """
        Assess code quality and perform automatic rollback if needed.
        
        Args:
            code: Code to assess
            specification: Original specification
            triggers: Detected quality triggers
            
        Returns:
            RollbackResult with details of the rollback
        """
        logger.info("Starting automatic quality assessment and rollback")
        
        # Get comprehensive quality assessment
        assessment = await self._get_quality_assessment(code, specification, triggers)
        
        # Check if rollback is needed
        if not assessment.should_trigger_rollback(self.quality_threshold):
            logger.info(f"Quality score {assessment.quality_metrics.overall_score:.1f} is acceptable")
            return RollbackResult(
                success=True,
                original_code=code,
                fixed_code=None,
                issues_found=[],
                fixes_applied=[],
                quality_before=assessment.quality_metrics.overall_score,
                quality_after=None,
                timestamp=datetime.now(),
                rollback_reason="No rollback needed - quality acceptable",
                human_summary=assessment.human_readable_summary
            )
        
        # Quality is below threshold - attempt rollback
        logger.warning(
            f"Quality score {assessment.quality_metrics.overall_score:.1f} "
            f"below threshold {self.quality_threshold}"
        )
        
        if not self.enable_auto_fix:
            return self._create_rollback_result(
                success=False,
                code=code,
                assessment=assessment,
                reason="Auto-fix disabled - manual intervention required"
            )
        
        # Attempt automatic fixes
        fixed_code = await self._attempt_auto_fix(
            code,
            specification,
            assessment.auto_rollback_suggestions
        )
        
        if fixed_code and fixed_code != code:
            # Re-assess the fixed code
            fixed_assessment = await self._get_quality_assessment(
                fixed_code,
                specification,
                triggers
            )
            
            if fixed_assessment.quality_metrics.overall_score >= self.quality_threshold:
                logger.info("Auto-fix successful! Quality improved.")
                return RollbackResult(
                    success=True,
                    original_code=code,
                    fixed_code=fixed_code,
                    issues_found=[s.issue_detected for s in assessment.auto_rollback_suggestions],
                    fixes_applied=[s.rollback_strategy for s in assessment.auto_rollback_suggestions],
                    quality_before=assessment.quality_metrics.overall_score,
                    quality_after=fixed_assessment.quality_metrics.overall_score,
                    timestamp=datetime.now(),
                    rollback_reason="Automatic quality improvement applied",
                    human_summary=self._generate_human_summary(assessment, fixed_assessment)
                )
        
        # Auto-fix failed or didn't improve quality enough
        return self._create_rollback_result(
            success=False,
            code=code,
            assessment=assessment,
            reason="Auto-fix attempted but quality still below threshold"
        )
    
    async def _get_quality_assessment(
        self,
        code: str,
        specification: Dict[str, Any],
        triggers: Optional[List[IntrospectionTrigger]] = None
    ) -> QualityAssessmentResponse:
        """Get comprehensive quality assessment from zen-MCP."""
        # Use multiple assessment methods for comprehensive view
        
        # 1. Code review
        review_result = await self.zen_client.codeview(
            code=code,
            focus_areas=["quality", "maintainability", "patterns"]
        )
        
        # 2. Deep thinking analysis
        think_result = await self.zen_client.thinkdeep(
            problem=f"Analyze this code for quality issues that would frustrate a non-technical user",
            context=f"Code:\n{code[:1000]}...\n\nSpecification: {specification}"
        )
        
        # 3. Challenge mode for critical assessment
        challenge_result = await self.zen_client.challenge(
            prompt="This code might have quality issues",
            context=f"Review findings: {review_result}"
        )
        
        # Synthesize results into quality assessment
        # (In real implementation, this would use the validated pydantic models)
        assessment = QualityAssessmentResponse(
            success=True,
            confidence=review_result.get("confidence", 0.7),
            quality_metrics={
                "readability_score": self._extract_score(review_result, "readability", 70.0),
                "maintainability_score": self._extract_score(review_result, "maintainability", 65.0),
                "test_coverage_estimate": self._extract_score(review_result, "testability", 60.0),
                "security_score": self._extract_score(review_result, "security", 80.0),
                "performance_score": self._extract_score(review_result, "performance", 75.0),
            },
            detected_patterns=self._extract_patterns(review_result, think_result),
            auto_rollback_suggestions=self._generate_rollback_suggestions(
                review_result,
                challenge_result,
                triggers
            ),
            human_readable_summary=self._create_human_summary(review_result, think_result),
            technical_debt_estimate=self._estimate_debt(review_result)
        )
        
        return assessment
    
    async def _attempt_auto_fix(
        self,
        code: str,
        specification: Dict[str, Any],
        suggestions: List[AutoRollbackSuggestion]
    ) -> Optional[str]:
        """Attempt to automatically fix the code based on suggestions."""
        if not suggestions:
            return None
        
        # Sort suggestions by severity and confidence
        sorted_suggestions = sorted(
            suggestions,
            key=lambda s: (
                {"critical": 0, "high": 1, "medium": 2, "low": 3}[s.severity],
                -s.confidence
            )
        )
        
        current_code = code
        
        for attempt in range(min(self.max_rollback_attempts, len(sorted_suggestions))):
            suggestion = sorted_suggestions[attempt]
            
            logger.info(f"Attempting auto-fix: {suggestion.issue_detected}")
            
            # Use thinkdeep to generate fix
            fix_result = await self.zen_client.thinkdeep(
                problem=f"Fix this code issue: {suggestion.issue_detected}",
                context=f"""
                Current code:
                {current_code}
                
                Suggestion: {suggestion.rollback_strategy}
                Alternative: {suggestion.alternative_implementation or 'Generate appropriate fix'}
                
                Requirements:
                - Maintain all existing functionality
                - Follow the original specification
                - Improve code quality
                """,
                thinking_mode="high"
            )
            
            # Extract fixed code from result
            fixed_code = self._extract_fixed_code(fix_result, current_code)
            
            if fixed_code and fixed_code != current_code:
                current_code = fixed_code
            else:
                logger.warning(f"Auto-fix attempt {attempt + 1} produced no changes")
        
        return current_code if current_code != code else None
    
    def _extract_score(self, result: Dict[str, Any], metric: str, default: float) -> float:
        """Extract a score from assessment results."""
        # Implementation would parse the actual response structure
        # For now, return a mock score based on confidence
        base_score = result.get("confidence", 0.7) * 100
        variance = {"readability": 0, "maintainability": -5, "testability": -10,
                   "security": +5, "performance": -3}.get(metric, 0)
        return max(0.0, min(100.0, base_score + variance))
    
    def _extract_patterns(self, review: Dict, think: Dict) -> List[str]:
        """Extract detected patterns from results."""
        patterns = []
        
        # From review
        if "issues" in review:
            for issue in review["issues"]:
                patterns.append(f"Issue pattern: {issue}")
        
        # From thinking
        if "findings" in think:
            patterns.append(f"Analysis: {think['findings'][:100]}...")
        
        return patterns
    
    def _generate_rollback_suggestions(
        self,
        review: Dict,
        challenge: Dict,
        triggers: Optional[List[IntrospectionTrigger]]
    ) -> List[AutoRollbackSuggestion]:
        """Generate rollback suggestions from various sources."""
        suggestions = []
        
        # From review issues
        if "issues" in review:
            for issue in review["issues"][:3]:  # Top 3 issues
                suggestions.append(AutoRollbackSuggestion(
                    issue_detected=issue,
                    severity="high" if "critical" in issue.lower() else "medium",
                    rollback_strategy=f"Refactor to address: {issue}",
                    alternative_implementation=None,
                    confidence=0.8
                ))
        
        # From triggers
        if triggers:
            for trigger in triggers:
                if trigger.severity in ["critical", "high"]:
                    suggestions.append(AutoRollbackSuggestion(
                        issue_detected=trigger.message,
                        severity=trigger.severity,
                        rollback_strategy=trigger.suggestion,
                        alternative_implementation=None,
                        confidence=0.9
                    ))
        
        return suggestions
    
    def _create_human_summary(self, review: Dict, think: Dict) -> str:
        """Create a human-readable summary for non-technical users."""
        confidence = review.get("confidence", 0)
        
        if confidence > 0.8:
            quality = "good"
            emoji = "✅"
        elif confidence > 0.6:
            quality = "acceptable with some issues"
            emoji = "⚠️"
        else:
            quality = "needs improvement"
            emoji = "❌"
        
        summary = f"{emoji} The code quality is {quality}.\n\n"
        
        if "issues" in review and review["issues"]:
            summary += "Main concerns:\n"
            for issue in review["issues"][:3]:
                summary += f"• {issue}\n"
        else:
            summary += "No major issues found.\n"
        
        summary += f"\nConfidence in this assessment: {confidence * 100:.0f}%"
        
        return summary
    
    def _estimate_debt(self, review: Dict) -> str:
        """Estimate technical debt level."""
        issues_count = len(review.get("issues", []))
        
        if issues_count == 0:
            return "none"
        elif issues_count <= 2:
            return "low"
        elif issues_count <= 5:
            return "medium"
        elif issues_count <= 10:
            return "high"
        else:
            return "critical"
    
    def _extract_fixed_code(self, fix_result: Dict, original: str) -> Optional[str]:
        """Extract fixed code from thinkdeep result."""
        # In real implementation, this would parse the response
        # to extract code blocks or apply suggested changes
        # For now, return None to indicate manual implementation needed
        return None
    
    def _create_rollback_result(
        self,
        success: bool,
        code: str,
        assessment: QualityAssessmentResponse,
        reason: str
    ) -> RollbackResult:
        """Create a rollback result."""
        return RollbackResult(
            success=success,
            original_code=code,
            fixed_code=None,
            issues_found=[s.issue_detected for s in assessment.auto_rollback_suggestions],
            fixes_applied=[],
            quality_before=assessment.quality_metrics.overall_score,
            quality_after=None,
            timestamp=datetime.now(),
            rollback_reason=reason,
            human_summary=assessment.human_readable_summary
        )
    
    def _generate_human_summary(
        self,
        before: QualityAssessmentResponse,
        after: QualityAssessmentResponse
    ) -> str:
        """Generate human-readable summary of the improvement."""
        improvement = after.quality_metrics.overall_score - before.quality_metrics.overall_score
        
        summary = f"🎉 Code quality improved by {improvement:.0f}%!\n\n"
        summary += f"Before: {before.quality_metrics.overall_score:.0f}/100\n"
        summary += f"After: {after.quality_metrics.overall_score:.0f}/100\n\n"
        summary += "Fixed issues:\n"
        
        for suggestion in before.auto_rollback_suggestions[:3]:
            summary += f"• {suggestion.issue_detected}\n"
        
        summary += "\nThe code is now cleaner and more maintainable."
        
        return summary
    
    def get_rollback_history(self) -> List[RollbackResult]:
        """Get the history of rollback attempts."""
        return self._rollback_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rollback statistics."""
        if not self._rollback_history:
            return {
                "total_attempts": 0,
                "successful_rollbacks": 0,
                "average_quality_improvement": 0.0,
                "most_common_issues": []
            }
        
        successful = [r for r in self._rollback_history if r.success and r.quality_after]
        quality_improvements = [
            r.quality_after - r.quality_before
            for r in successful
            if r.quality_after is not None
        ]
        
        all_issues = []
        for r in self._rollback_history:
            all_issues.extend(r.issues_found)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        most_common = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_attempts": len(self._rollback_history),
            "successful_rollbacks": len(successful),
            "average_quality_improvement": (
                sum(quality_improvements) / len(quality_improvements)
                if quality_improvements else 0.0
            ),
            "most_common_issues": [issue for issue, _ in most_common]
        }