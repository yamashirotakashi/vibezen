"""
Integration with the one-stop spec_to_implementation_workflow.

This module shows how VIBEZEN V2 enhances the existing workflow
by adding AI quality assurance at each step.
"""

from typing import Dict, Any, Optional, List
import asyncio
from pathlib import Path

from vibezen.core.guard_v2 import VIBEZENGuardV2
from vibezen.core.models import ThinkingPhase


class VIBEZENWorkflowIntegration:
    """
    Integrates VIBEZEN V2 with the one-stop workflow.
    
    This can be used as a drop-in enhancement to existing
    spec_to_implementation_workflow.py
    """
    
    def __init__(self, vibezen_config_path: Optional[Path] = None):
        """Initialize VIBEZEN integration."""
        self.guard = VIBEZENGuardV2(config_path=vibezen_config_path)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize VIBEZEN components."""
        if not self._initialized:
            await self.guard.initialize()
            self._initialized = True
    
    async def enhance_spec_understanding(
        self,
        specification: Dict[str, Any],
        provider: str = "mock",
        model: str = "mock-smart"
    ) -> Dict[str, Any]:
        """
        Enhance specification understanding phase.
        
        This replaces or enhances the existing spec parsing
        with AI-guided understanding.
        """
        await self.initialize()
        
        # Use VIBEZEN to guide deep understanding
        result = await self.guard.guide_specification_understanding(
            specification=specification,
            provider=provider,
            model=model
        )
        
        # Extract structured understanding
        understanding = result["understanding"]
        
        # Enhanced output for workflow
        return {
            "success": result["success"],
            "requirements": {
                "functional": understanding.get("requirements", []),
                "non_functional": understanding.get("constraints", []),
                "implicit": understanding.get("implicit_requirements", [])
            },
            "edge_cases": understanding.get("edge_cases", []),
            "ambiguities": understanding.get("ambiguities", []),
            "thinking_trace": result.get("thinking_trace"),
            "confidence": understanding.get("confidence", 0.5)
        }
    
    async def enhance_implementation_planning(
        self,
        specification: Dict[str, Any],
        understanding: Dict[str, Any],
        provider: str = "mock",
        model: str = "mock-smart"
    ) -> Dict[str, Any]:
        """
        Enhance implementation planning phase.
        
        Ensures AI considers multiple approaches and makes
        informed decisions.
        """
        # Use VIBEZEN to explore implementation approaches
        result = await self.guard.guide_implementation_choice(
            specification=specification,
            understanding=understanding,
            provider=provider,
            model=model
        )
        
        # Structure for workflow
        return {
            "success": result["success"],
            "approaches_considered": result["approaches"],
            "selected_approach": result["selected_approach"],
            "justification": result["selected_approach"].get("justification", ""),
            "implementation_plan": self._create_implementation_plan(
                result["selected_approach"]
            ),
            "thinking_trace": result.get("thinking_trace")
        }
    
    async def enhance_code_generation(
        self,
        specification: Dict[str, Any],
        approach: Dict[str, Any],
        provider: str = "mock",
        model: str = "mock-smart"
    ) -> Dict[str, Any]:
        """
        Enhance code generation phase.
        
        Ensures generated code meets quality standards and
        specification requirements.
        """
        # Use VIBEZEN to guide quality implementation
        result = await self.guard.guide_implementation(
            specification=specification,
            approach=approach,
            provider=provider,
            model=model
        )
        
        return {
            "success": result["success"],
            "code": result["code"],
            "language": approach.get("language", "python"),
            "violations": result.get("violations", []),
            "quality_assured": len(result.get("violations", [])) == 0,
            "thinking_trace": result.get("thinking_trace")
        }
    
    async def enhance_test_generation(
        self,
        specification: Dict[str, Any],
        code: str,
        provider: str = "mock",
        model: str = "mock-smart"
    ) -> Dict[str, Any]:
        """
        Enhance test generation phase.
        
        Ensures comprehensive test coverage based on
        specification requirements.
        """
        # Use VIBEZEN to guide test design
        result = await self.guard.guide_test_design(
            specification=specification,
            code=code,
            provider=provider,
            model=model
        )
        
        return {
            "success": result["success"],
            "test_cases": result["tests"],
            "coverage_estimate": result["coverage_estimate"],
            "test_categories": self._categorize_tests(result["tests"]),
            "thinking_trace": result.get("thinking_trace")
        }
    
    async def perform_final_validation(
        self,
        code: str,
        tests: List[Dict[str, Any]],
        specification: Dict[str, Any],
        provider: str = "mock",
        model: str = "mock-smart"
    ) -> Dict[str, Any]:
        """
        Perform final validation and quality review.
        
        This can be integrated into the workflow's
        completion phase.
        """
        # Use VIBEZEN for final review
        result = await self.guard.perform_quality_review(
            code=code,
            tests=tests,
            specification=specification,
            provider=provider,
            model=model
        )
        
        return {
            "success": result["success"],
            "quality_score": result["quality_score"],
            "findings": result["findings"],
            "recommendations": result["recommendations"],
            "ready_for_deployment": result["quality_score"] >= 0.8,
            "thinking_trace": result.get("thinking_trace")
        }
    
    def _create_implementation_plan(self, approach: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured implementation plan from approach."""
        return {
            "phases": [
                {
                    "name": "Setup",
                    "tasks": ["Create project structure", "Set up dependencies"]
                },
                {
                    "name": "Core Implementation",
                    "tasks": approach.get("implementation_steps", [])
                },
                {
                    "name": "Testing",
                    "tasks": ["Write unit tests", "Integration tests"]
                },
                {
                    "name": "Documentation",
                    "tasks": ["API documentation", "Usage examples"]
                }
            ],
            "estimated_effort": approach.get("complexity", "medium")
        }
    
    def _categorize_tests(self, tests: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categorize tests by type."""
        categories = {
            "unit": [],
            "integration": [],
            "edge_case": [],
            "performance": [],
            "security": []
        }
        
        for test in tests:
            test_type = test.get("type", "unit")
            test_name = test.get("name", "unnamed_test")
            
            if test_type in categories:
                categories[test_type].append(test_name)
            else:
                categories["unit"].append(test_name)
        
        return categories


# Example usage function that could be called from spec_to_implementation_workflow.py
async def enhance_workflow_with_vibezen(
    specification_path: Path,
    output_dir: Path,
    provider: str = "openai",
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Enhance the one-stop workflow with VIBEZEN quality assurance.
    
    This function can be integrated into the existing workflow
    or used as a standalone enhancement.
    """
    # Initialize VIBEZEN integration
    vibezen = VIBEZENWorkflowIntegration()
    await vibezen.initialize()
    
    # Load specification (simplified for example)
    specification = {
        "name": "Example Service",
        "description": "Service from specification file",
        # ... load from specification_path
    }
    
    results = {}
    
    # Phase 1: Enhanced Understanding
    print("Phase 1: Understanding specification with AI guidance...")
    understanding = await vibezen.enhance_spec_understanding(
        specification=specification,
        provider=provider,
        model=model
    )
    results["understanding"] = understanding
    
    if not understanding["success"]:
        return {
            "success": False,
            "error": "Failed to understand specification",
            "results": results
        }
    
    # Phase 2: Enhanced Planning
    print("Phase 2: Planning implementation with multiple approaches...")
    planning = await vibezen.enhance_implementation_planning(
        specification=specification,
        understanding=understanding,
        provider=provider,
        model=model
    )
    results["planning"] = planning
    
    # Phase 3: Enhanced Code Generation
    print("Phase 3: Generating code with quality assurance...")
    implementation = await vibezen.enhance_code_generation(
        specification=specification,
        approach=planning["selected_approach"],
        provider=provider,
        model=model
    )
    results["implementation"] = implementation
    
    # Phase 4: Enhanced Test Generation
    print("Phase 4: Generating comprehensive tests...")
    testing = await vibezen.enhance_test_generation(
        specification=specification,
        code=implementation["code"],
        provider=provider,
        model=model
    )
    results["testing"] = testing
    
    # Phase 5: Final Validation
    print("Phase 5: Performing final quality review...")
    validation = await vibezen.perform_final_validation(
        code=implementation["code"],
        tests=testing["test_cases"],
        specification=specification,
        provider=provider,
        model=model
    )
    results["validation"] = validation
    
    # Save outputs (simplified)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save code
    code_file = output_dir / "implementation.py"
    code_file.write_text(implementation["code"])
    
    # Save tests
    test_file = output_dir / "test_implementation.py"
    # ... format and save tests
    
    # Save quality report
    report_file = output_dir / "quality_report.md"
    report_content = f"""# Quality Report

## Overall Score: {validation['quality_score']:.2f}/1.00

## Findings:
{chr(10).join('- ' + str(f) for f in validation['findings'])}

## Recommendations:
{chr(10).join('- ' + r for r in validation['recommendations'])}

## Ready for Deployment: {'Yes' if validation['ready_for_deployment'] else 'No'}
"""
    report_file.write_text(report_content)
    
    return {
        "success": True,
        "quality_score": validation["quality_score"],
        "output_dir": output_dir,
        "results": results
    }