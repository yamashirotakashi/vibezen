"""
zen-MCP integration with VIBEZEN.
"""

from typing import Dict, List, Optional, Any, Callable
import asyncio

from vibezen.external.zen_mcp.client import ZenMCPClient
from vibezen.external.zen_mcp.config import ZenMCPConfig
from vibezen.core.types import (
    CodeContext,
    ThinkingStep,
    QualityReport,
    SpecificationAnalysis,
    IntrospectionTrigger,
)
from vibezen.utils.logger import get_logger

logger = get_logger(__name__)


class ZenMCPIntegration:
    """Integration layer between VIBEZEN and zen-MCP."""
    
    def __init__(
        self,
        config: Optional[ZenMCPConfig] = None,
        client: Optional[ZenMCPClient] = None
    ):
        """
        Initialize zen-MCP integration.
        
        Args:
            config: Configuration for zen-MCP
            client: Optional pre-configured client
        """
        self.config = config or ZenMCPConfig()
        self.client = client or ZenMCPClient(self.config)
        self._connected = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Connect to zen-MCP."""
        if not self._connected:
            await self.client.connect()
            self._connected = True
            logger.info("zen-MCP integration connected")
    
    async def disconnect(self):
        """Disconnect from zen-MCP."""
        if self._connected:
            await self.client.disconnect()
            self._connected = False
            logger.info("zen-MCP integration disconnected")
    
    async def enhance_specification_analysis(
        self,
        specification: Dict[str, Any],
        initial_analysis: SpecificationAnalysis
    ) -> SpecificationAnalysis:
        """
        Enhance specification analysis using zen-MCP's deep thinking.
        
        Args:
            specification: Original specification
            initial_analysis: Initial VIBEZEN analysis
            
        Returns:
            Enhanced specification analysis
        """
        logger.info("Enhancing specification analysis with zen-MCP")
        
        # Use zen-MCP to analyze specification
        zen_result = await self.client.analyze_specification(
            specification,
            implementation_plan=initial_analysis.implementation_hints.get("approach")
        )
        
        # Merge insights
        if "findings" in zen_result:
            initial_analysis.potential_issues.extend([
                f"[zen-MCP] {finding}"
                for finding in zen_result.get("findings", "").split("\\n")
                if finding.strip()
            ])
        
        if "recommendations" in zen_result:
            initial_analysis.implementation_hints["zen_recommendations"] = zen_result["recommendations"]
        
        if "challenge_insights" in zen_result:
            initial_analysis.metadata["zen_challenge"] = zen_result["challenge_insights"]
        
        # Update confidence based on zen-MCP analysis
        zen_confidence = zen_result.get("confidence", 0.5)
        initial_analysis.confidence = (initial_analysis.confidence + zen_confidence) / 2
        
        logger.info(f"Enhanced analysis confidence: {initial_analysis.confidence}")
        return initial_analysis
    
    async def generate_thinking_steps(
        self,
        context: CodeContext,
        min_steps: int = 3
    ) -> List[ThinkingStep]:
        """
        Generate thinking steps using zen-MCP's thinkdeep.
        
        Args:
            context: Code context
            min_steps: Minimum number of thinking steps
            
        Returns:
            List of thinking steps
        """
        logger.info("Generating thinking steps with zen-MCP")
        
        problem = f"Generate at least {min_steps} deep thinking steps for implementing: {context.specification.get('name', 'Unknown')}"
        
        result = await self.client.thinkdeep(
            problem=problem,
            context=f"Specification: {context.specification}",
            thinking_mode="high"
        )
        
        # Extract thinking steps from result
        steps = []
        step_number = 1
        
        # Parse the thinking process from the result
        if "thinking_steps" in result:
            for step_data in result["thinking_steps"]:
                step = ThinkingStep(
                    step_number=step_number,
                    thought=step_data.get("thought", ""),
                    confidence=step_data.get("confidence", 0.5),
                    metadata={"source": "zen-MCP"}
                )
                steps.append(step)
                step_number += 1
        
        # Ensure minimum steps
        while len(steps) < min_steps:
            # Generate additional steps
            additional_result = await self.client.thinkdeep(
                problem=f"What else should we consider for step {len(steps) + 1}?",
                context=f"Previous steps: {[s.thought for s in steps]}",
                thinking_mode="medium"
            )
            
            step = ThinkingStep(
                step_number=len(steps) + 1,
                thought=additional_result.get("findings", "Further analysis needed"),
                confidence=additional_result.get("confidence", 0.5),
                metadata={"source": "zen-MCP", "generated": True}
            )
            steps.append(step)
        
        return steps
    
    async def review_code_quality(
        self,
        code: str,
        specification: Dict[str, Any],
        triggers: Optional[List[IntrospectionTrigger]] = None
    ) -> QualityReport:
        """
        Review code quality using zen-MCP.
        
        Args:
            code: Code to review
            specification: Original specification
            triggers: Detected quality triggers
            
        Returns:
            Quality report
        """
        logger.info("Reviewing code quality with zen-MCP")
        
        # Convert triggers to dict format
        trigger_dicts = []
        if triggers:
            for trigger in triggers:
                trigger_dicts.append({
                    "type": trigger.trigger_type,
                    "severity": trigger.severity,
                    "message": trigger.message,
                    "location": trigger.code_location
                })
        
        # Get zen-MCP review
        review_result = await self.client.review_implementation(
            code=code,
            specification=specification,
            triggers=trigger_dicts
        )
        
        # Create quality report
        report = QualityReport(
            overall_assessment="",
            score=0.0,
            strengths=[],
            issues=[],
            recommendations=[],
            metadata={"zen_mcp_review": review_result}
        )
        
        # Parse review results
        if "confidence" in review_result:
            report.score = review_result["confidence"] * 100
        
        if "strengths" in review_result:
            report.strengths.extend(review_result["strengths"])
        
        if "issues" in review_result:
            report.issues.extend(review_result["issues"])
        
        if "recommendations" in review_result:
            report.recommendations.extend(review_result["recommendations"])
        
        # Determine overall assessment
        if report.score >= 85:
            report.overall_assessment = "excellent"
        elif report.score >= 70:
            report.overall_assessment = "good"
        elif report.score >= 50:
            report.overall_assessment = "needs_improvement"
        else:
            report.overall_assessment = "poor"
        
        # Add consensus insights if available
        if "consensus_on_triggers" in review_result:
            consensus = review_result["consensus_on_triggers"]
            report.metadata["consensus"] = consensus
            
            # Add consensus recommendations
            if "recommendations" in consensus:
                report.recommendations.extend([
                    f"[Consensus] {rec}" for rec in consensus["recommendations"]
                ])
        
        return report
    
    async def challenge_implementation(
        self,
        code: str,
        rationale: str,
        confidence: float
    ) -> Dict[str, Any]:
        """
        Challenge implementation decisions when confidence is low.
        
        Args:
            code: Implementation code
            rationale: Implementation rationale
            confidence: Current confidence level
            
        Returns:
            Challenge results with insights
        """
        if not self.config.enable_challenge:
            return {}
        
        # Only challenge if confidence is below threshold
        if confidence >= 0.8:
            return {}
        
        logger.info(f"Challenging implementation with confidence {confidence}")
        
        prompt = f"""
        The implementation confidence is {confidence:.2f}. 
        
        Rationale: {rationale}
        
        Code:
        ```
        {code[:1000]}...
        ```
        
        What are the potential issues or better approaches?
        """
        
        result = await self.client.challenge(prompt)
        
        # Extract actionable insights
        insights = {
            "challenged": True,
            "original_confidence": confidence,
            "challenge_result": result,
            "should_reconsider": result.get("confidence", 0) < confidence
        }
        
        return insights
    
    async def build_consensus_on_quality(
        self,
        code: str,
        quality_reports: List[QualityReport]
    ) -> Dict[str, Any]:
        """
        Build consensus on code quality across multiple assessments.
        
        Args:
            code: Code being evaluated
            quality_reports: Multiple quality reports
            
        Returns:
            Consensus analysis
        """
        if not self.config.enable_consensus:
            return {}
        
        logger.info("Building consensus on code quality")
        
        # Prepare proposal
        scores = [r.score for r in quality_reports]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        proposal = f"""
        Code quality assessments:
        - Average score: {avg_score:.1f}/100
        - Score range: {min(scores):.1f} - {max(scores):.1f}
        - Number of assessments: {len(quality_reports)}
        
        Should this code be accepted as-is, or does it need improvements?
        
        Key issues identified:
        {self._summarize_issues(quality_reports)}
        """
        
        # Get consensus
        result = await self.client.consensus(proposal)
        
        # Add code snippet for context
        result["code_preview"] = code[:500] + "..." if len(code) > 500 else code
        result["average_score"] = avg_score
        result["score_variance"] = max(scores) - min(scores) if scores else 0
        
        return result
    
    async def generate_improvement_strategy(
        self,
        code: str,
        triggers: List[IntrospectionTrigger],
        quality_score: float
    ) -> Dict[str, Any]:
        """
        Generate comprehensive improvement strategy.
        
        Args:
            code: Current code
            triggers: Detected issues
            quality_score: Current quality score
            
        Returns:
            Improvement strategy with prioritized actions
        """
        logger.info("Generating improvement strategy with zen-MCP")
        
        # Get improvement prompts
        prompts = await self.client.generate_improvement_prompts(
            code=code,
            triggers=[{
                "type": t.trigger_type,
                "severity": t.severity,
                "message": t.message,
                "location": t.code_location
            } for t in triggers],
            quality_score=quality_score
        )
        
        # Organize by priority
        strategy = {
            "current_score": quality_score,
            "target_score": min(quality_score + 20, 95),  # Realistic target
            "immediate_actions": [],
            "short_term_improvements": [],
            "long_term_refactoring": [],
            "estimated_effort": "",
            "prompts": prompts
        }
        
        # Categorize improvements based on trigger severity
        critical_triggers = [t for t in triggers if t.severity == "critical"]
        high_triggers = [t for t in triggers if t.severity == "high"]
        medium_triggers = [t for t in triggers if t.severity == "medium"]
        
        # Immediate actions (critical issues)
        for trigger in critical_triggers[:3]:
            strategy["immediate_actions"].append({
                "issue": trigger.message,
                "action": trigger.suggestion,
                "impact": "Critical - Must fix immediately",
                "estimated_time": "15-30 minutes"
            })
        
        # Short-term improvements (high priority)
        for trigger in high_triggers[:5]:
            strategy["short_term_improvements"].append({
                "issue": trigger.message,
                "action": trigger.suggestion,
                "impact": "High - Significant quality improvement",
                "estimated_time": "30-60 minutes"
            })
        
        # Long-term refactoring (medium priority, structural issues)
        for trigger in medium_triggers[:3]:
            if "refactor" in trigger.suggestion.lower() or "redesign" in trigger.suggestion.lower():
                strategy["long_term_refactoring"].append({
                    "issue": trigger.message,
                    "action": trigger.suggestion,
                    "impact": "Structural improvement",
                    "estimated_time": "2-4 hours"
                })
        
        # Estimate total effort
        total_items = (
            len(strategy["immediate_actions"]) +
            len(strategy["short_term_improvements"]) +
            len(strategy["long_term_refactoring"])
        )
        
        if total_items <= 3:
            strategy["estimated_effort"] = "1-2 hours"
        elif total_items <= 8:
            strategy["estimated_effort"] = "4-8 hours"
        else:
            strategy["estimated_effort"] = "1-2 days"
        
        return strategy
    
    def _summarize_issues(self, reports: List[QualityReport]) -> str:
        """Summarize issues from multiple reports."""
        all_issues = []
        for report in reports:
            all_issues.extend(report.issues)
        
        # Count occurrences
        issue_counts = {}
        for issue in all_issues:
            issue_str = str(issue)
            if issue_str in issue_counts:
                issue_counts[issue_str] += 1
            else:
                issue_counts[issue_str] = 1
        
        # Format top issues
        sorted_issues = sorted(
            issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        summary = []
        for issue, count in sorted_issues[:5]:
            if count > 1:
                summary.append(f"- {issue} (reported {count} times)")
            else:
                summary.append(f"- {issue}")
        
        return "\\n".join(summary) if summary else "No consistent issues found"