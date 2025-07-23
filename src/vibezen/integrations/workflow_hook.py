"""
Integration hook for spec_to_implementation_workflow.

Provides seamless integration with the one-stop workflow.
"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from pathlib import Path

from vibezen.core.models import (
    ThinkingResult,
    SpecViolation,
    QualityMetrics,
)
from vibezen.engine.sequential_thinking import SequentialThinkingEngine


class Specification:
    """Represents a project specification."""
    def __init__(self, content: Dict[str, Any]):
        self.content = content
        self.requirements = content.get("requirements", [])
        self.design = content.get("design", {})
        self.metadata = content.get("metadata", {})


class WorkflowResult:
    """Result from workflow execution."""
    def __init__(self, success: bool, artifacts: Dict[str, Any]):
        self.success = success
        self.artifacts = artifacts


class QualityReport:
    """Quality report for the entire workflow."""
    def __init__(self, 
                 overall_score: float,
                 violations: List[SpecViolation],
                 thinking_traces: List[ThinkingResult],
                 recommendations: List[str]):
        self.overall_score = overall_score
        self.violations = violations
        self.thinking_traces = thinking_traces
        self.recommendations = recommendations


class WorkflowHook(ABC):
    """Abstract base class for workflow hooks."""
    
    @abstractmethod
    async def on_spec_loaded(self, spec: Specification) -> None:
        """Called when specification is loaded."""
        pass
    
    @abstractmethod
    async def on_implementation_start(self, spec: Specification) -> None:
        """Called when implementation starts."""
        pass
    
    @abstractmethod
    async def on_code_generated(self, code: str, spec: Specification) -> None:
        """Called when code is generated."""
        pass
    
    @abstractmethod
    async def on_test_generated(self, tests: str, spec: Specification) -> None:
        """Called when tests are generated."""
        pass
    
    @abstractmethod
    async def on_completion(self, result: WorkflowResult) -> QualityReport:
        """Called when workflow completes."""
        pass


class VIBEZENWorkflowHook(WorkflowHook):
    """
    VIBEZEN integration for spec_to_implementation_workflow.
    
    This hook integrates all VIBEZEN features into the workflow:
    - Sequential thinking at each phase
    - 3-layer defense system
    - Spec traceability
    - Quality reporting
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize VIBEZEN workflow hook.
        
        Args:
            config_path: Path to vibezen.yaml configuration
        """
        self.config_path = config_path or Path("vibezen.yaml")
        self.config = self._load_config()
        
        # Initialize components
        self.thinking_engine = SequentialThinkingEngine(
            min_steps=self.config.get("thinking", {}).get("min_steps", {}),
            confidence_threshold=self.config.get("thinking", {}).get("confidence_threshold", 0.7),
            allow_revision=self.config.get("thinking", {}).get("allow_revision", True),
        )
        
        # Storage for tracking
        self.thinking_traces: List[ThinkingResult] = []
        self.violations: List[SpecViolation] = []
        self.current_spec: Optional[Specification] = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f).get("vibezen", {})
        
        # Default configuration
        return {
            "thinking": {
                "min_steps": {
                    "spec_understanding": 5,
                    "implementation_choice": 4,
                    "test_design": 3,
                },
                "confidence_threshold": 0.7,
                "allow_revision": True,
            },
            "defense": {
                "pre_validation": {
                    "enabled": True,
                    "use_o3_search": True,
                },
                "runtime_monitoring": {
                    "enabled": True,
                    "real_time": True,
                },
                "post_validation": {
                    "enabled": True,
                    "strict_mode": False,
                },
            },
            "triggers": {
                "hardcode_detection": {
                    "enabled": True,
                },
                "complexity_threshold": 10,
            },
        }
    
    async def on_spec_loaded(self, spec: Specification) -> None:
        """
        Handle specification loading.
        
        Triggers pre-validation and understanding phase.
        """
        self.current_spec = spec
        
        # Start sequential thinking for spec understanding
        if self.config.get("defense", {}).get("pre_validation", {}).get("enabled", True):
            problem = f"Understand specification: {spec.metadata.get('name', 'Unknown')}"
            result = await self.thinking_engine.think(
                problem=problem,
                context_type="spec_understanding",
                min_steps=self.config["thinking"]["min_steps"].get("spec_understanding", 5),
            )
            self.thinking_traces.append(result)
            
            # Log quality metrics
            if result.trace.quality_metrics:
                print(f"📊 Spec Understanding Quality: {result.trace.quality_metrics.quality_grade}")
                print(f"   Confidence: {result.trace.confidence:.2f}")
    
    async def on_implementation_start(self, spec: Specification) -> None:
        """
        Handle implementation start.
        
        Triggers implementation choice thinking.
        """
        # Sequential thinking for implementation choices
        problem = "Choose implementation approach based on specification"
        result = await self.thinking_engine.think(
            problem=problem,
            context_type="implementation_choice",
            min_steps=self.config["thinking"]["min_steps"].get("implementation_choice", 4),
            force_branches=True,  # Force exploring alternatives
        )
        self.thinking_traces.append(result)
        
        # Log thinking summary
        print(f"🤔 Implementation Thinking: {result.trace.get_step_count()} steps")
        if result.trace.branches:
            print(f"   Explored {len(result.trace.branches)} alternative approaches")
    
    async def on_code_generated(self, code: str, spec: Specification) -> None:
        """
        Handle code generation.
        
        Triggers runtime monitoring and validation.
        """
        if self.config.get("defense", {}).get("runtime_monitoring", {}).get("enabled", True):
            # Analyze generated code
            violations = await self._analyze_code(code, spec)
            self.violations.extend(violations)
            
            # Report violations
            if violations:
                print(f"⚠️  Found {len(violations)} specification violations:")
                for v in violations:
                    print(f"   - {v.severity.value.upper()}: {v.description}")
    
    async def on_test_generated(self, tests: str, spec: Specification) -> None:
        """
        Handle test generation.
        
        Updates traceability matrix.
        """
        # Sequential thinking for test design review
        problem = "Review test design and coverage"
        result = await self.thinking_engine.think(
            problem=problem,
            context_type="test_design",
            min_steps=self.config["thinking"]["min_steps"].get("test_design", 3),
        )
        self.thinking_traces.append(result)
    
    async def on_completion(self, result: WorkflowResult) -> QualityReport:
        """
        Handle workflow completion.
        
        Generates comprehensive quality report.
        """
        # Calculate overall quality
        overall_score = self._calculate_overall_score()
        
        # Generate recommendations
        recommendations = self._generate_final_recommendations()
        
        # Create quality report
        report = QualityReport(
            overall_score=overall_score,
            violations=self.violations,
            thinking_traces=self.thinking_traces,
            recommendations=recommendations,
        )
        
        # Print summary
        print("\n📋 VIBEZEN Quality Report")
        print(f"Overall Score: {overall_score:.2f}/1.00")
        print(f"Violations: {len(self.violations)}")
        print(f"Thinking Quality: {self._get_average_thinking_grade()}")
        
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        return report
    
    async def _analyze_code(self, code: str, spec: Specification) -> List[SpecViolation]:
        """Analyze code for violations."""
        violations = []
        
        # Hardcode detection
        if self.config.get("triggers", {}).get("hardcode_detection", {}).get("enabled", True):
            import re
            patterns = [
                (r'port\s*=\s*\d+', "Hardcoded port number"),
                (r'password\s*=\s*["\']', "Hardcoded password"),
                (r'(localhost|127\.0\.0\.1)', "Hardcoded localhost"),
                (r'timeout\s*=\s*\d+', "Hardcoded timeout value"),
            ]
            
            for pattern, description in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    violations.append(SpecViolation(
                        type="hardcode",
                        description=description,
                        severity="high",
                        suggested_action="Move to configuration file",
                    ))
        
        return violations
    
    def _calculate_overall_score(self) -> float:
        """Calculate overall quality score."""
        # Base score
        score = 1.0
        
        # Deduct for violations
        for violation in self.violations:
            if violation.severity.value == "critical":
                score -= 0.2
            elif violation.severity.value == "high":
                score -= 0.1
            elif violation.severity.value == "medium":
                score -= 0.05
            else:
                score -= 0.02
        
        # Factor in thinking quality
        avg_thinking_score = self._get_average_thinking_score()
        score = score * 0.7 + avg_thinking_score * 0.3
        
        return max(0.0, min(1.0, score))
    
    def _get_average_thinking_score(self) -> float:
        """Get average thinking quality score."""
        if not self.thinking_traces:
            return 0.5
        
        scores = []
        for trace in self.thinking_traces:
            if trace.trace.quality_metrics:
                scores.append(trace.trace.quality_metrics.overall_score)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _get_average_thinking_grade(self) -> str:
        """Get average thinking quality grade."""
        score = self._get_average_thinking_score()
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        return "F"
    
    def _generate_final_recommendations(self) -> List[str]:
        """Generate final recommendations."""
        recommendations = []
        
        # Based on violations
        hardcode_count = sum(1 for v in self.violations if v.type.value == "hardcode")
        if hardcode_count > 0:
            recommendations.append(f"Externalize {hardcode_count} hardcoded values to configuration")
        
        # Based on thinking quality
        avg_score = self._get_average_thinking_score()
        if avg_score < 0.7:
            recommendations.append("Consider deeper analysis in future implementations")
        
        # Based on confidence
        low_confidence_count = sum(
            1 for trace in self.thinking_traces 
            if trace.trace.confidence < self.config["thinking"]["confidence_threshold"]
        )
        if low_confidence_count > 0:
            recommendations.append(f"Review {low_confidence_count} low-confidence decisions")
        
        return recommendations