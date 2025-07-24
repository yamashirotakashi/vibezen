"""
Traceability analyzer for coverage analysis and impact assessment.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from uuid import UUID

from vibezen.traceability.models import (
    SpecificationItem,
    ImplementationItem,
    TestItem,
    TraceLink,
    TraceLinkType,
    TraceabilityStatus,
    TraceabilityMatrix,
)


@dataclass
class CoverageReport:
    """Coverage report for traceability analysis."""
    # Overall metrics
    total_specifications: int = 0
    implemented_specifications: int = 0
    tested_specifications: int = 0
    verified_specifications: int = 0
    
    total_implementations: int = 0
    tested_implementations: int = 0
    
    total_tests: int = 0
    passing_tests: int = 0
    failing_tests: int = 0
    
    # Coverage percentages
    specification_coverage: float = 0.0  # % of specs implemented
    test_coverage: float = 0.0  # % of implementations tested
    verification_coverage: float = 0.0  # % of specs verified by tests
    
    # Detailed lists
    unimplemented_specs: List[SpecificationItem] = field(default_factory=list)
    untested_implementations: List[ImplementationItem] = field(default_factory=list)
    unverified_specs: List[SpecificationItem] = field(default_factory=list)
    orphan_tests: List[TestItem] = field(default_factory=list)
    failing_tests_list: List[TestItem] = field(default_factory=list)
    
    # Over-implementation
    over_implementations: List[ImplementationItem] = field(default_factory=list)
    
    # High priority issues
    high_priority_unimplemented: List[SpecificationItem] = field(default_factory=list)
    complex_untested: List[ImplementationItem] = field(default_factory=list)


@dataclass
class ImpactAnalysis:
    """Impact analysis for changes."""
    changed_item_id: UUID
    changed_item_type: str  # "specification", "implementation", "test"
    
    # Direct impacts
    directly_affected_specs: List[SpecificationItem] = field(default_factory=list)
    directly_affected_impls: List[ImplementationItem] = field(default_factory=list)
    directly_affected_tests: List[TestItem] = field(default_factory=list)
    
    # Indirect impacts (through transitive relationships)
    indirectly_affected_specs: List[SpecificationItem] = field(default_factory=list)
    indirectly_affected_impls: List[ImplementationItem] = field(default_factory=list)
    indirectly_affected_tests: List[TestItem] = field(default_factory=list)
    
    # Risk assessment
    risk_level: str = "low"  # low, medium, high, critical
    risk_factors: List[str] = field(default_factory=list)
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    tests_to_run: List[TestItem] = field(default_factory=list)
    specs_to_review: List[SpecificationItem] = field(default_factory=list)


class TraceabilityAnalyzer:
    """Analyzes traceability data for insights and issues."""
    
    def __init__(self, matrix: TraceabilityMatrix):
        """Initialize analyzer with a traceability matrix."""
        self.matrix = matrix
    
    def generate_coverage_report(self) -> CoverageReport:
        """Generate a comprehensive coverage report."""
        report = CoverageReport()
        
        # Count totals
        report.total_specifications = len(self.matrix.specifications)
        report.total_implementations = len(self.matrix.implementations)
        report.total_tests = len(self.matrix.tests)
        
        # Find unimplemented specifications
        report.unimplemented_specs = self.matrix.get_unimplemented_specs()
        report.implemented_specifications = report.total_specifications - len(report.unimplemented_specs)
        
        # Find untested implementations
        report.untested_implementations = self.matrix.get_untested_implementations()
        report.tested_implementations = report.total_implementations - len(report.untested_implementations)
        
        # Find unverified specifications (no direct or indirect test verification)
        verified_specs = set()
        for test in self.matrix.tests.values():
            # Direct verification
            for link in self.matrix.get_links_from(test.id):
                if link.link_type == TraceLinkType.VERIFIES:
                    verified_specs.add(link.target_id)
            
            # Indirect verification through implementations
            for link in self.matrix.get_links_from(test.id):
                if link.link_type == TraceLinkType.TESTS:
                    impl_id = link.target_id
                    # Find specs implemented by this implementation
                    for impl_link in self.matrix.get_links_to(impl_id):
                        if impl_link.link_type == TraceLinkType.IMPLEMENTS:
                            verified_specs.add(impl_link.source_id)
        
        report.verified_specifications = len(verified_specs)
        report.unverified_specs = [
            spec for spec_id, spec in self.matrix.specifications.items()
            if spec_id not in verified_specs
        ]
        report.tested_specifications = report.verified_specifications
        
        # Find orphan tests
        report.orphan_tests = self.matrix.get_orphan_tests()
        
        # Count test results
        for test in self.matrix.tests.values():
            if test.last_result is True:
                report.passing_tests += 1
            elif test.last_result is False:
                report.failing_tests += 1
                report.failing_tests_list.append(test)
        
        # Calculate coverage percentages
        if report.total_specifications > 0:
            report.specification_coverage = (
                report.implemented_specifications / report.total_specifications * 100
            )
            report.verification_coverage = (
                report.verified_specifications / report.total_specifications * 100
            )
        
        if report.total_implementations > 0:
            report.test_coverage = (
                report.tested_implementations / report.total_implementations * 100
            )
        
        # Find over-implementations (implementations without corresponding specs)
        spec_linked_impls = set()
        for link in self.matrix.get_links_of_type(TraceLinkType.IMPLEMENTS):
            spec_linked_impls.add(link.target_id)
        
        report.over_implementations = [
            impl for impl_id, impl in self.matrix.implementations.items()
            if impl_id not in spec_linked_impls
        ]
        
        # Find high priority unimplemented specs
        report.high_priority_unimplemented = [
            spec for spec in report.unimplemented_specs
            if spec.is_high_priority()
        ]
        
        # Find complex untested implementations
        report.complex_untested = [
            impl for impl in report.untested_implementations
            if impl.is_complex()
        ]
        
        return report
    
    def analyze_impact(self, item_id: UUID) -> ImpactAnalysis:
        """Analyze the impact of changing an item."""
        analysis = ImpactAnalysis(changed_item_id=item_id)
        
        # Determine item type
        if item_id in self.matrix.specifications:
            analysis.changed_item_type = "specification"
            self._analyze_spec_impact(item_id, analysis)
        elif item_id in self.matrix.implementations:
            analysis.changed_item_type = "implementation"
            self._analyze_impl_impact(item_id, analysis)
        elif item_id in self.matrix.tests:
            analysis.changed_item_type = "test"
            self._analyze_test_impact(item_id, analysis)
        else:
            raise ValueError(f"Item {item_id} not found in matrix")
        
        # Assess risk level
        self._assess_risk(analysis)
        
        # Generate recommendations
        self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_spec_impact(self, spec_id: UUID, analysis: ImpactAnalysis) -> None:
        """Analyze impact of specification change."""
        spec = self.matrix.specifications[spec_id]
        
        # Direct impacts: implementations and tests
        for impl in self.matrix.get_implementations_for_spec(spec_id):
            analysis.directly_affected_impls.append(impl)
        
        for test in self.matrix.get_tests_for_spec(spec_id):
            analysis.directly_affected_tests.append(test)
        
        # Indirect impacts: derived specifications
        for link in self.matrix.get_links_from(spec_id):
            if link.link_type == TraceLinkType.DERIVED_FROM:
                derived_spec_id = link.target_id
                if derived_spec_id in self.matrix.specifications:
                    derived_spec = self.matrix.specifications[derived_spec_id]
                    analysis.indirectly_affected_specs.append(derived_spec)
                    
                    # Their implementations and tests are also indirectly affected
                    for impl in self.matrix.get_implementations_for_spec(derived_spec_id):
                        if impl not in analysis.indirectly_affected_impls:
                            analysis.indirectly_affected_impls.append(impl)
                    
                    for test in self.matrix.get_tests_for_spec(derived_spec_id):
                        if test not in analysis.indirectly_affected_tests:
                            analysis.indirectly_affected_tests.append(test)
        
        # Risk factors
        if spec.is_high_priority():
            analysis.risk_factors.append("High priority specification")
        
        if len(analysis.directly_affected_impls) > 3:
            analysis.risk_factors.append(f"Affects {len(analysis.directly_affected_impls)} implementations")
        
        if len(analysis.indirectly_affected_specs) > 0:
            analysis.risk_factors.append(f"Has {len(analysis.indirectly_affected_specs)} derived specifications")
    
    def _analyze_impl_impact(self, impl_id: UUID, analysis: ImpactAnalysis) -> None:
        """Analyze impact of implementation change."""
        impl = self.matrix.implementations[impl_id]
        
        # Direct impacts: tests that test this implementation
        for test in self.matrix.get_tests_for_implementation(impl_id):
            analysis.directly_affected_tests.append(test)
        
        # Find specifications this implements
        for link in self.matrix.get_links_to(impl_id):
            if link.link_type == TraceLinkType.IMPLEMENTS:
                spec_id = link.source_id
                if spec_id in self.matrix.specifications:
                    analysis.directly_affected_specs.append(self.matrix.specifications[spec_id])
        
        # Indirect impacts: other implementations that depend on this
        for link in self.matrix.get_links_from(impl_id):
            if link.link_type == TraceLinkType.DEPENDS_ON:
                dep_impl_id = link.target_id
                if dep_impl_id in self.matrix.implementations:
                    dep_impl = self.matrix.implementations[dep_impl_id]
                    analysis.indirectly_affected_impls.append(dep_impl)
                    
                    # Tests for dependent implementations
                    for test in self.matrix.get_tests_for_implementation(dep_impl_id):
                        if test not in analysis.indirectly_affected_tests:
                            analysis.indirectly_affected_tests.append(test)
        
        # Risk factors
        if impl.is_complex():
            analysis.risk_factors.append("Complex implementation")
        
        if len(analysis.directly_affected_tests) == 0:
            analysis.risk_factors.append("No tests for this implementation")
        
        if len(analysis.indirectly_affected_impls) > 0:
            analysis.risk_factors.append(f"{len(analysis.indirectly_affected_impls)} dependent implementations")
    
    def _analyze_test_impact(self, test_id: UUID, analysis: ImpactAnalysis) -> None:
        """Analyze impact of test change."""
        test = self.matrix.tests[test_id]
        
        # Find implementations this test covers
        for link in self.matrix.get_links_from(test_id):
            if link.link_type == TraceLinkType.TESTS:
                impl_id = link.target_id
                if impl_id in self.matrix.implementations:
                    analysis.directly_affected_impls.append(self.matrix.implementations[impl_id])
            elif link.link_type == TraceLinkType.VERIFIES:
                spec_id = link.target_id
                if spec_id in self.matrix.specifications:
                    analysis.directly_affected_specs.append(self.matrix.specifications[spec_id])
        
        # Risk factors
        if test.last_result is False:
            analysis.risk_factors.append("Currently failing test")
        
        if test.test_type in ["integration", "system", "acceptance"]:
            analysis.risk_factors.append(f"High-level {test.test_type} test")
    
    def _assess_risk(self, analysis: ImpactAnalysis) -> None:
        """Assess the risk level based on impact analysis."""
        risk_score = 0
        
        # Count affected items
        total_affected = (
            len(analysis.directly_affected_specs) +
            len(analysis.directly_affected_impls) +
            len(analysis.directly_affected_tests) +
            len(analysis.indirectly_affected_specs) +
            len(analysis.indirectly_affected_impls) +
            len(analysis.indirectly_affected_tests)
        )
        
        if total_affected > 20:
            risk_score += 3
        elif total_affected > 10:
            risk_score += 2
        elif total_affected > 5:
            risk_score += 1
        
        # Risk factors
        risk_score += len(analysis.risk_factors)
        
        # High priority specs
        high_priority_affected = sum(
            1 for spec in analysis.directly_affected_specs + analysis.indirectly_affected_specs
            if spec.is_high_priority()
        )
        risk_score += high_priority_affected * 2
        
        # Determine risk level
        if risk_score >= 8:
            analysis.risk_level = "critical"
        elif risk_score >= 5:
            analysis.risk_level = "high"
        elif risk_score >= 2:
            analysis.risk_level = "medium"
        else:
            analysis.risk_level = "low"
    
    def _generate_recommendations(self, analysis: ImpactAnalysis) -> None:
        """Generate recommendations based on impact analysis."""
        # Tests to run
        analysis.tests_to_run = (
            analysis.directly_affected_tests +
            [t for t in analysis.indirectly_affected_tests if t not in analysis.directly_affected_tests]
        )
        
        # Specs to review
        analysis.specs_to_review = (
            analysis.directly_affected_specs +
            [s for s in analysis.indirectly_affected_specs if s not in analysis.directly_affected_specs]
        )
        
        # Recommendations based on change type
        if analysis.changed_item_type == "specification":
            analysis.recommended_actions.append("Review all implementations of this specification")
            analysis.recommended_actions.append("Update related test cases")
            if analysis.risk_level in ["high", "critical"]:
                analysis.recommended_actions.append("Conduct formal review before implementation")
        
        elif analysis.changed_item_type == "implementation":
            analysis.recommended_actions.append("Run all related tests")
            if len(analysis.directly_affected_tests) == 0:
                analysis.recommended_actions.append("CREATE TESTS for this implementation (currently untested!)")
            if analysis.risk_level in ["high", "critical"]:
                analysis.recommended_actions.append("Perform code review")
                analysis.recommended_actions.append("Run integration tests")
        
        elif analysis.changed_item_type == "test":
            analysis.recommended_actions.append("Verify test still accurately reflects requirements")
            if analysis.risk_factors:
                analysis.recommended_actions.append("Review test implementation for correctness")
        
        # General recommendations based on risk
        if analysis.risk_level == "critical":
            analysis.recommended_actions.append("CRITICAL: Extensive testing required")
            analysis.recommended_actions.append("Consider phased rollout")
            analysis.recommended_actions.append("Prepare rollback plan")
        elif analysis.risk_level == "high":
            analysis.recommended_actions.append("Thorough regression testing recommended")
            analysis.recommended_actions.append("Monitor closely after deployment")
    
    def find_circular_dependencies(self) -> List[List[UUID]]:
        """Find circular dependencies in the traceability graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: UUID, path: List[UUID]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            # Check all outgoing links
            for link in self.matrix.get_links_from(node_id):
                if link.link_type in [TraceLinkType.DEPENDS_ON, TraceLinkType.DERIVED_FROM]:
                    target_id = link.target_id
                    
                    if target_id not in visited:
                        dfs(target_id, path.copy())
                    elif target_id in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(target_id)
                        cycle = path[cycle_start:] + [target_id]
                        cycles.append(cycle)
            
            rec_stack.remove(node_id)
        
        # Check all nodes
        all_nodes = (
            set(self.matrix.specifications.keys()) |
            set(self.matrix.implementations.keys()) |
            set(self.matrix.tests.keys())
        )
        
        for node_id in all_nodes:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def get_traceability_metrics(self) -> Dict[str, Any]:
        """Get key traceability metrics."""
        report = self.generate_coverage_report()
        
        return {
            "specification_metrics": {
                "total": report.total_specifications,
                "implemented": report.implemented_specifications,
                "verified": report.verified_specifications,
                "coverage_percentage": report.specification_coverage,
                "high_priority_missing": len(report.high_priority_unimplemented),
            },
            "implementation_metrics": {
                "total": report.total_implementations,
                "tested": report.tested_implementations,
                "test_coverage_percentage": report.test_coverage,
                "over_implementations": len(report.over_implementations),
                "complex_untested": len(report.complex_untested),
            },
            "test_metrics": {
                "total": report.total_tests,
                "passing": report.passing_tests,
                "failing": report.failing_tests,
                "orphaned": len(report.orphan_tests),
                "pass_rate": (report.passing_tests / report.total_tests * 100) if report.total_tests > 0 else 0,
            },
            "link_metrics": {
                "total_links": len(self.matrix.links),
                "implements_links": len(self.matrix.get_links_of_type(TraceLinkType.IMPLEMENTS)),
                "tests_links": len(self.matrix.get_links_of_type(TraceLinkType.TESTS)),
                "verifies_links": len(self.matrix.get_links_of_type(TraceLinkType.VERIFIES)),
            },
            "quality_indicators": {
                "has_circular_dependencies": len(self.find_circular_dependencies()) > 0,
                "untested_ratio": (len(report.untested_implementations) / report.total_implementations * 100) 
                                if report.total_implementations > 0 else 0,
                "unimplemented_ratio": (len(report.unimplemented_specs) / report.total_specifications * 100)
                                     if report.total_specifications > 0 else 0,
            }
        }