"""
VIBEZENGuardV2 with integrated traceability management.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio

from vibezen.core.guard_v2 import VIBEZENGuardV2
from vibezen.core.types import (
    SpecificationAnalysis,
    ImplementationChoice,
    QualityReport,
)
from vibezen.traceability import (
    TraceabilityTracker,
    TraceabilityAnalyzer,
    TraceabilityVisualizer,
    SpecificationItem,
    ImplementationItem,
    TestItem,
    TraceLink,
    TraceLinkType,
    TraceabilityStatus,
    CoverageReport,
    ImpactAnalysis,
)


class VIBEZENGuardV2WithTraceability(VIBEZENGuardV2):
    """VIBEZENGuardV2 enhanced with traceability management."""
    
    def __init__(self, *args, **kwargs):
        """Initialize guard with traceability support."""
        super().__init__(*args, **kwargs)
        
        # Initialize traceability components
        self.tracker = TraceabilityTracker()
        self.analyzer = TraceabilityAnalyzer(self.tracker.matrix)
        self.visualizer = TraceabilityVisualizer(self.tracker.matrix)
        
        # Auto-discovery settings
        self.auto_discover_links = True
        self.link_confidence_threshold = 0.7
    
    async def guide_specification_understanding(
        self,
        specification: Dict[str, Any]
    ) -> SpecificationAnalysis:
        """Guide specification understanding with traceability tracking."""
        # First, perform normal analysis
        analysis = await super().guide_specification_understanding(specification)
        
        # Create specification item in traceability matrix
        spec_item = SpecificationItem(
            requirement_id=specification.get("id", f"SPEC-{len(self.tracker.matrix.specifications) + 1}"),
            name=specification.get("name", "Unnamed Specification"),
            description=specification.get("description", ""),
            priority=specification.get("priority", 5),
            acceptance_criteria=specification.get("acceptance_criteria", []),
        )
        
        # Extract tags from specification
        if "tags" in specification:
            for tag in specification["tags"]:
                spec_item.add_tag(tag)
        
        # Add to matrix
        self.tracker.matrix.add_specification(spec_item)
        
        # Store spec ID in analysis for reference
        analysis.metadata["spec_id"] = str(spec_item.id)
        analysis.metadata["requirement_id"] = spec_item.requirement_id
        
        return analysis
    
    async def guide_implementation_choice(
        self,
        specification: Dict[str, Any],
        analysis: Optional[SpecificationAnalysis] = None
    ) -> ImplementationChoice:
        """Guide implementation choice with traceability tracking."""
        # Perform normal implementation guidance
        choice = await super().guide_implementation_choice(specification, analysis)
        
        # Create implementation item
        impl_item = ImplementationItem(
            name=choice.approach["name"],
            description=choice.rationale,
            file_path=choice.approach.get("file_path", "TBD"),
            function_name=choice.approach.get("function_name", ""),
            class_name=choice.approach.get("class_name", ""),
            complexity_score=choice.approach.get("complexity", 5.0),
        )
        
        # Add to matrix
        self.tracker.matrix.add_implementation(impl_item)
        
        # Create link to specification
        if analysis and "spec_id" in analysis.metadata:
            spec_id = analysis.metadata["spec_id"]
            # Find spec by ID string
            for sid, spec in self.tracker.matrix.specifications.items():
                if str(sid) == spec_id:
                    link = TraceLink(
                        source_id=sid,
                        target_id=impl_item.id,
                        link_type=TraceLinkType.IMPLEMENTS,
                        confidence=0.95,  # High confidence for guided implementation
                    )
                    link.add_evidence("Implementation chosen by VIBEZENGuard")
                    self.tracker.matrix.add_link(link)
                    break
        
        # Store impl ID in choice for reference
        choice.metadata["impl_id"] = str(impl_item.id)
        
        return choice
    
    async def review_code_quality(
        self,
        implementation: str,
        specification: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """Review code quality with traceability updates."""
        # Perform normal quality review
        report = await super().review_code_quality(implementation, specification, context)
        
        # Update implementation status based on quality report
        if context and "impl_id" in context:
            impl_id_str = context["impl_id"]
            for iid, impl in self.tracker.matrix.implementations.items():
                if str(iid) == impl_id_str:
                    if report.overall_assessment == "excellent":
                        impl.update_status(TraceabilityStatus.IMPLEMENTED)
                    elif report.overall_assessment in ["good", "acceptable"]:
                        impl.update_status(TraceabilityStatus.IN_PROGRESS)
                    else:
                        impl.update_status(TraceabilityStatus.FAILED)
                    
                    # Update complexity score
                    if "complexity" in report.metrics:
                        impl.complexity_score = report.metrics["complexity"]
                    
                    break
        
        return report
    
    def parse_project_files(
        self,
        project_path: Path,
        spec_patterns: List[str] = None,
        impl_patterns: List[str] = None,
        test_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """Parse project files to build traceability matrix."""
        if spec_patterns is None:
            spec_patterns = ["**/specs/*.md", "**/requirements/*.md", "**/docs/requirements.md"]
        if impl_patterns is None:
            impl_patterns = ["**/*.py"]
        if test_patterns is None:
            test_patterns = ["**/test_*.py", "**/*_test.py", "**/tests/*.py"]
        
        results = {
            "specifications": [],
            "implementations": [],
            "tests": [],
            "discovered_links": [],
        }
        
        # Parse specification files
        for pattern in spec_patterns:
            for spec_file in project_path.glob(pattern):
                if spec_file.is_file():
                    specs = self.tracker.parse_specification_file(spec_file)
                    results["specifications"].extend(specs)
        
        # Parse implementation files
        for pattern in impl_patterns:
            for impl_file in project_path.glob(pattern):
                if impl_file.is_file() and not any(
                    test_pattern.replace("**", "") in str(impl_file) 
                    for test_pattern in test_patterns
                ):
                    impls = self.tracker.parse_implementation_file(impl_file)
                    results["implementations"].extend(impls)
        
        # Parse test files
        for pattern in test_patterns:
            for test_file in project_path.glob(pattern):
                if test_file.is_file():
                    tests = self.tracker.parse_test_file(test_file)
                    results["tests"].extend(tests)
        
        # Auto-discover links if enabled
        if self.auto_discover_links:
            discovered = self.tracker.auto_discover_links(self.link_confidence_threshold)
            results["discovered_links"].extend(discovered)
        
        return results
    
    def get_coverage_report(self) -> CoverageReport:
        """Get the current coverage report."""
        return self.analyzer.generate_coverage_report()
    
    def analyze_change_impact(self, item_id: str) -> ImpactAnalysis:
        """Analyze the impact of changing an item."""
        # Convert string ID to UUID
        for uid in list(self.tracker.matrix.specifications.keys()) + \
                   list(self.tracker.matrix.implementations.keys()) + \
                   list(self.tracker.matrix.tests.keys()):
            if str(uid) == item_id:
                return self.analyzer.analyze_impact(uid)
        
        raise ValueError(f"Item {item_id} not found in traceability matrix")
    
    def get_unimplemented_specs(self) -> List[SpecificationItem]:
        """Get specifications that haven't been implemented yet."""
        return self.tracker.matrix.get_unimplemented_specs()
    
    def get_untested_implementations(self) -> List[ImplementationItem]:
        """Get implementations that don't have tests."""
        return self.tracker.matrix.get_untested_implementations()
    
    def generate_traceability_report(self, output_dir: Path) -> None:
        """Generate comprehensive traceability reports."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate HTML report
        html_path = output_dir / "traceability_report.html"
        self.visualizer.generate_html_report(html_path)
        
        # Generate JSON export
        json_path = output_dir / "traceability_data.json"
        self.visualizer.export_to_json(json_path)
        
        # Generate Mermaid diagram
        mermaid_path = output_dir / "traceability_diagram.mmd"
        mermaid_content = self.visualizer.generate_mermaid_diagram()
        mermaid_path.write_text(mermaid_content, encoding='utf-8')
        
        # Generate PlantUML diagram
        plantuml_path = output_dir / "traceability_diagram.puml"
        plantuml_content = self.visualizer.generate_plantuml_diagram()
        plantuml_path.write_text(plantuml_content, encoding='utf-8')
        
        # Generate coverage summary
        summary_path = output_dir / "coverage_summary.txt"
        report = self.get_coverage_report()
        summary = f"""
VIBEZEN Traceability Coverage Summary
=====================================

Overall Coverage:
- Specification Coverage: {report.specification_coverage:.1f}%
- Test Coverage: {report.test_coverage:.1f}%
- Verification Coverage: {report.verification_coverage:.1f}%

Specifications:
- Total: {report.total_specifications}
- Implemented: {report.implemented_specifications}
- Tested: {report.tested_specifications}
- Verified: {report.verified_specifications}

Implementations:
- Total: {report.total_implementations}
- Tested: {report.tested_implementations}

Tests:
- Total: {report.total_tests}
- Passing: {report.passing_tests}
- Failing: {report.failing_tests}

Issues:
- Unimplemented Specs: {len(report.unimplemented_specs)}
- High Priority Unimplemented: {len(report.high_priority_unimplemented)}
- Untested Implementations: {len(report.untested_implementations)}
- Complex Untested: {len(report.complex_untested)}
- Over-implementations: {len(report.over_implementations)}
- Orphan Tests: {len(report.orphan_tests)}
"""
        summary_path.write_text(summary, encoding='utf-8')
    
    async def validate_traceability(self) -> Dict[str, Any]:
        """Validate the traceability matrix for completeness and consistency."""
        issues = {
            "errors": [],
            "warnings": [],
            "info": [],
        }
        
        # Check for circular dependencies
        cycles = self.analyzer.find_circular_dependencies()
        if cycles:
            for cycle in cycles:
                cycle_desc = " -> ".join([str(node_id) for node_id in cycle])
                issues["errors"].append(f"Circular dependency detected: {cycle_desc}")
        
        # Check for unimplemented high-priority specs
        report = self.get_coverage_report()
        if report.high_priority_unimplemented:
            for spec in report.high_priority_unimplemented:
                issues["warnings"].append(
                    f"High priority spec not implemented: {spec.requirement_id} - {spec.name}"
                )
        
        # Check for complex untested implementations
        if report.complex_untested:
            for impl in report.complex_untested:
                issues["warnings"].append(
                    f"Complex implementation without tests: {impl.name} (complexity: {impl.complexity_score:.1f})"
                )
        
        # Check for orphan tests
        if report.orphan_tests:
            for test in report.orphan_tests:
                issues["info"].append(
                    f"Orphan test found: {test.name} - doesn't test any implementation or specification"
                )
        
        # Check for over-implementations
        if report.over_implementations:
            for impl in report.over_implementations:
                issues["info"].append(
                    f"Over-implementation detected: {impl.name} - no corresponding specification"
                )
        
        # Check link confidence
        low_confidence_links = []
        for link in self.tracker.matrix.links.values():
            if link.confidence < 0.5:
                low_confidence_links.append(link)
        
        if low_confidence_links:
            for link in low_confidence_links:
                issues["info"].append(
                    f"Low confidence link: {link.link_type.value} with confidence {link.confidence:.2f}"
                )
        
        return {
            "valid": len(issues["errors"]) == 0,
            "issues": issues,
            "metrics": self.analyzer.get_traceability_metrics(),
        }