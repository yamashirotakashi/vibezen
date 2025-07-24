"""
VIBEZENGuardV2 with integrated introspection capabilities.
"""

from typing import Dict, List, Optional, Any, Callable
import asyncio

from vibezen.core.guard_v2 import VIBEZENGuardV2
from vibezen.core.types import (
    SpecificationAnalysis,
    ImplementationChoice,
    QualityReport,
    CodeContext,
    ThinkingStep,
    IntrospectionTrigger,
)
from vibezen.introspection import (
    IntrospectionEngine,
    InteractiveIntrospectionSystem,
    QualityMetricsEngine,
    TriggerType,
    QualityGrade,
)
from vibezen.core.auto_rollback import AutoRollbackManager, RollbackResult
from vibezen.external.zen_mcp import ZenMCPClient, ZenMCPConfig
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class VIBEZENGuardV2WithIntrospection(VIBEZENGuardV2):
    """VIBEZENGuardV2 enhanced with introspection capabilities."""
    
    def __init__(
        self,
        *args,
        enable_introspection: bool = True,
        introspection_callback: Optional[Callable[[str], asyncio.Awaitable[str]]] = None,
        quality_threshold: float = 75.0,
        max_introspection_rounds: int = 3,
        enable_auto_rollback: bool = True,
        zen_mcp_config: Optional[ZenMCPConfig] = None,
        **kwargs
    ):
        """
        Initialize guard with introspection support.
        
        Args:
            enable_introspection: Whether to enable introspection features
            introspection_callback: Callback for interactive introspection
            quality_threshold: Minimum quality score required
            max_introspection_rounds: Maximum introspection iterations
            enable_auto_rollback: Whether to enable automatic quality rollback
            zen_mcp_config: Configuration for zen-MCP integration
        """
        super().__init__(*args, **kwargs)
        
        self.enable_introspection = enable_introspection
        self.introspection_engine = IntrospectionEngine()
        self.quality_engine = QualityMetricsEngine()
        self.interactive_system = InteractiveIntrospectionSystem(
            prompt_callback=introspection_callback,
            quality_threshold=quality_threshold
        )
        self.max_introspection_rounds = max_introspection_rounds
        
        # Auto-rollback setup
        self.enable_auto_rollback = enable_auto_rollback
        if enable_auto_rollback:
            zen_client = ZenMCPClient(zen_mcp_config or ZenMCPConfig())
            self.rollback_manager = AutoRollbackManager(
                zen_client=zen_client,
                quality_threshold=quality_threshold,
                enable_auto_fix=True
            )
        else:
            self.rollback_manager = None
        
        # History tracking
        self.introspection_history: List[IntrospectionTrigger] = []
        self.quality_history: List[Dict[str, Any]] = []
        self.rollback_history: List[RollbackResult] = []
    
    async def guide_implementation_with_introspection(
        self,
        specification: Dict[str, Any],
        analysis: Optional[SpecificationAnalysis] = None
    ) -> Dict[str, Any]:
        """
        Guide implementation with introspection support.
        
        Returns a dictionary containing:
        - choice: The implementation choice
        - code: The final improved code
        - quality_report: The final quality report
        - introspection_summary: Summary of introspection process
        """
        # First, get the initial implementation choice
        choice = await self.guide_implementation_choice(specification, analysis)
        
        if not self.enable_introspection:
            return {
                "choice": choice,
                "code": choice.approach.get("code", ""),
                "quality_report": None,
                "introspection_summary": None
            }
        
        # Create code context
        context = CodeContext(
            code=choice.approach.get("code", ""),
            specification=specification,
            metadata={
                "implementation_choice": choice.approach,
                "rationale": choice.rationale
            }
        )
        
        # Get thinking steps if available
        thinking_steps = self._extract_thinking_steps(choice)
        
        # Run introspection process
        try:
            final_code, final_report = await self.interactive_system.run_full_introspection(
                context, thinking_steps
            )
            
            # Get session summary
            session_id = list(self.interactive_system.sessions.keys())[-1]
            summary = self.interactive_system.get_session_summary(session_id)
            
            # Run auto-rollback if enabled
            rollback_result = None
            if self.enable_auto_rollback and self.rollback_manager:
                # Get triggers from the introspection
                triggers = await self.analyze_code_with_triggers(
                    final_code, specification
                )
                
                # Assess and potentially rollback
                rollback_result = await self.rollback_manager.assess_and_rollback(
                    final_code, specification, triggers
                )
                
                # Update code if rollback was successful
                if rollback_result.success and rollback_result.fixed_code:
                    final_code = rollback_result.fixed_code
                    # Re-analyze the fixed code
                    final_report = await self.review_code_with_introspection(
                        final_code, specification
                    )
                
                # Track rollback history
                self.rollback_history.append(rollback_result)
            
            # Update choice with improved code
            choice.approach["code"] = final_code
            
            # Track history
            self.quality_history.append({
                "specification_id": specification.get("id", "unknown"),
                "initial_score": summary.get("quality_progression", [{}])[0].get("score", 0),
                "final_score": final_report.overall_score if final_report else 0,
                "improvement": summary.get("total_improvement", 0),
                "iterations": summary.get("iterations", 0),
                "auto_rollback": rollback_result is not None,
                "rollback_success": rollback_result.success if rollback_result else None
            })
            
            return {
                "choice": choice,
                "code": final_code,
                "quality_report": final_report,
                "introspection_summary": summary,
                "rollback_result": rollback_result
            }
            
        except Exception as e:
            logger.error(f"Error in introspection process: {e}")
            return {
                "choice": choice,
                "code": choice.approach.get("code", ""),
                "quality_report": None,
                "introspection_summary": {"error": str(e)}
            }
    
    async def analyze_code_with_triggers(
        self,
        code: str,
        specification: Optional[Dict[str, Any]] = None,
        trigger_types: Optional[List[str]] = None
    ) -> List[IntrospectionTrigger]:
        """
        Analyze code and return introspection triggers.
        
        Args:
            code: The code to analyze
            specification: Optional specification for context
            trigger_types: Optional list of trigger types to check
        
        Returns:
            List of introspection triggers found
        """
        context = CodeContext(
            code=code,
            specification=specification or {}
        )
        
        # Convert string trigger types to enum
        if trigger_types:
            trigger_type_enums = [TriggerType(t) for t in trigger_types]
        else:
            trigger_type_enums = None
        
        triggers = await self.introspection_engine.analyze(context, trigger_type_enums)
        
        # Track in history
        self.introspection_history.extend(triggers)
        
        return triggers
    
    async def review_code_with_introspection(
        self,
        implementation: str,
        specification: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """
        Review code quality with introspection analysis.
        
        Enhanced version that includes introspection triggers in the quality report.
        """
        # Get base quality report
        report = await self.review_code_quality(implementation, specification, context)
        
        if not self.enable_introspection:
            return report
        
        # Run introspection analysis
        code_context = CodeContext(
            code=implementation,
            specification=specification or {},
            metadata=context or {}
        )
        
        triggers = await self.introspection_engine.analyze(code_context)
        
        # Add introspection findings to report
        if triggers:
            # Add to issues list
            for trigger in triggers:
                severity = trigger.severity
                if severity in ["critical", "high"]:
                    report.issues.append({
                        "type": trigger.trigger_type,
                        "severity": severity,
                        "message": trigger.message,
                        "location": trigger.code_location,
                        "suggestion": trigger.suggestion
                    })
            
            # Update overall assessment based on triggers
            critical_count = sum(1 for t in triggers if t.severity == "critical")
            high_count = sum(1 for t in triggers if t.severity == "high")
            
            if critical_count > 0:
                report.overall_assessment = "poor"
            elif high_count > 2:
                report.overall_assessment = "needs_improvement"
            elif high_count > 0 and report.overall_assessment == "excellent":
                report.overall_assessment = "good"
        
        # Add introspection metadata
        report.metadata["introspection_triggers"] = len(triggers)
        report.metadata["introspection_enabled"] = True
        
        return report
    
    def _extract_thinking_steps(self, choice: ImplementationChoice) -> List[ThinkingStep]:
        """Extract thinking steps from implementation choice."""
        steps = []
        
        # If choice has thinking_trace, use it
        if hasattr(choice, 'thinking_trace') and choice.thinking_trace:
            return choice.thinking_trace
        
        # Otherwise, create synthetic steps from available data
        if choice.metadata.get("thinking_steps"):
            for i, step_data in enumerate(choice.metadata["thinking_steps"]):
                step = ThinkingStep(
                    step_number=i + 1,
                    thought=step_data.get("thought", ""),
                    confidence=step_data.get("confidence", 0.5),
                    metadata=step_data.get("metadata", {})
                )
                steps.append(step)
        
        return steps
    
    async def generate_quality_improvement_plan(
        self,
        code: str,
        quality_report: Optional[Any] = None,
        triggers: Optional[List[IntrospectionTrigger]] = None
    ) -> Dict[str, Any]:
        """
        Generate a detailed plan for improving code quality.
        
        Returns:
            Dictionary containing improvement plan with priorities
        """
        plan = {
            "priorities": [],
            "quick_wins": [],
            "long_term_improvements": [],
            "estimated_quality_gain": 0.0
        }
        
        # Analyze code if triggers not provided
        if not triggers:
            context = CodeContext(code=code)
            triggers = await self.introspection_engine.analyze(context)
        
        # Group by severity
        critical = [t for t in triggers if t.severity == "critical"]
        high = [t for t in triggers if t.severity == "high"]
        medium = [t for t in triggers if t.severity == "medium"]
        low = [t for t in triggers if t.severity == "low"]
        
        # Critical issues are top priority
        for trigger in critical:
            plan["priorities"].append({
                "issue": trigger.message,
                "action": trigger.suggestion,
                "impact": "Critical - Must fix immediately",
                "estimated_time": "15-30 minutes"
            })
        
        # High severity issues
        for trigger in high:
            plan["priorities"].append({
                "issue": trigger.message,
                "action": trigger.suggestion,
                "impact": "High - Significant quality improvement",
                "estimated_time": "10-20 minutes"
            })
        
        # Quick wins (low severity, easy fixes)
        for trigger in low:
            if "constant" in trigger.suggestion.lower() or "rename" in trigger.suggestion.lower():
                plan["quick_wins"].append({
                    "issue": trigger.message,
                    "action": trigger.suggestion,
                    "impact": "Minor improvement",
                    "estimated_time": "2-5 minutes"
                })
        
        # Long-term improvements
        for trigger in medium:
            if "refactor" in trigger.suggestion.lower() or "redesign" in trigger.suggestion.lower():
                plan["long_term_improvements"].append({
                    "issue": trigger.message,
                    "action": trigger.suggestion,
                    "impact": "Structural improvement",
                    "estimated_time": "30-60 minutes"
                })
        
        # Estimate quality gain
        base_gain = len(critical) * 10 + len(high) * 5 + len(medium) * 3 + len(low) * 1
        plan["estimated_quality_gain"] = min(base_gain, 50.0)  # Cap at 50 points
        
        # Add specific recommendations based on trigger types
        trigger_types = set(t.trigger_type for t in triggers)
        
        if "hardcode" in trigger_types:
            plan["long_term_improvements"].append({
                "issue": "Hardcoded values throughout codebase",
                "action": "Create a centralized configuration system",
                "impact": "Improved maintainability and deployment flexibility",
                "estimated_time": "1-2 hours"
            })
        
        if "complexity" in trigger_types:
            plan["long_term_improvements"].append({
                "issue": "High complexity in some functions",
                "action": "Refactor complex functions using design patterns",
                "impact": "Better readability and testability",
                "estimated_time": "2-4 hours"
            })
        
        return plan
    
    def get_introspection_stats(self) -> Dict[str, Any]:
        """Get statistics about introspection usage."""
        stats = {
            "total_triggers": len(self.introspection_history),
            "trigger_breakdown": {},
            "quality_improvements": [],
            "average_improvement": 0.0,
            "sessions_count": len(self.interactive_system.sessions),
            "auto_rollback_stats": None
        }
        
        # Count triggers by type
        for trigger in self.introspection_history:
            trigger_type = trigger.trigger_type
            if trigger_type not in stats["trigger_breakdown"]:
                stats["trigger_breakdown"][trigger_type] = 0
            stats["trigger_breakdown"][trigger_type] += 1
        
        # Calculate quality improvements
        if self.quality_history:
            improvements = [h["improvement"] for h in self.quality_history if "improvement" in h]
            if improvements:
                stats["average_improvement"] = sum(improvements) / len(improvements)
                stats["quality_improvements"] = self.quality_history[-5:]  # Last 5
        
        # Add rollback statistics if available
        if self.rollback_manager:
            stats["auto_rollback_stats"] = self.rollback_manager.get_statistics()
        
        return stats
    
    async def get_non_technical_quality_summary(
        self,
        code: str,
        specification: Dict[str, Any]
    ) -> str:
        """
        Get a non-technical quality summary for users without coding knowledge.
        
        Returns:
            Human-readable quality summary
        """
        # Analyze code
        triggers = await self.analyze_code_with_triggers(code, specification)
        
        # Run quality assessment if rollback manager is available
        if self.rollback_manager:
            rollback_result = await self.rollback_manager.assess_and_rollback(
                code, specification, triggers
            )
            return rollback_result.human_summary
        
        # Otherwise, create a simple summary
        critical_count = sum(1 for t in triggers if t.severity == "critical")
        high_count = sum(1 for t in triggers if t.severity == "high")
        
        if critical_count > 0:
            emoji = "🚨"
            status = "has serious issues that need immediate attention"
        elif high_count > 2:
            emoji = "⚠️"
            status = "has several issues that should be fixed"
        elif high_count > 0:
            emoji = "🟡"
            status = "is mostly good but has minor issues"
        else:
            emoji = "✅"
            status = "looks good and follows best practices"
        
        summary = f"{emoji} The code {status}.\n\n"
        
        if triggers:
            summary += "Main concerns:\n"
            for trigger in triggers[:3]:
                summary += f"• {trigger.message}\n"
        
        return summary