"""
Quality metrics system for VIBEZEN.

This module implements quality metrics for thinking depth,
revision patterns, and overall code quality assessment.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import statistics

from vibezen.core.types import ThinkingStep, CodeContext
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class QualityGrade(Enum):
    """Quality grade levels."""
    S = "S"  # Exceptional quality
    A = "A"  # Excellent quality
    B = "B"  # Good quality
    C = "C"  # Acceptable quality
    D = "D"  # Poor quality
    F = "F"  # Failing quality


@dataclass
class ThinkingMetrics:
    """Metrics for thinking quality."""
    total_steps: int = 0
    max_depth: int = 0
    revision_count: int = 0
    branch_count: int = 0
    backtrack_count: int = 0
    average_confidence: float = 0.0
    thinking_time_seconds: float = 0.0
    final_confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeQualityMetrics:
    """Metrics for code quality."""
    lines_of_code: int = 0
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 0.0
    test_coverage: float = 0.0
    documentation_coverage: float = 0.0
    code_duplication_ratio: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OverallQualityReport:
    """Overall quality assessment report."""
    thinking_metrics: ThinkingMetrics
    code_metrics: CodeQualityMetrics
    quality_grade: QualityGrade
    overall_score: float  # 0-100
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class ThinkingQualityAnalyzer:
    """Analyzes the quality of thinking process."""
    
    @staticmethod
    def analyze_thinking_steps(steps: List[ThinkingStep]) -> ThinkingMetrics:
        """Analyze thinking steps to extract quality metrics."""
        if not steps:
            return ThinkingMetrics()
        
        metrics = ThinkingMetrics()
        metrics.total_steps = len(steps)
        
        # Calculate depth (max nesting level)
        max_depth = 0
        current_depth = 0
        depth_stack = []
        
        # Track revisions and branches
        revision_count = 0
        branch_count = 0
        backtrack_count = 0
        
        # Confidence tracking
        confidences = []
        
        # Time tracking
        start_time = steps[0].timestamp if steps else None
        end_time = steps[-1].timestamp if steps else None
        
        for step in steps:
            # Update confidence
            confidences.append(step.confidence)
            
            # Check for revisions
            if step.metadata.get("is_revision", False):
                revision_count += 1
            
            # Check for branches
            if step.metadata.get("branch_from"):
                branch_count += 1
                depth_stack.append(current_depth)
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            # Check for backtracks
            if step.metadata.get("backtrack", False):
                backtrack_count += 1
                if depth_stack:
                    current_depth = depth_stack.pop()
        
        # Calculate metrics
        metrics.max_depth = max_depth
        metrics.revision_count = revision_count
        metrics.branch_count = branch_count
        metrics.backtrack_count = backtrack_count
        
        if confidences:
            metrics.average_confidence = statistics.mean(confidences)
            metrics.final_confidence = confidences[-1]
        
        if start_time and end_time:
            metrics.thinking_time_seconds = (end_time - start_time).total_seconds()
        
        # Add metadata
        metrics.metadata = {
            "confidence_trend": "increasing" if len(confidences) > 1 and confidences[-1] > confidences[0] else "stable",
            "revision_ratio": revision_count / metrics.total_steps if metrics.total_steps > 0 else 0,
            "branch_ratio": branch_count / metrics.total_steps if metrics.total_steps > 0 else 0
        }
        
        return metrics
    
    @staticmethod
    def calculate_thinking_score(metrics: ThinkingMetrics) -> float:
        """Calculate a quality score (0-100) for thinking process."""
        score = 0.0
        
        # Base score from confidence
        score += metrics.final_confidence * 30  # Max 30 points
        
        # Depth bonus (deeper thinking is better, up to a point)
        depth_score = min(metrics.max_depth / 5, 1.0) * 20  # Max 20 points
        score += depth_score
        
        # Step count (adequate thinking, not too little or too much)
        if metrics.total_steps < 3:
            step_score = 5  # Too shallow
        elif metrics.total_steps <= 10:
            step_score = 15  # Good range
        elif metrics.total_steps <= 20:
            step_score = 10  # Getting long
        else:
            step_score = 5  # Too long
        score += step_score
        
        # Revision bonus (shows reflection)
        revision_score = min(metrics.revision_count / 3, 1.0) * 15  # Max 15 points
        score += revision_score
        
        # Branch exploration bonus
        branch_score = min(metrics.branch_count / 2, 1.0) * 10  # Max 10 points
        score += branch_score
        
        # Time efficiency (not too fast, not too slow)
        if metrics.thinking_time_seconds < 5:
            time_score = 3  # Too fast
        elif metrics.thinking_time_seconds <= 60:
            time_score = 10  # Good range
        elif metrics.thinking_time_seconds <= 300:
            time_score = 7  # Getting slow
        else:
            time_score = 3  # Too slow
        score += time_score
        
        return min(score, 100.0)


class CodeQualityAnalyzer:
    """Analyzes the quality of generated code."""
    
    @staticmethod
    def analyze_code(context: CodeContext) -> CodeQualityMetrics:
        """Analyze code to extract quality metrics."""
        if not context.code:
            return CodeQualityMetrics()
        
        metrics = CodeQualityMetrics()
        
        # Count lines of code (non-empty, non-comment)
        lines = context.code.split('\n')
        code_lines = 0
        comment_lines = 0
        docstring_lines = 0
        in_docstring = False
        
        for line in lines:
            stripped = line.strip()
            
            # Track docstrings
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                docstring_lines += 1
            elif in_docstring:
                docstring_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            elif stripped:
                code_lines += 1
        
        metrics.lines_of_code = code_lines
        
        # Calculate documentation coverage
        total_lines = code_lines + comment_lines + docstring_lines
        if total_lines > 0:
            metrics.documentation_coverage = (comment_lines + docstring_lines) / total_lines
        
        # Extract complexity from context if available
        if hasattr(context, 'complexity_score'):
            metrics.cyclomatic_complexity = context.complexity_score
        
        # Calculate maintainability index (simplified)
        # MI = 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)
        # Simplified version
        import math
        if metrics.lines_of_code > 0:
            mi = 171 - 16.2 * math.log(metrics.lines_of_code)
            if metrics.cyclomatic_complexity > 0:
                mi -= 0.23 * metrics.cyclomatic_complexity
            metrics.maintainability_index = max(0, min(100, mi))
        
        # Extract test coverage if available
        if hasattr(context, 'test_coverage'):
            metrics.test_coverage = context.test_coverage
        
        # TODO: Implement code duplication detection
        metrics.code_duplication_ratio = 0.0
        
        # Extract security and performance scores if available
        if hasattr(context, 'security_score'):
            metrics.security_score = context.security_score
        if hasattr(context, 'performance_score'):
            metrics.performance_score = context.performance_score
        
        return metrics
    
    @staticmethod
    def calculate_code_score(metrics: CodeQualityMetrics) -> float:
        """Calculate a quality score (0-100) for code."""
        score = 0.0
        
        # Maintainability index contribution (max 25 points)
        score += (metrics.maintainability_index / 100) * 25
        
        # Documentation coverage (max 20 points)
        score += metrics.documentation_coverage * 20
        
        # Test coverage (max 20 points)
        score += metrics.test_coverage * 20
        
        # Complexity penalty (max -15 points)
        if metrics.cyclomatic_complexity > 0:
            complexity_penalty = min(metrics.cyclomatic_complexity / 20, 1.0) * 15
            score -= complexity_penalty
        
        # Code duplication penalty (max -10 points)
        score -= metrics.code_duplication_ratio * 10
        
        # Security bonus (max 15 points)
        score += (metrics.security_score / 100) * 15
        
        # Performance bonus (max 10 points)
        score += (metrics.performance_score / 100) * 10
        
        # Bonus for reasonable size (not too large)
        if metrics.lines_of_code <= 100:
            score += 10
        elif metrics.lines_of_code <= 200:
            score += 5
        
        return max(0, min(score, 100.0))


class QualityMetricsEngine:
    """Main engine for quality metrics calculation."""
    
    def __init__(self):
        """Initialize quality metrics engine."""
        self.thinking_analyzer = ThinkingQualityAnalyzer()
        self.code_analyzer = CodeQualityAnalyzer()
    
    def calculate_overall_quality(
        self,
        thinking_steps: List[ThinkingStep],
        code_context: CodeContext
    ) -> OverallQualityReport:
        """Calculate overall quality metrics and grade."""
        # Analyze thinking
        thinking_metrics = self.thinking_analyzer.analyze_thinking_steps(thinking_steps)
        thinking_score = self.thinking_analyzer.calculate_thinking_score(thinking_metrics)
        
        # Analyze code
        code_metrics = self.code_analyzer.analyze_code(code_context)
        code_score = self.code_analyzer.calculate_code_score(code_metrics)
        
        # Calculate overall score (weighted average)
        overall_score = (thinking_score * 0.4 + code_score * 0.6)
        
        # Determine grade
        grade = self._score_to_grade(overall_score)
        
        # Identify strengths and weaknesses
        strengths = self._identify_strengths(thinking_metrics, code_metrics, thinking_score, code_score)
        weaknesses = self._identify_weaknesses(thinking_metrics, code_metrics, thinking_score, code_score)
        recommendations = self._generate_recommendations(thinking_metrics, code_metrics, weaknesses)
        
        return OverallQualityReport(
            thinking_metrics=thinking_metrics,
            code_metrics=code_metrics,
            quality_grade=grade,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _score_to_grade(self, score: float) -> QualityGrade:
        """Convert numeric score to quality grade."""
        if score >= 95:
            return QualityGrade.S
        elif score >= 85:
            return QualityGrade.A
        elif score >= 75:
            return QualityGrade.B
        elif score >= 65:
            return QualityGrade.C
        elif score >= 50:
            return QualityGrade.D
        else:
            return QualityGrade.F
    
    def _identify_strengths(
        self,
        thinking: ThinkingMetrics,
        code: CodeQualityMetrics,
        thinking_score: float,
        code_score: float
    ) -> List[str]:
        """Identify strengths in the quality report."""
        strengths = []
        
        # Thinking strengths
        if thinking.final_confidence >= 0.8:
            strengths.append("High confidence in final solution")
        if thinking.max_depth >= 3:
            strengths.append("Deep, multi-level thinking process")
        if thinking.revision_count >= 2:
            strengths.append("Good self-reflection and revision")
        if thinking_score >= 80:
            strengths.append("Excellent thinking process quality")
        
        # Code strengths
        if code.maintainability_index >= 80:
            strengths.append("Highly maintainable code")
        if code.documentation_coverage >= 0.3:
            strengths.append("Well-documented code")
        if code.test_coverage >= 0.8:
            strengths.append("Excellent test coverage")
        if code.cyclomatic_complexity <= 5:
            strengths.append("Simple, easy-to-understand code")
        if code_score >= 80:
            strengths.append("High quality code implementation")
        
        return strengths
    
    def _identify_weaknesses(
        self,
        thinking: ThinkingMetrics,
        code: CodeQualityMetrics,
        thinking_score: float,
        code_score: float
    ) -> List[str]:
        """Identify weaknesses in the quality report."""
        weaknesses = []
        
        # Thinking weaknesses
        if thinking.final_confidence < 0.5:
            weaknesses.append("Low confidence in solution")
        if thinking.total_steps < 3:
            weaknesses.append("Insufficient thinking depth")
        if thinking.revision_count == 0:
            weaknesses.append("No self-reflection or revision")
        if thinking_score < 50:
            weaknesses.append("Poor thinking process quality")
        
        # Code weaknesses
        if code.maintainability_index < 50:
            weaknesses.append("Low code maintainability")
        if code.documentation_coverage < 0.1:
            weaknesses.append("Insufficient documentation")
        if code.test_coverage < 0.5:
            weaknesses.append("Poor test coverage")
        if code.cyclomatic_complexity > 10:
            weaknesses.append("High code complexity")
        if code.lines_of_code > 500:
            weaknesses.append("Code may be too large for single module")
        if code_score < 50:
            weaknesses.append("Low code quality")
        
        return weaknesses
    
    def _generate_recommendations(
        self,
        thinking: ThinkingMetrics,
        code: CodeQualityMetrics,
        weaknesses: List[str]
    ) -> List[str]:
        """Generate recommendations based on metrics and weaknesses."""
        recommendations = []
        
        # Thinking recommendations
        if thinking.total_steps < 3:
            recommendations.append("Consider more thorough analysis before implementation")
        if thinking.revision_count == 0:
            recommendations.append("Review and revise your approach for better quality")
        if thinking.final_confidence < 0.7:
            recommendations.append("Explore alternative approaches to increase confidence")
        
        # Code recommendations
        if code.cyclomatic_complexity > 10:
            recommendations.append("Refactor complex functions into smaller, focused units")
        if code.documentation_coverage < 0.2:
            recommendations.append("Add docstrings and comments to improve documentation")
        if code.test_coverage < 0.7:
            recommendations.append("Increase test coverage to at least 70%")
        if code.maintainability_index < 65:
            recommendations.append("Improve code structure for better maintainability")
        if code.lines_of_code > 300:
            recommendations.append("Consider splitting into smaller modules")
        
        # General recommendations
        if len(weaknesses) > 3:
            recommendations.append("Focus on addressing the most critical issues first")
        
        return recommendations
    
    def format_quality_report(self, report: OverallQualityReport) -> str:
        """Format quality report as a readable string."""
        lines = [
            "=" * 60,
            "VIBEZEN Quality Assessment Report",
            "=" * 60,
            f"Overall Grade: {report.quality_grade.value}",
            f"Overall Score: {report.overall_score:.1f}/100",
            f"Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "THINKING METRICS:",
            f"  Total Steps: {report.thinking_metrics.total_steps}",
            f"  Max Depth: {report.thinking_metrics.max_depth}",
            f"  Revisions: {report.thinking_metrics.revision_count}",
            f"  Final Confidence: {report.thinking_metrics.final_confidence:.2f}",
            f"  Thinking Time: {report.thinking_metrics.thinking_time_seconds:.1f}s",
            "",
            "CODE METRICS:",
            f"  Lines of Code: {report.code_metrics.lines_of_code}",
            f"  Cyclomatic Complexity: {report.code_metrics.cyclomatic_complexity:.1f}",
            f"  Maintainability Index: {report.code_metrics.maintainability_index:.1f}",
            f"  Documentation Coverage: {report.code_metrics.documentation_coverage:.1%}",
            f"  Test Coverage: {report.code_metrics.test_coverage:.1%}",
            ""
        ]
        
        if report.strengths:
            lines.extend([
                "STRENGTHS:",
                *[f"  ✓ {strength}" for strength in report.strengths],
                ""
            ])
        
        if report.weaknesses:
            lines.extend([
                "WEAKNESSES:",
                *[f"  ✗ {weakness}" for weakness in report.weaknesses],
                ""
            ])
        
        if report.recommendations:
            lines.extend([
                "RECOMMENDATIONS:",
                *[f"  → {rec}" for rec in report.recommendations],
                ""
            ])
        
        lines.append("=" * 60)
        
        return "\n".join(lines)