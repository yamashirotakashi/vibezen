"""
Tests for VIBEZEN traceability management system.
"""

import pytest
from pathlib import Path
from uuid import uuid4
import tempfile
import json

from vibezen.traceability import (
    SpecificationItem,
    ImplementationItem,
    TestItem,
    TraceLink,
    TraceLinkType,
    TraceabilityStatus,
    TraceabilityMatrix,
    TraceabilityTracker,
    TraceabilityAnalyzer,
    TraceabilityVisualizer,
    CoverageReport,
    ImpactAnalysis,
)
from vibezen.core.guard_v2_traceability import VIBEZENGuardV2WithTraceability


@pytest.fixture
def sample_matrix():
    """Create a sample traceability matrix for testing."""
    matrix = TraceabilityMatrix()
    
    # Add specifications
    spec1 = SpecificationItem(
        requirement_id="REQ-001",
        name="User Authentication",
        description="System shall provide secure user authentication",
        priority=9,
        acceptance_criteria=["Users can login", "Passwords are encrypted"],
    )
    spec2 = SpecificationItem(
        requirement_id="REQ-002",
        name="Data Validation",
        description="System shall validate all input data",
        priority=7,
    )
    spec3 = SpecificationItem(
        requirement_id="REQ-003",
        name="Logging",
        description="System shall log all activities",
        priority=5,
    )
    
    matrix.add_specification(spec1)
    matrix.add_specification(spec2)
    matrix.add_specification(spec3)
    
    # Add implementations
    impl1 = ImplementationItem(
        name="authenticate_user",
        file_path="src/auth.py",
        line_start=10,
        line_end=50,
        function_name="authenticate_user",
        complexity_score=8.0,
    )
    impl2 = ImplementationItem(
        name="validate_input",
        file_path="src/validation.py",
        line_start=5,
        line_end=25,
        function_name="validate_input",
        complexity_score=5.0,
    )
    
    matrix.add_implementation(impl1)
    matrix.add_implementation(impl2)
    
    # Add tests
    test1 = TestItem(
        name="test_authentication",
        test_type="unit",
        test_file="tests/test_auth.py",
        test_method="test_authentication",
        coverage_percentage=85.0,
    )
    test2 = TestItem(
        name="test_validation", 
        test_type="unit",
        test_file="tests/test_validation.py",
        test_method="test_validation",
        coverage_percentage=90.0,
    )
    test3 = TestItem(
        name="test_orphan",
        test_type="unit",
        test_file="tests/test_orphan.py",
        test_method="test_orphan",
    )
    
    matrix.add_test(test1)
    matrix.add_test(test2)
    matrix.add_test(test3)
    
    # Add links
    # spec1 -> impl1
    link1 = TraceLink(
        source_id=spec1.id,
        target_id=impl1.id,
        link_type=TraceLinkType.IMPLEMENTS,
        confidence=0.9,
    )
    matrix.add_link(link1)
    
    # spec2 -> impl2
    link2 = TraceLink(
        source_id=spec2.id,
        target_id=impl2.id,
        link_type=TraceLinkType.IMPLEMENTS,
        confidence=0.85,
    )
    matrix.add_link(link2)
    
    # test1 -> impl1
    link3 = TraceLink(
        source_id=test1.id,
        target_id=impl1.id,
        link_type=TraceLinkType.TESTS,
        confidence=0.95,
    )
    matrix.add_link(link3)
    
    # test2 -> impl2
    link4 = TraceLink(
        source_id=test2.id,
        target_id=impl2.id,
        link_type=TraceLinkType.TESTS,
        confidence=0.9,
    )
    matrix.add_link(link4)
    
    # test1 -> spec1 (verifies)
    link5 = TraceLink(
        source_id=test1.id,
        target_id=spec1.id,
        link_type=TraceLinkType.VERIFIES,
        confidence=0.8,
    )
    matrix.add_link(link5)
    
    return matrix


class TestTraceabilityModels:
    """Test traceability models."""
    
    def test_specification_item(self):
        """Test specification item creation and methods."""
        spec = SpecificationItem(
            requirement_id="REQ-001",
            name="Test Requirement",
            priority=8,
        )
        
        assert spec.requirement_id == "REQ-001"
        assert spec.name == "Test Requirement"
        assert spec.priority == 8
        assert spec.is_high_priority() is True
        
        # Test adding acceptance criteria
        spec.add_acceptance_criterion("Must do X")
        assert len(spec.acceptance_criteria) == 1
        assert "Must do X" in spec.acceptance_criteria
    
    def test_implementation_item(self):
        """Test implementation item creation and methods."""
        impl = ImplementationItem(
            name="test_function",
            file_path="src/test.py",
            line_start=10,
            line_end=20,
            complexity_score=15.0,
        )
        
        assert impl.name == "test_function"
        assert impl.get_location() == "src/test.py:10-20"
        assert impl.is_complex() is True
        assert impl.is_complex(20.0) is False
    
    def test_test_item(self):
        """Test test item creation and methods."""
        test = TestItem(
            name="test_example",
            test_type="unit",
            test_file="tests/test_example.py",
        )
        
        assert test.name == "test_example"
        assert test.test_type == "unit"
        assert test.is_passing() is False
        
        # Test marking as passed
        test.mark_passed()
        assert test.is_passing() is True
        assert test.last_result is True
        assert test.status == TraceabilityStatus.VERIFIED
        
        # Test marking as failed
        test.mark_failed()
        assert test.is_passing() is False
        assert test.last_result is False
        assert test.status == TraceabilityStatus.FAILED
    
    def test_trace_link(self):
        """Test trace link creation and methods."""
        link = TraceLink(
            source_id=uuid4(),
            target_id=uuid4(),
            link_type=TraceLinkType.IMPLEMENTS,
            confidence=0.85,
        )
        
        assert link.link_type == TraceLinkType.IMPLEMENTS
        assert link.confidence == 0.85
        assert link.is_strong_link() is True
        
        # Test adding evidence
        link.add_evidence("Found in docstring")
        assert len(link.evidence) == 1


class TestTraceabilityMatrix:
    """Test traceability matrix functionality."""
    
    def test_matrix_operations(self, sample_matrix):
        """Test basic matrix operations."""
        # Check counts
        assert len(sample_matrix.specifications) == 3
        assert len(sample_matrix.implementations) == 2
        assert len(sample_matrix.tests) == 3
        assert len(sample_matrix.links) == 5
    
    def test_get_implementations_for_spec(self, sample_matrix):
        """Test getting implementations for a specification."""
        # Get spec1
        spec1 = next(s for s in sample_matrix.specifications.values() 
                    if s.requirement_id == "REQ-001")
        
        impls = sample_matrix.get_implementations_for_spec(spec1.id)
        assert len(impls) == 1
        assert impls[0].name == "authenticate_user"
    
    def test_get_tests_for_implementation(self, sample_matrix):
        """Test getting tests for an implementation."""
        # Get impl1
        impl1 = next(i for i in sample_matrix.implementations.values()
                    if i.name == "authenticate_user")
        
        tests = sample_matrix.get_tests_for_implementation(impl1.id)
        assert len(tests) == 1
        assert tests[0].name == "test_authentication"
    
    def test_get_unimplemented_specs(self, sample_matrix):
        """Test getting unimplemented specifications."""
        unimplemented = sample_matrix.get_unimplemented_specs()
        assert len(unimplemented) == 1
        assert unimplemented[0].requirement_id == "REQ-003"
    
    def test_get_untested_implementations(self, sample_matrix):
        """Test getting untested implementations."""
        untested = sample_matrix.get_untested_implementations()
        assert len(untested) == 0  # All implementations have tests
    
    def test_get_orphan_tests(self, sample_matrix):
        """Test getting orphan tests."""
        orphans = sample_matrix.get_orphan_tests()
        assert len(orphans) == 1
        assert orphans[0].name == "test_orphan"


class TestTraceabilityTracker:
    """Test traceability tracker functionality."""
    
    def test_parse_specification_file(self, tmp_path):
        """Test parsing specification files."""
        spec_file = tmp_path / "requirements.md"
        spec_file.write_text("""
# REQ-001: User Authentication [Priority: 9]
The system shall provide secure user authentication.

## Acceptance Criteria
- Users can login with username and password
- Passwords are stored encrypted
- Session timeout after 30 minutes

# REQ-002: Data Validation
All user input must be validated.
""")
        
        tracker = TraceabilityTracker()
        specs = tracker.parse_specification_file(spec_file)
        
        assert len(specs) == 2
        assert specs[0].requirement_id == "001"
        assert specs[0].priority == 9
        assert len(specs[0].acceptance_criteria) == 3
        assert specs[1].requirement_id == "002"
    
    def test_parse_implementation_file(self, tmp_path):
        """Test parsing implementation files."""
        impl_file = tmp_path / "auth.py"
        impl_file.write_text('''
def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user.
    
    Implements: REQ-001
    """
    # Complex authentication logic
    if username and password:
        return True
    return False

class UserManager:
    """Manages users. @implements REQ-001"""
    pass
''')
        
        tracker = TraceabilityTracker()
        impls = tracker.parse_implementation_file(impl_file)
        
        assert len(impls) == 2
        assert impls[0].name == "authenticate_user"
        assert impls[0].function_name == "authenticate_user"
        assert "implements:REQ-001" in impls[0].tags
        assert impls[1].name == "UserManager"
        assert impls[1].class_name == "UserManager"
    
    def test_parse_test_file(self, tmp_path):
        """Test parsing test files."""
        test_file = tmp_path / "test_auth.py"
        test_file.write_text('''
import pytest

def test_authenticate_user():
    """
    Test user authentication.
    
    Tests: authenticate_user
    Verifies: REQ-001
    """
    assert authenticate_user("user", "pass") is True
    assert authenticate_user("", "") is False

@pytest.mark.integration
def test_user_login_flow():
    """Integration test for login flow."""
    pass
''')
        
        tracker = TraceabilityTracker()
        tests = tracker.parse_test_file(test_file)
        
        assert len(tests) == 2
        assert tests[0].name == "test_authenticate_user"
        assert "verifies:REQ-001" in tests[0].tags
        assert "tests:authenticate_user" in tests[0].tags
        assert tests[1].test_type == "unit"  # Default type
    
    def test_auto_discover_links(self, sample_matrix):
        """Test automatic link discovery."""
        tracker = TraceabilityTracker(sample_matrix)
        
        # Add a new implementation without explicit links
        impl3 = ImplementationItem(
            name="logging_handler",
            description="Handles system logging for all activities",
        )
        tracker.matrix.add_implementation(impl3)
        
        # Discover links
        discovered = tracker.auto_discover_links(confidence_threshold=0.6)
        
        # Should find link between "Logging" spec and "logging_handler" impl
        assert len(discovered) > 0


class TestTraceabilityAnalyzer:
    """Test traceability analyzer functionality."""
    
    def test_generate_coverage_report(self, sample_matrix):
        """Test coverage report generation."""
        analyzer = TraceabilityAnalyzer(sample_matrix)
        report = analyzer.generate_coverage_report()
        
        assert report.total_specifications == 3
        assert report.implemented_specifications == 2
        assert report.specification_coverage == pytest.approx(66.67, 0.1)
        
        assert report.total_implementations == 2
        assert report.tested_implementations == 2
        assert report.test_coverage == 100.0
        
        assert len(report.unimplemented_specs) == 1
        assert len(report.orphan_tests) == 1
        assert len(report.high_priority_unimplemented) == 0  # REQ-003 is not high priority
    
    def test_analyze_impact(self, sample_matrix):
        """Test impact analysis."""
        analyzer = TraceabilityAnalyzer(sample_matrix)
        
        # Get spec1
        spec1 = next(s for s in sample_matrix.specifications.values()
                    if s.requirement_id == "REQ-001")
        
        impact = analyzer.analyze_impact(spec1.id)
        
        assert impact.changed_item_type == "specification"
        assert len(impact.directly_affected_impls) == 1
        assert len(impact.directly_affected_tests) == 1
        assert impact.risk_level in ["low", "medium", "high", "critical"]
        assert len(impact.recommended_actions) > 0
    
    def test_find_circular_dependencies(self):
        """Test circular dependency detection."""
        matrix = TraceabilityMatrix()
        
        # Create items
        spec1 = SpecificationItem(requirement_id="SPEC-1", name="Spec 1")
        spec2 = SpecificationItem(requirement_id="SPEC-2", name="Spec 2")
        spec3 = SpecificationItem(requirement_id="SPEC-3", name="Spec 3")
        
        matrix.add_specification(spec1)
        matrix.add_specification(spec2)
        matrix.add_specification(spec3)
        
        # Create circular dependency: spec1 -> spec2 -> spec3 -> spec1
        link1 = TraceLink(source_id=spec1.id, target_id=spec2.id, link_type=TraceLinkType.DEPENDS_ON)
        link2 = TraceLink(source_id=spec2.id, target_id=spec3.id, link_type=TraceLinkType.DEPENDS_ON)
        link3 = TraceLink(source_id=spec3.id, target_id=spec1.id, link_type=TraceLinkType.DEPENDS_ON)
        
        matrix.add_link(link1)
        matrix.add_link(link2)
        matrix.add_link(link3)
        
        analyzer = TraceabilityAnalyzer(matrix)
        cycles = analyzer.find_circular_dependencies()
        
        assert len(cycles) > 0
    
    def test_get_traceability_metrics(self, sample_matrix):
        """Test getting traceability metrics."""
        analyzer = TraceabilityAnalyzer(sample_matrix)
        metrics = analyzer.get_traceability_metrics()
        
        assert "specification_metrics" in metrics
        assert "implementation_metrics" in metrics
        assert "test_metrics" in metrics
        assert "link_metrics" in metrics
        assert "quality_indicators" in metrics
        
        assert metrics["specification_metrics"]["total"] == 3
        assert metrics["test_metrics"]["orphaned"] == 1


class TestTraceabilityVisualizer:
    """Test traceability visualizer functionality."""
    
    def test_generate_mermaid_diagram(self, sample_matrix):
        """Test Mermaid diagram generation."""
        visualizer = TraceabilityVisualizer(sample_matrix)
        diagram = visualizer.generate_mermaid_diagram()
        
        assert "graph TD" in diagram
        assert "REQ-001" in diagram
        assert "authenticate_user" in diagram
        assert "-->" in diagram  # IMPLEMENTS arrow
        assert "-.->)" in diagram  # TESTS arrow
    
    def test_generate_coverage_heatmap(self, sample_matrix):
        """Test coverage heatmap generation."""
        visualizer = TraceabilityVisualizer(sample_matrix)
        heatmap_data = visualizer.generate_coverage_heatmap()
        
        assert "spec_impl_coverage" in heatmap_data
        assert "impl_test_coverage" in heatmap_data
        assert "summary" in heatmap_data
        
        assert len(heatmap_data["spec_impl_coverage"]["matrix"]) == 3
        assert len(heatmap_data["impl_test_coverage"]["matrix"]) == 2
    
    def test_generate_html_report(self, sample_matrix, tmp_path):
        """Test HTML report generation."""
        visualizer = TraceabilityVisualizer(sample_matrix)
        output_file = tmp_path / "report.html"
        
        visualizer.generate_html_report(output_file)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "VIBEZEN Traceability Report" in content
        assert "Coverage Metrics" in content
        assert "mermaid" in content
    
    def test_export_to_json(self, sample_matrix, tmp_path):
        """Test JSON export."""
        visualizer = TraceabilityVisualizer(sample_matrix)
        output_file = tmp_path / "traceability.json"
        
        visualizer.export_to_json(output_file)
        
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        
        assert "specifications" in data
        assert "implementations" in data
        assert "tests" in data
        assert "links" in data
        assert "metrics" in data


@pytest.mark.asyncio
class TestVIBEZENGuardWithTraceability:
    """Test VIBEZENGuard with traceability integration."""
    
    async def test_guide_specification_with_tracking(self):
        """Test specification guidance with traceability tracking."""
        guard = VIBEZENGuardV2WithTraceability()
        
        spec = {
            "id": "REQ-001",
            "name": "User Authentication",
            "description": "Secure authentication system",
            "priority": 9,
            "tags": ["security", "authentication"],
        }
        
        analysis = await guard.guide_specification_understanding(spec)
        
        # Check that specification was added to matrix
        assert len(guard.tracker.matrix.specifications) == 1
        spec_item = list(guard.tracker.matrix.specifications.values())[0]
        assert spec_item.requirement_id == "REQ-001"
        assert spec_item.priority == 9
        assert "security" in spec_item.tags
        
        # Check metadata
        assert "spec_id" in analysis.metadata
        assert "requirement_id" in analysis.metadata
    
    async def test_guide_implementation_with_tracking(self):
        """Test implementation guidance with traceability tracking."""
        guard = VIBEZENGuardV2WithTraceability()
        
        # First add a specification
        spec = {
            "id": "REQ-001",
            "name": "Data Validation",
            "description": "Validate all inputs",
        }
        analysis = await guard.guide_specification_understanding(spec)
        
        # Then guide implementation
        choice = await guard.guide_implementation_choice(spec, analysis)
        
        # Check that implementation was added and linked
        assert len(guard.tracker.matrix.implementations) == 1
        impl_item = list(guard.tracker.matrix.implementations.values())[0]
        
        # Check link was created
        assert len(guard.tracker.matrix.links) == 1
        link = list(guard.tracker.matrix.links.values())[0]
        assert link.link_type == TraceLinkType.IMPLEMENTS
        assert link.confidence == 0.95
    
    def test_parse_project_files(self, tmp_path):
        """Test parsing project files."""
        guard = VIBEZENGuardV2WithTraceability()
        
        # Create project structure
        (tmp_path / "specs").mkdir()
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        
        # Create a spec file
        spec_file = tmp_path / "specs" / "requirements.md"
        spec_file.write_text("# REQ-001: Test Requirement\nTest description")
        
        # Create an implementation file
        impl_file = tmp_path / "src" / "module.py"
        impl_file.write_text('def test_func():\n    """Implements REQ-001"""\n    pass')
        
        # Create a test file
        test_file = tmp_path / "tests" / "test_module.py"
        test_file.write_text('def test_func():\n    """Tests test_func"""\n    pass')
        
        # Parse files
        results = guard.parse_project_files(tmp_path)
        
        assert len(results["specifications"]) == 1
        assert len(results["implementations"]) == 1
        assert len(results["tests"]) == 1
    
    def test_get_coverage_report(self, sample_matrix):
        """Test getting coverage report from guard."""
        guard = VIBEZENGuardV2WithTraceability()
        guard.tracker.matrix = sample_matrix
        guard.analyzer = TraceabilityAnalyzer(sample_matrix)
        
        report = guard.get_coverage_report()
        
        assert isinstance(report, CoverageReport)
        assert report.total_specifications == 3
    
    def test_generate_traceability_report(self, sample_matrix, tmp_path):
        """Test generating full traceability report."""
        guard = VIBEZENGuardV2WithTraceability()
        guard.tracker.matrix = sample_matrix
        guard.analyzer = TraceabilityAnalyzer(sample_matrix)
        guard.visualizer = TraceabilityVisualizer(sample_matrix)
        
        output_dir = tmp_path / "reports"
        guard.generate_traceability_report(output_dir)
        
        assert (output_dir / "traceability_report.html").exists()
        assert (output_dir / "traceability_data.json").exists()
        assert (output_dir / "traceability_diagram.mmd").exists()
        assert (output_dir / "coverage_summary.txt").exists()
    
    async def test_validate_traceability(self, sample_matrix):
        """Test traceability validation."""
        guard = VIBEZENGuardV2WithTraceability()
        guard.tracker.matrix = sample_matrix
        guard.analyzer = TraceabilityAnalyzer(sample_matrix)
        
        validation = await guard.validate_traceability()
        
        assert "valid" in validation
        assert "issues" in validation
        assert "metrics" in validation
        
        # Should have warnings for unimplemented spec
        assert len(validation["issues"]["warnings"]) > 0