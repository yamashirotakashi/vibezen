"""
VIBEZEN Guard V2 - Redesigned for prompt intervention.

This is the main entry point that uses prompt engineering
rather than external monitoring.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import asyncio
import logging

from vibezen.core.config import VIBEZENConfig
from vibezen.core.models import (
    ThinkingContext,
    ThinkingPhase,
    SpecViolation,
    ViolationType,
    Severity,
)
from vibezen.proxy.ai_proxy import AIProxy, ProxyConfig
from vibezen.providers.registry import ProviderRegistry
from vibezen.prompts.template_engine import PromptTemplateEngine
from vibezen.prompts.phases import PhaseManager


logger = logging.getLogger(__name__)


class VIBEZENGuardV2:
    """
    Redesigned VIBEZEN guard that intervenes at the prompt level.
    
    Instead of monitoring AI output, this version shapes AI behavior
    through carefully crafted prompts and thinking guidance.
    """
    
    def __init__(
        self,
        config: Optional[VIBEZENConfig] = None,
        config_path: Optional[Path] = None,
    ):
        """Initialize VIBEZEN Guard V2."""
        # Load configuration
        if config:
            self.config = config
        elif config_path:
            self.config = VIBEZENConfig.from_yaml(config_path)
        else:
            default_path = Path("vibezen.yaml")
            if default_path.exists():
                self.config = VIBEZENConfig.from_yaml(default_path)
            else:
                self.config = VIBEZENConfig()
        
        # Initialize components
        self.proxy_config = ProxyConfig(
            enable_interception=True,
            enable_checkpoints=True,
            enable_thinking_prompts=True,
            cache_prompts=self.config.defense.pre_validation.cache_results,
            timeout_seconds=300,
        )
        
        self.ai_proxy = AIProxy(self.proxy_config)
        self.provider_registry = ProviderRegistry()
        self.template_engine = PromptTemplateEngine()
        self.phase_manager = PhaseManager()
        
        # State
        self.current_context: Optional[ThinkingContext] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return
        
        # Initialize provider registry
        await self.provider_registry.initialize()
        
        # Register providers with proxy
        for name, provider in self.provider_registry.providers.items():
            self.ai_proxy.register_provider(name, provider)
        
        self._initialized = True
        logger.info("VIBEZEN Guard V2 initialized")
    
    async def guide_specification_understanding(
        self,
        specification: Dict[str, Any],
        provider: str = "mock",
        model: str = "mock-smart",
    ) -> Dict[str, Any]:
        """
        Guide AI through specification understanding.
        
        This is the entry point for the VIBEcoding workflow.
        """
        await self.initialize()
        
        # Create thinking context
        self.current_context = ThinkingContext(
            phase=ThinkingPhase.SPEC_UNDERSTANDING,
            specification=specification,
            confidence=0.0,
        )
        
        # Start the phase
        phase = self.phase_manager.start_phase(
            ThinkingPhase.SPEC_UNDERSTANDING,
            {"specification": specification}
        )
        
        # Get minimum steps for this phase
        min_steps = self.config.thinking.min_steps.get("spec_understanding", 5)
        
        # Force AI to think through the specification
        response = await self.ai_proxy.force_thinking(
            problem=f"Understand this specification: {specification}",
            phase=ThinkingPhase.SPEC_UNDERSTANDING,
            min_steps=min_steps,
        )
        
        # Extract understanding from response
        understanding = self._extract_understanding(response.content)
        
        # Update context
        self.current_context.confidence = understanding.get("confidence", 0.5)
        self.current_context.metadata.update(understanding)
        
        return {
            "success": True,
            "understanding": understanding,
            "thinking_trace": response.thinking_trace,
            "next_phase": ThinkingPhase.IMPLEMENTATION_CHOICE,
        }
    
    async def guide_implementation_choice(
        self,
        specification: Dict[str, Any],
        understanding: Dict[str, Any],
        provider: str = "mock",
        model: str = "mock-smart",
    ) -> Dict[str, Any]:
        """Guide AI through implementation choice."""
        if not self.current_context:
            self.current_context = ThinkingContext(
                phase=ThinkingPhase.IMPLEMENTATION_CHOICE,
                specification=specification,
            )
        
        # Transition to implementation choice phase
        phase = self.phase_manager.transition_to(
            ThinkingPhase.IMPLEMENTATION_CHOICE,
            {
                "specification": specification,
                "understanding": understanding,
            }
        )
        
        # Create context for prompt generation
        prompt_context = {
            "spec_summary": understanding.get("summary", ""),
            "requirements": understanding.get("requirements", []),
            "constraints": understanding.get("constraints", []),
            "min_approaches": 3,
        }
        
        # Generate implementation choice prompt
        prompt = await self.template_engine.generate_prompt(
            phase=ThinkingPhase.IMPLEMENTATION_CHOICE,
            context=prompt_context,
        )
        
        # Get AI response with thinking
        response = await self.ai_proxy.call(
            prompt=prompt,
            provider=provider,
            model=model,
            context=self.current_context,
        )
        
        # Extract approaches from response
        approaches = self._extract_approaches(response.content)
        
        return {
            "success": True,
            "approaches": approaches,
            "selected_approach": approaches[0] if approaches else None,
            "thinking_trace": response.thinking_trace,
            "next_phase": ThinkingPhase.IMPLEMENTATION,
        }
    
    async def guide_implementation(
        self,
        specification: Dict[str, Any],
        approach: Dict[str, Any],
        provider: str = "mock",
        model: str = "mock-smart",
    ) -> Dict[str, Any]:
        """Guide AI through implementation with quality checks."""
        if not self.current_context:
            self.current_context = ThinkingContext(
                phase=ThinkingPhase.IMPLEMENTATION,
                specification=specification,
            )
        
        # Transition to implementation phase
        phase = self.phase_manager.transition_to(
            ThinkingPhase.IMPLEMENTATION,
            {
                "specification": specification,
                "approach": approach,
            }
        )
        
        # Check for checkpoint
        checkpoint = self.phase_manager.get_next_checkpoint()
        if checkpoint:
            # Generate checkpoint prompt
            checkpoint_prompt = self.template_engine.create_checkpoint_prompt(
                checkpoint.name,
                {
                    "phase": ThinkingPhase.IMPLEMENTATION,
                    "approach": approach,
                }
            )
            
            # Get validation
            validation_response = await self.ai_proxy.call(
                prompt=checkpoint_prompt,
                provider=provider,
                model=model,
                context=self.current_context,
            )
            
            # Process validation
            if not self._validate_checkpoint(validation_response.content):
                return {
                    "success": False,
                    "error": "Checkpoint validation failed",
                    "suggestions": ["Review approach", "Check requirements"],
                }
        
        # Generate implementation prompt with quality guidelines
        impl_prompt = self._create_implementation_prompt(specification, approach)
        
        # Get implementation
        response = await self.ai_proxy.call(
            prompt=impl_prompt,
            provider=provider,
            model=model,
            context=self.current_context,
        )
        
        # Extract code and validate
        code = self._extract_code(response.content)
        violations = await self._validate_code(code, specification)
        
        # If violations found, generate correction prompt
        if violations:
            correction_prompt = await self._create_correction_prompt(code, violations)
            
            # Get corrected code
            correction_response = await self.ai_proxy.call(
                prompt=correction_prompt,
                provider=provider,
                model=model,
                context=self.current_context,
            )
            
            code = self._extract_code(correction_response.content)
            violations = await self._validate_code(code, specification)
        
        return {
            "success": len(violations) == 0,
            "code": code,
            "violations": violations,
            "thinking_trace": response.thinking_trace,
            "next_phase": ThinkingPhase.TEST_DESIGN,
        }
    
    async def guide_test_design(
        self,
        specification: Dict[str, Any],
        code: str,
        provider: str = "mock",
        model: str = "mock-smart",
    ) -> Dict[str, Any]:
        """Guide AI through test design."""
        if not self.current_context:
            self.current_context = ThinkingContext(
                phase=ThinkingPhase.TEST_DESIGN,
                specification=specification,
                code=code,
            )
        
        # Generate test design prompt
        test_prompt = await self.template_engine.generate_prompt(
            phase=ThinkingPhase.TEST_DESIGN,
            context={
                "specification": specification,
                "code": code,
            }
        )
        
        # Get test design
        response = await self.ai_proxy.call(
            prompt=test_prompt,
            provider=provider,
            model=model,
            context=self.current_context,
        )
        
        # Extract tests
        tests = self._extract_tests(response.content)
        
        return {
            "success": True,
            "tests": tests,
            "coverage_estimate": self._estimate_coverage(tests, specification),
            "thinking_trace": response.thinking_trace,
            "next_phase": ThinkingPhase.QUALITY_REVIEW,
        }
    
    async def perform_quality_review(
        self,
        code: str,
        tests: List[Dict[str, Any]],
        specification: Dict[str, Any],
        provider: str = "mock",
        model: str = "mock-smart",
    ) -> Dict[str, Any]:
        """Perform final quality review."""
        # Create review context
        review_context = {
            "code": code,
            "tests": tests,
            "specification": specification,
            "language": "python",
        }
        
        # Generate critical review prompt
        review_prompt = await self.template_engine.generate_prompt(
            phase=ThinkingPhase.QUALITY_REVIEW,
            context=review_context,
            template_name="critical_review",
        )
        
        # Get review
        response = await self.ai_proxy.call(
            prompt=review_prompt,
            provider=provider,
            model=model,
            context=self.current_context,
        )
        
        # Extract findings
        findings = self._extract_review_findings(response.content)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(findings)
        
        return {
            "success": quality_score >= 0.7,
            "quality_score": quality_score,
            "findings": findings,
            "recommendations": self._generate_recommendations(findings),
            "thinking_trace": response.thinking_trace,
        }
    
    # Helper methods
    
    def _extract_understanding(self, content: str) -> Dict[str, Any]:
        """Extract understanding from AI response."""
        # Simplified extraction - real implementation would be more sophisticated
        return {
            "summary": "Extracted summary",
            "requirements": ["req1", "req2"],
            "constraints": ["constraint1"],
            "edge_cases": ["edge1"],
            "confidence": 0.7,
        }
    
    def _extract_approaches(self, content: str) -> List[Dict[str, Any]]:
        """Extract implementation approaches."""
        # Simplified - real implementation would parse structured response
        return [
            {
                "name": "Approach 1",
                "description": "Simple implementation",
                "pros": ["Easy", "Fast"],
                "cons": ["Limited"],
            }
        ]
    
    def _extract_code(self, content: str) -> str:
        """Extract code from response."""
        # Look for code blocks
        import re
        code_pattern = r"```(?:python)?\n(.*?)\n```"
        matches = re.findall(code_pattern, content, re.DOTALL)
        return matches[0] if matches else content
    
    async def _validate_code(self, code: str, specification: Dict[str, Any]) -> List[SpecViolation]:
        """Validate code against specification."""
        violations = []
        
        # Check for hardcodes
        if self.config.triggers.hardcode_detection.enabled:
            import re
            for pattern in self.config.triggers.hardcode_detection.patterns:
                if re.search(pattern, code):
                    violations.append(SpecViolation(
                        type=ViolationType.HARDCODE,
                        description=f"Hardcoded value matching: {pattern}",
                        severity=Severity.HIGH,
                        suggested_action="Move to configuration",
                    ))
        
        return violations
    
    def _create_implementation_prompt(self, spec: Dict[str, Any], approach: Dict[str, Any]) -> str:
        """Create implementation prompt with quality guidelines."""
        return f"""Implement the following specification using the chosen approach.

SPECIFICATION: {spec}

APPROACH: {approach}

CRITICAL REQUIREMENTS:
1. NO hardcoded values - use configuration or parameters
2. Implement ONLY what's specified - no extra features
3. Handle errors appropriately
4. Keep functions small and focused
5. Write clean, readable code

Provide the implementation:"""
    
    async def _create_correction_prompt(self, code: str, violations: List[SpecViolation]) -> str:
        """Create prompt to correct code violations."""
        violation_text = "\n".join([
            f"- {v.description}: {v.suggested_action}"
            for v in violations
        ])
        
        return f"""The following code has quality issues that must be fixed:

```python
{code}
```

ISSUES FOUND:
{violation_text}

Please provide corrected code that addresses ALL issues:"""
    
    def _validate_checkpoint(self, content: str) -> bool:
        """Validate checkpoint response."""
        # Simple validation - check for positive indicators
        positive_indicators = ["ready", "complete", "understood", "yes"]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in positive_indicators)
    
    def _extract_tests(self, content: str) -> List[Dict[str, Any]]:
        """Extract test cases from response."""
        # Simplified extraction
        return [
            {"name": "test_happy_path", "type": "unit"},
            {"name": "test_edge_case", "type": "unit"},
        ]
    
    def _estimate_coverage(self, tests: List[Dict[str, Any]], spec: Dict[str, Any]) -> float:
        """Estimate test coverage."""
        # Simple heuristic
        return min(len(tests) / 5.0, 1.0)  # Assume 5 tests for full coverage
    
    def _extract_review_findings(self, content: str) -> List[Dict[str, Any]]:
        """Extract findings from review."""
        # Simplified extraction
        return [
            {"type": "quality", "severity": "low", "description": "Could improve naming"},
        ]
    
    def _calculate_quality_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate quality score from findings."""
        if not findings:
            return 1.0
        
        # Deduct for each finding based on severity
        score = 1.0
        severity_weights = {"critical": 0.3, "high": 0.2, "medium": 0.1, "low": 0.05}
        
        for finding in findings:
            severity = finding.get("severity", "low")
            score -= severity_weights.get(severity, 0.05)
        
        return max(0.0, score)
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations from findings."""
        if not findings:
            return ["Code quality is excellent!"]
        
        recommendations = []
        for finding in findings:
            if finding["type"] == "quality":
                recommendations.append("Improve code readability and naming")
            elif finding["type"] == "performance":
                recommendations.append("Consider performance optimizations")
        
        return recommendations or ["Address the findings above"]