# VIBEZEN Traceability Management System

## Overview

The VIBEZEN Traceability Management System provides complete tracking of specification-implementation-test relationships, ensuring that all requirements are properly implemented and tested. It helps identify gaps in coverage, over-implementations, and the impact of changes across the codebase.

## Key Features

### 1. Complete Traceability Matrix
- **Specification Tracking**: Track all requirements and specifications
- **Implementation Mapping**: Link implementations to specifications
- **Test Coverage**: Map tests to both implementations and specifications
- **Bidirectional Links**: Navigate relationships in both directions

### 2. Coverage Analysis
- **Specification Coverage**: Percentage of specifications that are implemented
- **Test Coverage**: Percentage of implementations that have tests
- **Verification Coverage**: Percentage of specifications verified by tests
- **Gap Identification**: Find unimplemented specs, untested code, and orphan tests

### 3. Impact Analysis
- **Change Impact**: Analyze what is affected when changing a specification, implementation, or test
- **Risk Assessment**: Evaluate the risk level of changes
- **Dependency Tracking**: Understand dependencies and circular relationships
- **Recommendations**: Get actionable recommendations for changes

### 4. Visualization
- **Mermaid Diagrams**: Interactive relationship diagrams
- **Coverage Heatmaps**: Visual representation of coverage gaps
- **HTML Reports**: Comprehensive reports with metrics and visualizations
- **Export Options**: JSON, PlantUML, and other formats

## Architecture

```
┌─────────────────────┐
│ Specifications      │
│ - Requirements      │
│ - Acceptance        │
│   Criteria          │
└──────────┬──────────┘
           │ IMPLEMENTS
           ▼
┌─────────────────────┐
│ Implementations     │
│ - Functions         │
│ - Classes           │
│ - Modules           │
└──────────┬──────────┘
           │ TESTS
           ▼
┌─────────────────────┐
│ Tests               │
│ - Unit Tests        │
│ - Integration Tests │
│ - System Tests      │
└─────────────────────┘
```

## Usage

### Basic Usage with VIBEZENGuard

```python
from vibezen.core.guard_v2_traceability import VIBEZENGuardV2WithTraceability

# Initialize guard with traceability
guard = VIBEZENGuardV2WithTraceability()

# Parse project files to build traceability matrix
results = guard.parse_project_files(
    project_path=Path("./my_project"),
    spec_patterns=["**/specs/*.md", "**/requirements/*.md"],
    impl_patterns=["**/*.py"],
    test_patterns=["**/test_*.py", "**/tests/*.py"]
)

# Get coverage report
report = guard.get_coverage_report()
print(f"Specification Coverage: {report.specification_coverage:.1f}%")
print(f"Test Coverage: {report.test_coverage:.1f}%")

# Generate reports
guard.generate_traceability_report(Path("./reports"))
```

### Manual Traceability Tracking

```python
from vibezen.traceability import (
    TraceabilityTracker,
    SpecificationItem,
    ImplementationItem,
    TestItem,
    TraceLink,
    TraceLinkType
)

# Create tracker
tracker = TraceabilityTracker()

# Add specification
spec = SpecificationItem(
    requirement_id="REQ-001",
    name="User Authentication",
    description="System shall provide secure authentication",
    priority=9,
    acceptance_criteria=[
        "Users can login with credentials",
        "Passwords are encrypted",
        "Session timeout after 30 minutes"
    ]
)
tracker.matrix.add_specification(spec)

# Add implementation
impl = ImplementationItem(
    name="authenticate_user",
    file_path="src/auth.py",
    line_start=10,
    line_end=50,
    function_name="authenticate_user",
    complexity_score=8.0
)
tracker.matrix.add_implementation(impl)

# Create link
link = TraceLink(
    source_id=spec.id,
    target_id=impl.id,
    link_type=TraceLinkType.IMPLEMENTS,
    confidence=0.95
)
tracker.matrix.add_link(link)
```

### Analyzing Impact of Changes

```python
from vibezen.traceability import TraceabilityAnalyzer

# Create analyzer
analyzer = TraceabilityAnalyzer(tracker.matrix)

# Analyze impact of changing a specification
impact = analyzer.analyze_impact(spec.id)

print(f"Risk Level: {impact.risk_level}")
print(f"Affected Implementations: {len(impact.directly_affected_impls)}")
print(f"Affected Tests: {len(impact.directly_affected_tests)}")
print("Recommendations:")
for recommendation in impact.recommended_actions:
    print(f"  - {recommendation}")
```

### Generating Visualizations

```python
from vibezen.traceability import TraceabilityVisualizer

# Create visualizer
visualizer = TraceabilityVisualizer(tracker.matrix)

# Generate Mermaid diagram
mermaid_diagram = visualizer.generate_mermaid_diagram()
print(mermaid_diagram)

# Generate HTML report
visualizer.generate_html_report(Path("traceability_report.html"))

# Export to JSON
visualizer.export_to_json(Path("traceability_data.json"))
```

## Specification File Format

Specifications should be written in Markdown format:

```markdown
# REQ-001: User Authentication [Priority: 9]
The system shall provide secure user authentication mechanism.

## Acceptance Criteria
- Users can login with username and password
- Passwords are stored using bcrypt hashing
- Session expires after 30 minutes of inactivity
- Failed login attempts are logged

# REQ-002: Data Validation [Priority: 7]
All user input must be validated before processing.
```

## Implementation Annotations

Link implementations to specifications using docstrings or comments:

```python
def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user against the database.
    
    Implements: REQ-001
    """
    # Implementation code here
    pass

class UserValidator:
    """
    Validates user input.
    
    @implements REQ-002
    """
    pass
```

## Test Annotations

Link tests to implementations and specifications:

```python
def test_user_authentication():
    """
    Test user authentication functionality.
    
    Tests: authenticate_user
    Verifies: REQ-001
    """
    assert authenticate_user("valid_user", "valid_pass") is True
    assert authenticate_user("invalid_user", "wrong_pass") is False
```

## Coverage Metrics

### Specification Coverage
Percentage of specifications that have at least one implementation:
```
Specification Coverage = (Implemented Specs / Total Specs) × 100
```

### Test Coverage
Percentage of implementations that have at least one test:
```
Test Coverage = (Tested Implementations / Total Implementations) × 100
```

### Verification Coverage
Percentage of specifications that are verified by tests:
```
Verification Coverage = (Verified Specs / Total Specs) × 100
```

## Best Practices

### 1. Consistent Naming
- Use consistent requirement IDs (e.g., REQ-XXX, SPEC-XXX)
- Follow naming conventions for implementations and tests
- Use descriptive names that clearly indicate purpose

### 2. Complete Annotations
- Always annotate implementations with the specs they implement
- Always annotate tests with what they test and verify
- Include confidence levels for uncertain relationships

### 3. Regular Updates
- Update traceability matrix when adding new features
- Remove obsolete links when refactoring
- Review coverage reports regularly

### 4. Impact Analysis Before Changes
- Always run impact analysis before modifying specifications
- Review affected implementations and tests
- Update all affected components together

### 5. Maintain High Coverage
- Aim for >95% specification coverage
- Aim for >90% test coverage
- Investigate and document any gaps

## Troubleshooting

### Low Specification Coverage
1. Check for missing implementation annotations
2. Review unimplemented specifications
3. Prioritize high-priority unimplemented specs

### Low Test Coverage
1. Identify untested implementations
2. Focus on complex untested code first
3. Add test annotations to existing tests

### Circular Dependencies
1. Run circular dependency detection
2. Review and refactor dependencies
3. Consider breaking large specs into smaller ones

### Orphan Tests
1. Identify tests without links
2. Add appropriate annotations
3. Remove truly obsolete tests

## Integration with CI/CD

### Pre-commit Hooks
```bash
#!/bin/bash
# Check traceability coverage
python -m vibezen.traceability check-coverage --min-spec-coverage 95 --min-test-coverage 90
```

### GitHub Actions
```yaml
- name: Traceability Analysis
  run: |
    python -m vibezen.traceability analyze --format json > traceability.json
    python -m vibezen.traceability report --format html > traceability.html
  
- name: Upload Traceability Report
  uses: actions/upload-artifact@v2
  with:
    name: traceability-report
    path: traceability.html
```

## Advanced Features

### Custom Link Types
```python
from vibezen.traceability import TraceLinkType

# Add custom link types
class CustomLinkType(TraceLinkType):
    PARTIALLY_IMPLEMENTS = "partially_implements"
    EXTENDS = "extends"
    REPLACES = "replaces"
```

### Confidence Thresholds
```python
# Set confidence threshold for auto-discovery
tracker.auto_discover_links(confidence_threshold=0.8)

# Filter links by confidence
high_confidence_links = [
    link for link in matrix.links.values()
    if link.confidence >= 0.9
]
```

### Custom Analyzers
```python
class CustomAnalyzer(TraceabilityAnalyzer):
    def analyze_technical_debt(self) -> Dict[str, Any]:
        """Analyze technical debt based on traceability."""
        # Custom analysis logic
        pass
```

## Examples

See the `examples/traceability` directory for complete examples:
- `basic_tracking.py`: Basic traceability tracking
- `coverage_analysis.py`: Coverage report generation
- `impact_analysis.py`: Change impact analysis
- `visualization.py`: Creating visualizations
- `ci_integration.py`: CI/CD integration