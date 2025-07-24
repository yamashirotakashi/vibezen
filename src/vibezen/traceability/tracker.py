"""
Traceability tracker for managing specification-implementation-test relationships.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
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


class TraceabilityTracker:
    """Tracks relationships between specifications, implementations, and tests."""
    
    def __init__(self, matrix: Optional[TraceabilityMatrix] = None):
        """Initialize the tracker with an optional existing matrix."""
        self.matrix = matrix or TraceabilityMatrix()
        
        # Patterns for detecting relationships in code
        self.spec_patterns = [
            r'(?:spec|requirement|req)[\s_-]*(?:id)?[\s:=]*["\']?([A-Z0-9\-_.]+)',
            r'@(?:implements|satisfies|fulfills)[\s\(]*["\']?([A-Z0-9\-_.]+)',
            r'#\s*(?:Implements|Satisfies|Fulfills):?\s*([A-Z0-9\-_.]+)',
        ]
        
        self.test_patterns = [
            r'(?:test|verify|validate)[\s_-]*(?:spec|requirement|req)[\s_-]*["\']?([A-Z0-9\-_.]+)',
            r'@(?:tests|verifies|validates)[\s\(]*["\']?([A-Z0-9\-_.]+)',
            r'#\s*(?:Tests|Verifies|Validates):?\s*([A-Z0-9\-_.]+)',
        ]
    
    def parse_specification_file(self, file_path: Path) -> List[SpecificationItem]:
        """Parse a specification file and extract specification items."""
        specs = []
        
        content = file_path.read_text(encoding='utf-8')
        
        # Parse markdown-style requirements
        req_pattern = r'^#+\s*(?:REQ-|SPEC-)?([A-Z0-9\-_.]+)(?:\s*:\s*)?(.+?)$'
        priority_pattern = r'\[Priority:\s*(\d+)\]'
        
        current_spec = None
        in_acceptance_criteria = False
        
        for line in content.split('\n'):
            # Check for requirement header
            req_match = re.match(req_pattern, line, re.MULTILINE)
            if req_match:
                # Save previous spec if exists
                if current_spec:
                    specs.append(current_spec)
                
                # Create new spec
                req_id = req_match.group(1)
                title = req_match.group(2).strip()
                
                # Extract priority
                priority = 5  # Default medium priority
                priority_match = re.search(priority_pattern, line)
                if priority_match:
                    priority = int(priority_match.group(1))
                    title = re.sub(priority_pattern, '', title).strip()
                
                current_spec = SpecificationItem(
                    requirement_id=req_id,
                    name=title,
                    priority=priority,
                    source=str(file_path),
                )
                in_acceptance_criteria = False
            
            # Check for acceptance criteria section
            elif current_spec and re.match(r'^#+\s*Acceptance\s+Criteria', line, re.IGNORECASE):
                in_acceptance_criteria = True
            
            # Add acceptance criteria
            elif current_spec and in_acceptance_criteria and line.strip().startswith('- '):
                criterion = line.strip()[2:].strip()
                if criterion:
                    current_spec.add_acceptance_criterion(criterion)
            
            # Add to description
            elif current_spec and line.strip() and not line.startswith('#'):
                if not in_acceptance_criteria:
                    current_spec.description += line.strip() + '\n'
        
        # Don't forget the last spec
        if current_spec:
            specs.append(current_spec)
        
        # Add all specs to the matrix
        for spec in specs:
            self.matrix.add_specification(spec)
        
        return specs
    
    def parse_implementation_file(self, file_path: Path) -> List[ImplementationItem]:
        """Parse a Python implementation file and extract implementation items."""
        implementations = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # Extract docstring
                    docstring = ast.get_docstring(node) or ""
                    
                    # Look for spec references in docstring or comments
                    spec_refs = self._extract_spec_references(docstring)
                    
                    # Get complexity score
                    complexity = self._calculate_complexity(node)
                    
                    # Create implementation item
                    impl = ImplementationItem(
                        name=node.name,
                        file_path=str(file_path),
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        function_name=node.name if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "",
                        class_name=node.name if isinstance(node, ast.ClassDef) else "",
                        complexity_score=complexity,
                        description=docstring.split('\n')[0] if docstring else "",
                    )
                    
                    # Add tags for spec references
                    for spec_ref in spec_refs:
                        impl.add_tag(f"implements:{spec_ref}")
                    
                    implementations.append(impl)
                    self.matrix.add_implementation(impl)
                    
                    # Create links to specifications
                    self._create_spec_impl_links(impl, spec_refs)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        return implementations
    
    def parse_test_file(self, file_path: Path) -> List[TestItem]:
        """Parse a test file and extract test items."""
        tests = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check if it's a test function
                    if node.name.startswith('test_') or any(
                        decorator.id == 'test' if isinstance(decorator, ast.Name) else False
                        for decorator in node.decorator_list
                    ):
                        # Extract docstring
                        docstring = ast.get_docstring(node) or ""
                        
                        # Look for spec/impl references
                        spec_refs = self._extract_spec_references(docstring)
                        impl_refs = self._extract_impl_references(docstring)
                        
                        # Count assertions
                        assertions = self._count_assertions(node)
                        
                        # Determine test type
                        test_type = self._determine_test_type(node, file_path)
                        
                        # Create test item
                        test = TestItem(
                            name=node.name,
                            test_type=test_type,
                            test_file=str(file_path),
                            test_method=node.name,
                            description=docstring.split('\n')[0] if docstring else "",
                            assertions=[f"assertion_{i}" for i in range(assertions)],
                        )
                        
                        # Add tags
                        for spec_ref in spec_refs:
                            test.add_tag(f"verifies:{spec_ref}")
                        for impl_ref in impl_refs:
                            test.add_tag(f"tests:{impl_ref}")
                        
                        tests.append(test)
                        self.matrix.add_test(test)
                        
                        # Create links
                        self._create_test_links(test, spec_refs, impl_refs)
            
        except Exception as e:
            print(f"Error parsing test file {file_path}: {e}")
        
        return tests
    
    def _extract_spec_references(self, text: str) -> List[str]:
        """Extract specification references from text."""
        refs = []
        for pattern in self.spec_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            refs.extend(matches)
        return list(set(refs))  # Remove duplicates
    
    def _extract_impl_references(self, text: str) -> List[str]:
        """Extract implementation references from text."""
        # Look for function/class names referenced in test
        impl_patterns = [
            r'(?:tests?|validates?|verifies?)\s+(\w+)(?:\s+function|\s+method|\s+class)?',
            r'@(?:tests|validates|verifies)\s*\(\s*["\']?(\w+)',
        ]
        
        refs = []
        for pattern in impl_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            refs.extend(matches)
        return list(set(refs))
    
    def _calculate_complexity(self, node: ast.AST) -> float:
        """Calculate cyclomatic complexity of a function or class."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers) + (1 if child.orelse else 0)
            elif isinstance(child, ast.With):
                complexity += len(child.items)
        
        return float(complexity)
    
    def _count_assertions(self, node: ast.AST) -> int:
        """Count the number of assertions in a test function."""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                count += 1
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                # Count common assertion methods
                if child.func.attr in ['assertEqual', 'assertTrue', 'assertFalse',
                                      'assertIs', 'assertIsNot', 'assertIn',
                                      'assertNotIn', 'assertRaises', 'assert_called',
                                      'assert_called_once', 'assert_called_with']:
                    count += 1
        return count
    
    def _determine_test_type(self, node: ast.AST, file_path: Path) -> str:
        """Determine the type of test based on context."""
        file_name = file_path.name.lower()
        
        if 'unit' in file_name:
            return 'unit'
        elif 'integration' in file_name:
            return 'integration'
        elif 'system' in file_name:
            return 'system'
        elif 'acceptance' in file_name or 'e2e' in file_name:
            return 'acceptance'
        
        # Check decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if 'unit' in decorator.id.lower():
                    return 'unit'
                elif 'integration' in decorator.id.lower():
                    return 'integration'
        
        # Default to unit test
        return 'unit'
    
    def _create_spec_impl_links(self, impl: ImplementationItem, spec_refs: List[str]) -> None:
        """Create links between specifications and implementations."""
        for spec_ref in spec_refs:
            # Find matching specification
            for spec in self.matrix.specifications.values():
                if spec.requirement_id == spec_ref:
                    link = TraceLink(
                        source_id=spec.id,
                        target_id=impl.id,
                        link_type=TraceLinkType.IMPLEMENTS,
                        confidence=0.9,  # High confidence for explicit references
                    )
                    link.add_evidence(f"Explicit reference in {impl.get_location()}")
                    self.matrix.add_link(link)
                    break
    
    def _create_test_links(self, test: TestItem, spec_refs: List[str], impl_refs: List[str]) -> None:
        """Create links between tests and specifications/implementations."""
        # Links to specifications
        for spec_ref in spec_refs:
            for spec in self.matrix.specifications.values():
                if spec.requirement_id == spec_ref:
                    link = TraceLink(
                        source_id=test.id,
                        target_id=spec.id,
                        link_type=TraceLinkType.VERIFIES,
                        confidence=0.9,
                    )
                    link.add_evidence(f"Explicit verification in {test.test_method}")
                    self.matrix.add_link(link)
                    break
        
        # Links to implementations
        for impl_ref in impl_refs:
            for impl in self.matrix.implementations.values():
                if impl.name == impl_ref or impl.function_name == impl_ref or impl.class_name == impl_ref:
                    link = TraceLink(
                        source_id=test.id,
                        target_id=impl.id,
                        link_type=TraceLinkType.TESTS,
                        confidence=0.85,
                    )
                    link.add_evidence(f"Test method {test.test_method} tests {impl_ref}")
                    self.matrix.add_link(link)
                    break
    
    def auto_discover_links(self, confidence_threshold: float = 0.7) -> List[TraceLink]:
        """Automatically discover potential links based on naming conventions and patterns."""
        discovered_links = []
        
        # Discover spec-impl links by name similarity
        for spec in self.matrix.specifications.values():
            spec_keywords = self._extract_keywords(spec.name + " " + spec.description)
            
            for impl in self.matrix.implementations.values():
                impl_keywords = self._extract_keywords(impl.name + " " + impl.description)
                
                similarity = self._calculate_similarity(spec_keywords, impl_keywords)
                if similarity >= confidence_threshold:
                    # Check if link already exists
                    existing = False
                    for link in self.matrix.get_links_from(spec.id):
                        if link.target_id == impl.id and link.link_type == TraceLinkType.IMPLEMENTS:
                            existing = True
                            break
                    
                    if not existing:
                        link = TraceLink(
                            source_id=spec.id,
                            target_id=impl.id,
                            link_type=TraceLinkType.IMPLEMENTS,
                            confidence=similarity,
                        )
                        link.add_evidence(f"Name/description similarity: {similarity:.2f}")
                        discovered_links.append(link)
        
        # Discover test-impl links
        for test in self.matrix.tests.values():
            test_name_parts = test.name.lower().split('_')
            
            for impl in self.matrix.implementations.values():
                impl_name_lower = impl.name.lower()
                
                # Check if implementation name appears in test name
                if impl_name_lower in test.name.lower() or any(
                    part in impl_name_lower for part in test_name_parts if len(part) > 3
                ):
                    # Check if link already exists
                    existing = False
                    for link in self.matrix.get_links_from(test.id):
                        if link.target_id == impl.id and link.link_type == TraceLinkType.TESTS:
                            existing = True
                            break
                    
                    if not existing:
                        link = TraceLink(
                            source_id=test.id,
                            target_id=impl.id,
                            link_type=TraceLinkType.TESTS,
                            confidence=0.75,
                        )
                        link.add_evidence(f"Name pattern match: {test.name} -> {impl.name}")
                        discovered_links.append(link)
        
        # Add discovered links to matrix
        for link in discovered_links:
            self.matrix.add_link(link)
        
        return discovered_links
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text for similarity matching."""
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\w+', text.lower())
        # Filter out common words and short words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'}
        keywords = {w for w in words if len(w) > 2 and w not in stopwords}
        return keywords
    
    def _calculate_similarity(self, keywords1: Set[str], keywords2: Set[str]) -> float:
        """Calculate Jaccard similarity between two sets of keywords."""
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def update_from_test_results(self, test_results: Dict[str, bool]) -> None:
        """Update test items based on test execution results."""
        for test in self.matrix.tests.values():
            if test.test_method in test_results:
                if test_results[test.test_method]:
                    test.mark_passed()
                else:
                    test.mark_failed()
    
    def get_matrix(self) -> TraceabilityMatrix:
        """Get the current traceability matrix."""
        return self.matrix