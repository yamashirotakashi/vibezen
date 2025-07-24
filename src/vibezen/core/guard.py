"""
VIBEZEN Guard - Main entry point for quality assurance.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import asyncio

from vibezen.core.config import VIBEZENConfig
from vibezen.core.models import (
    ThinkingResult,
    SpecViolation,
    QualityMetrics,
    ViolationType,
    Severity,
)
from vibezen.engine.sequential_thinking import SequentialThinkingEngine
from vibezen.integrations.workflow_hook import (
    Specification,
    WorkflowResult,
    QualityReport,
)
from vibezen.metrics.quality_detector import (
    get_quality_detector,
    MovingCodeDetector,
)


class VIBEZENGuard:
    """
    Main VIBEZEN guard for AI coding quality assurance.
    
    This is the primary interface for using VIBEZEN in your projects.
    It orchestrates all components and provides a simple API.
    """
    
    def __init__(self, config: Optional[VIBEZENConfig] = None, config_path: Optional[Path] = None):
        """
        Initialize VIBEZEN Guard.
        
        Args:
            config: Configuration object (takes precedence)
            config_path: Path to configuration file
        """
        if config:
            self.config = config
        elif config_path:
            self.config = VIBEZENConfig.from_yaml(config_path)
        else:
            # Try default locations
            default_path = Path("vibezen.yaml")
            if default_path.exists():
                self.config = VIBEZENConfig.from_yaml(default_path)
            else:
                self.config = VIBEZENConfig()
        
        # Initialize components
        self.thinking_engine = SequentialThinkingEngine(
            min_steps=self.config.thinking.min_steps,
            confidence_threshold=self.config.thinking.confidence_threshold,
            max_steps=self.config.thinking.max_steps,
            allow_revision=self.config.thinking.allow_revision,
            force_branches=self.config.thinking.force_branches,
        )
        
        # Quality detector for "moving code" detection
        self.quality_detector = get_quality_detector()
        
        # State tracking
        self._current_spec: Optional[Dict[str, Any]] = None
        self._violations: List[SpecViolation] = []
        self._thinking_results: List[ThinkingResult] = []
        self._detection_rates: Dict[str, float] = {}
    
    async def validate_specification(self, spec: Dict[str, Any]) -> ThinkingResult:
        """
        Validate and understand a specification.
        
        Args:
            spec: Specification dictionary
            
        Returns:
            ThinkingResult with understanding analysis
        """
        self._current_spec = spec
        
        # Think through the specification
        result = await self.thinking_engine.think(
            problem=f"Understand specification: {spec.get('name', 'Unknown')}",
            context_type="spec_understanding",
        )
        
        self._thinking_results.append(result)
        return result
    
    async def validate_implementation(self, spec: Dict[str, Any], code: str) -> Dict[str, Any]:
        """
        Validate implementation against specification.
        
        Args:
            spec: Specification dictionary
            code: Generated code
            
        Returns:
            Validation results with violations and recommendations
        """
        violations = []
        
        # Run quality detector for "moving code" patterns
        quality_triggers, detection_rates = await self.quality_detector.detect_quality_issues(
            code=code,
            specification=spec,
            context={"phase": "implementation_validation"}
        )
        
        # Convert quality triggers to violations
        for trigger in quality_triggers:
            violations.append(SpecViolation(
                type=ViolationType.QUALITY,
                description=trigger.message,
                severity=self._map_trigger_severity(trigger.severity),
                suggested_action=trigger.suggestion,
            ))
        
        # Store detection rates for reporting
        self._detection_rates = detection_rates
        
        # Check for hardcoded values
        if self.config.triggers.hardcode_detection.enabled:
            hardcode_violations = await self._detect_hardcodes(code)
            violations.extend(hardcode_violations)
        
        # Check for over-implementation
        if self.config.triggers.over_implementation_detection:
            over_impl_violations = await self._detect_over_implementation(spec, code)
            violations.extend(over_impl_violations)
        
        # Check complexity
        complexity_violations = await self._check_complexity(code)
        violations.extend(complexity_violations)
        
        self._violations.extend(violations)
        
        return {
            "violations": violations,
            "violation_count": len(violations),
            "critical_count": sum(1 for v in violations if v.severity == Severity.CRITICAL),
            "high_count": sum(1 for v in violations if v.severity == Severity.HIGH),
            "recommendations": self._generate_recommendations(violations),
            "detection_rates": self._detection_rates,
            "quality_report": self.quality_detector.get_detection_report(),
        }
    
    async def guide_implementation(self, spec: Dict[str, Any]) -> ThinkingResult:
        """
        Guide implementation choices based on specification.
        
        Args:
            spec: Specification dictionary
            
        Returns:
            ThinkingResult with implementation guidance
        """
        result = await self.thinking_engine.think(
            problem="Choose best implementation approach for specification",
            context_type="implementation_choice",
            force_branches=True,  # Explore alternatives
        )
        
        self._thinking_results.append(result)
        return result
    
    async def review_code_quality(self, code: str) -> ThinkingResult:
        """
        Review code quality and suggest improvements.
        
        Args:
            code: Code to review
            
        Returns:
            ThinkingResult with quality review
        """
        result = await self.thinking_engine.think(
            problem="Review code quality and identify improvements",
            context_type="quality_review",
        )
        
        self._thinking_results.append(result)
        return result
    
    async def generate_quality_report(self) -> QualityReport:
        """
        Generate comprehensive quality report.
        
        Returns:
            QualityReport with all findings
        """
        # Calculate overall score
        overall_score = self._calculate_overall_score()
        
        # Compile recommendations
        all_recommendations = []
        for result in self._thinking_results:
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates
        unique_recommendations = list(set(all_recommendations))
        
        return QualityReport(
            overall_score=overall_score,
            violations=self._violations,
            thinking_traces=self._thinking_results,
            recommendations=unique_recommendations,
        )
    
    async def _detect_hardcodes(self, code: str) -> List[SpecViolation]:
        """Detect hardcoded values in code."""
        import re
        violations = []
        
        # Combine default and custom patterns
        patterns = (
            self.config.triggers.hardcode_detection.patterns +
            self.config.triggers.hardcode_detection.custom_patterns
        )
        
        pattern_descriptions = {
            r'port\s*=\s*\d+': "Hardcoded port number",
            r'password\s*=\s*["\']': "Hardcoded password",
            r'(localhost|127\.0\.0\.1)': "Hardcoded localhost reference",
            r'timeout\s*=\s*\d+': "Hardcoded timeout value",
            r'api_key\s*=\s*["\']': "Hardcoded API key",
        }
        
        for pattern in patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                description = pattern_descriptions.get(
                    pattern, 
                    f"Hardcoded value matching pattern: {pattern}"
                )
                
                violations.append(SpecViolation(
                    type=ViolationType.HARDCODE,
                    description=description,
                    severity=Severity.HIGH,
                    suggested_action="Move to configuration file or environment variable",
                ))
        
        return violations
    
    async def _detect_over_implementation(self, spec: Dict[str, Any], code: str) -> List[SpecViolation]:
        """Detect features not in specification."""
        violations = []
        
        # This is a simplified check - real implementation would be more sophisticated
        spec_features = spec.get("features", [])
        spec_text = str(spec).lower()
        
        # Check for common over-implementation patterns
        suspicious_patterns = [
            (r'class\s+Admin', "admin", "Administrative functionality"),
            (r'def\s+bulk_', "bulk", "Bulk operations"),
            (r'cache[_\.]', "cache", "Caching functionality"),
            (r'async\s+def\s+export_', "export", "Export functionality"),
            (r'logging\.', "logging", "Logging functionality"),
        ]
        
        import re
        for pattern, feature_key, description in suspicious_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                # Check if this feature is mentioned in spec
                if feature_key not in spec_text:
                    violations.append(SpecViolation(
                        type=ViolationType.OVER_IMPLEMENTED,
                        description=f"{description} not found in specification",
                        severity=Severity.MEDIUM,
                        suggested_action="Remove feature or add to specification",
                    ))
        
        return violations
    
    async def _check_complexity(self, code: str) -> List[SpecViolation]:
        """Check code complexity."""
        violations = []
        
        # Simple complexity check based on nesting and function length
        import re
        
        # Check for deeply nested code (more than 4 levels)
        indent_pattern = r'^(    ){5,}'  # 5+ levels of indentation
        if re.search(indent_pattern, code, re.MULTILINE):
            violations.append(SpecViolation(
                type=ViolationType.COMPLEXITY,
                description="Deeply nested code detected (5+ levels)",
                severity=Severity.MEDIUM,
                suggested_action="Refactor to reduce nesting levels",
            ))
        
        # Check for long functions (more than 50 lines)
        function_pattern = r'def\s+\w+\s*\([^)]*\):'
        functions = list(re.finditer(function_pattern, code))
        
        for i, func_match in enumerate(functions):
            start = func_match.start()
            # Find next function or end of file
            end = functions[i + 1].start() if i + 1 < len(functions) else len(code)
            
            func_lines = code[start:end].count('\n')
            if func_lines > 50:
                func_name = func_match.group(0).split('(')[0].replace('def ', '')
                violations.append(SpecViolation(
                    type=ViolationType.COMPLEXITY,
                    description=f"Function '{func_name}' is too long ({func_lines} lines)",
                    severity=Severity.MEDIUM,
                    suggested_action="Break down into smaller functions",
                ))
        
        return violations
    
    def _calculate_overall_score(self) -> float:
        """Calculate overall quality score."""
        base_score = 1.0
        
        # Deduct for violations
        for violation in self._violations:
            if violation.severity == Severity.CRITICAL:
                base_score -= 0.2
            elif violation.severity == Severity.HIGH:
                base_score -= 0.1
            elif violation.severity == Severity.MEDIUM:
                base_score -= 0.05
            else:
                base_score -= 0.02
        
        # Factor in thinking quality
        if self._thinking_results:
            avg_confidence = sum(
                r.trace.confidence for r in self._thinking_results
            ) / len(self._thinking_results)
            
            avg_quality = sum(
                r.trace.quality_metrics.overall_score 
                for r in self._thinking_results 
                if r.trace.quality_metrics
            ) / len(self._thinking_results)
            
            # Weighted combination
            base_score = base_score * 0.6 + avg_confidence * 0.2 + avg_quality * 0.2
        
        return max(0.0, min(1.0, base_score))
    
    def _generate_recommendations(self, violations: List[SpecViolation]) -> List[str]:
        """Generate recommendations based on violations."""
        recommendations = []
        
        # Group violations by type
        hardcode_count = sum(1 for v in violations if v.type == ViolationType.HARDCODE)
        complexity_count = sum(1 for v in violations if v.type == ViolationType.COMPLEXITY)
        over_impl_count = sum(1 for v in violations if v.type == ViolationType.OVER_IMPLEMENTED)
        
        if hardcode_count > 0:
            recommendations.append(
                f"Externalize {hardcode_count} hardcoded values to configuration"
            )
        
        if complexity_count > 0:
            recommendations.append(
                "Refactor complex functions to improve maintainability"
            )
        
        if over_impl_count > 0:
            recommendations.append(
                f"Review {over_impl_count} features not in specification"
            )
        
        if not violations:
            recommendations.append("Code quality looks good! Consider adding more tests.")
        
        return recommendations
    
    def reset(self) -> None:
        """Reset guard state for new analysis."""
        self._current_spec = None
        self._violations.clear()
        self._thinking_results.clear()
        self.thinking_engine.clear_traces()
        self._detection_rates.clear()
    
    def _map_trigger_severity(self, trigger_severity: str) -> Severity:
        """Map trigger severity to VIBEZEN severity."""
        mapping = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
        }
        return mapping.get(trigger_severity.lower(), Severity.MEDIUM)
    
    async def record_detection_feedback(
        self, 
        violation: SpecViolation, 
        is_correct: bool,
        user_comment: Optional[str] = None
    ) -> None:
        """
        Record user feedback on detection accuracy.
        
        Args:
            violation: The violation detected
            is_correct: Whether the detection was correct
            user_comment: Optional user comment
        """
        # Find corresponding trigger
        for trigger in self.quality_detector.detection_history:
            if trigger.get("message") == violation.description:
                self.quality_detector.record_feedback(
                    trigger=trigger,
                    is_correct=is_correct,
                    user_comment=user_comment
                )
                break
    
    def get_detection_metrics(self) -> Dict[str, Any]:
        """Get current detection rate metrics."""
        return {
            "detection_rates": self._detection_rates,
            "detection_report": self.quality_detector.get_detection_report(),
            "metrics_export": self.quality_detector._calculate_overall_detection_rate(),
        }