"""
Traceability models for VIBEZEN.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from uuid import UUID, uuid4


class TraceLinkType(Enum):
    """Types of traceability links."""
    IMPLEMENTS = "implements"  # Implementation implements specification
    TESTS = "tests"  # Test tests implementation
    VERIFIES = "verifies"  # Test verifies specification
    DERIVED_FROM = "derived_from"  # Specification derived from another
    RELATED_TO = "related_to"  # General relationship
    CONFLICTS_WITH = "conflicts_with"  # Items conflict with each other
    DEPENDS_ON = "depends_on"  # Dependency relationship


class TraceabilityStatus(Enum):
    """Status of traceability items."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    VERIFIED = "verified"
    OBSOLETE = "obsolete"
    FAILED = "failed"


@dataclass
class TraceableItem:
    """Base class for traceable items."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    status: TraceabilityStatus = TraceabilityStatus.NOT_STARTED
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_status(self, new_status: TraceabilityStatus) -> None:
        """Update the status of the item."""
        self.status = new_status
        self.modified_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the item."""
        self.tags.add(tag)
        self.modified_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the item."""
        self.tags.discard(tag)
        self.modified_at = datetime.utcnow()


@dataclass
class SpecificationItem(TraceableItem):
    """Represents a specification item."""
    requirement_id: str = ""
    priority: int = 0  # 0=lowest, 10=highest
    source: str = ""  # Source document or reference
    rationale: str = ""  # Why this requirement exists
    acceptance_criteria: List[str] = field(default_factory=list)
    
    def is_high_priority(self) -> bool:
        """Check if this is a high priority specification."""
        return self.priority >= 7
    
    def add_acceptance_criterion(self, criterion: str) -> None:
        """Add an acceptance criterion."""
        self.acceptance_criteria.append(criterion)
        self.modified_at = datetime.utcnow()


@dataclass
class ImplementationItem(TraceableItem):
    """Represents an implementation item."""
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    function_name: str = ""
    class_name: str = ""
    complexity_score: float = 0.0
    implementation_notes: str = ""
    
    def get_location(self) -> str:
        """Get the location string for this implementation."""
        location = self.file_path
        if self.line_start > 0:
            location += f":{self.line_start}"
            if self.line_end > self.line_start:
                location += f"-{self.line_end}"
        return location
    
    def is_complex(self, threshold: float = 10.0) -> bool:
        """Check if this implementation is complex."""
        return self.complexity_score > threshold


@dataclass
class TestItem(TraceableItem):
    """Represents a test item."""
    test_type: str = "unit"  # unit, integration, system, acceptance
    test_file: str = ""
    test_method: str = ""
    assertions: List[str] = field(default_factory=list)
    coverage_percentage: float = 0.0
    last_run_at: Optional[datetime] = None
    last_result: Optional[bool] = None  # True=passed, False=failed, None=not run
    
    def mark_passed(self) -> None:
        """Mark the test as passed."""
        self.last_result = True
        self.last_run_at = datetime.utcnow()
        self.status = TraceabilityStatus.VERIFIED
        self.modified_at = datetime.utcnow()
    
    def mark_failed(self) -> None:
        """Mark the test as failed."""
        self.last_result = False
        self.last_run_at = datetime.utcnow()
        self.status = TraceabilityStatus.FAILED
        self.modified_at = datetime.utcnow()
    
    def is_passing(self) -> bool:
        """Check if the test is currently passing."""
        return self.last_result is True


@dataclass
class TraceLink:
    """Represents a link between traceable items."""
    id: UUID = field(default_factory=uuid4)
    source_id: UUID = field(default_factory=uuid4)
    target_id: UUID = field(default_factory=uuid4)
    link_type: TraceLinkType = TraceLinkType.RELATED_TO
    created_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0  # 0.0 to 1.0, how confident we are in this link
    evidence: List[str] = field(default_factory=list)  # Evidence for the link
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_evidence(self, evidence: str) -> None:
        """Add evidence for this link."""
        self.evidence.append(evidence)
    
    def is_strong_link(self, threshold: float = 0.8) -> bool:
        """Check if this is a strong link based on confidence."""
        return self.confidence >= threshold


@dataclass
class TraceabilityMatrix:
    """The complete traceability matrix."""
    specifications: Dict[UUID, SpecificationItem] = field(default_factory=dict)
    implementations: Dict[UUID, ImplementationItem] = field(default_factory=dict)
    tests: Dict[UUID, TestItem] = field(default_factory=dict)
    links: Dict[UUID, TraceLink] = field(default_factory=dict)
    
    # Indexes for fast lookup
    _links_by_source: Dict[UUID, Set[UUID]] = field(default_factory=dict)
    _links_by_target: Dict[UUID, Set[UUID]] = field(default_factory=dict)
    _links_by_type: Dict[TraceLinkType, Set[UUID]] = field(default_factory=dict)
    
    def add_specification(self, spec: SpecificationItem) -> None:
        """Add a specification to the matrix."""
        self.specifications[spec.id] = spec
    
    def add_implementation(self, impl: ImplementationItem) -> None:
        """Add an implementation to the matrix."""
        self.implementations[impl.id] = impl
    
    def add_test(self, test: TestItem) -> None:
        """Add a test to the matrix."""
        self.tests[test.id] = test
    
    def add_link(self, link: TraceLink) -> None:
        """Add a link to the matrix."""
        self.links[link.id] = link
        
        # Update indexes
        if link.source_id not in self._links_by_source:
            self._links_by_source[link.source_id] = set()
        self._links_by_source[link.source_id].add(link.id)
        
        if link.target_id not in self._links_by_target:
            self._links_by_target[link.target_id] = set()
        self._links_by_target[link.target_id].add(link.id)
        
        if link.link_type not in self._links_by_type:
            self._links_by_type[link.link_type] = set()
        self._links_by_type[link.link_type].add(link.id)
    
    def get_links_from(self, item_id: UUID) -> List[TraceLink]:
        """Get all links originating from an item."""
        link_ids = self._links_by_source.get(item_id, set())
        return [self.links[lid] for lid in link_ids if lid in self.links]
    
    def get_links_to(self, item_id: UUID) -> List[TraceLink]:
        """Get all links pointing to an item."""
        link_ids = self._links_by_target.get(item_id, set())
        return [self.links[lid] for lid in link_ids if lid in self.links]
    
    def get_links_of_type(self, link_type: TraceLinkType) -> List[TraceLink]:
        """Get all links of a specific type."""
        link_ids = self._links_by_type.get(link_type, set())
        return [self.links[lid] for lid in link_ids if lid in self.links]
    
    def get_implementations_for_spec(self, spec_id: UUID) -> List[ImplementationItem]:
        """Get all implementations for a specification."""
        impl_ids = set()
        for link in self.get_links_from(spec_id):
            if link.link_type == TraceLinkType.IMPLEMENTS:
                impl_ids.add(link.target_id)
        
        return [self.implementations[iid] for iid in impl_ids if iid in self.implementations]
    
    def get_tests_for_implementation(self, impl_id: UUID) -> List[TestItem]:
        """Get all tests for an implementation."""
        test_ids = set()
        for link in self.get_links_to(impl_id):
            if link.link_type == TraceLinkType.TESTS and link.source_id in self.tests:
                test_ids.add(link.source_id)
        
        return [self.tests[tid] for tid in test_ids if tid in self.tests]
    
    def get_tests_for_spec(self, spec_id: UUID) -> List[TestItem]:
        """Get all tests that verify a specification."""
        test_ids = set()
        
        # Direct verification links
        for link in self.get_links_to(spec_id):
            if link.link_type == TraceLinkType.VERIFIES and link.source_id in self.tests:
                test_ids.add(link.source_id)
        
        # Tests through implementations
        for impl in self.get_implementations_for_spec(spec_id):
            for test in self.get_tests_for_implementation(impl.id):
                test_ids.add(test.id)
        
        return [self.tests[tid] for tid in test_ids if tid in self.tests]
    
    def get_unimplemented_specs(self) -> List[SpecificationItem]:
        """Get specifications without implementations."""
        implemented_specs = set()
        for link in self.get_links_of_type(TraceLinkType.IMPLEMENTS):
            implemented_specs.add(link.source_id)
        
        return [
            spec for spec_id, spec in self.specifications.items()
            if spec_id not in implemented_specs
        ]
    
    def get_untested_implementations(self) -> List[ImplementationItem]:
        """Get implementations without tests."""
        tested_impls = set()
        for link in self.get_links_of_type(TraceLinkType.TESTS):
            tested_impls.add(link.target_id)
        
        return [
            impl for impl_id, impl in self.implementations.items()
            if impl_id not in tested_impls
        ]
    
    def get_orphan_tests(self) -> List[TestItem]:
        """Get tests that don't test any implementation or specification."""
        linked_tests = set()
        
        # Tests that test implementations
        for link in self.get_links_of_type(TraceLinkType.TESTS):
            if link.source_id in self.tests:
                linked_tests.add(link.source_id)
        
        # Tests that verify specifications
        for link in self.get_links_of_type(TraceLinkType.VERIFIES):
            if link.source_id in self.tests:
                linked_tests.add(link.source_id)
        
        return [
            test for test_id, test in self.tests.items()
            if test_id not in linked_tests
        ]