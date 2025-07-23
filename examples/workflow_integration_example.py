"""
Example of integrating VIBEZEN with spec_to_implementation_workflow.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "memory-integration-project"))

from vibezen.integration.workflow_adapter import create_vibezen_adapter


async def mock_phase_1_spec_reading(spec_path: Path, vibezen_context=None):
    """Mock Phase 1: Read and analyze specification."""
    print(f"\n=== Phase 1: Reading spec from {spec_path} ===")
    
    if vibezen_context:
        print(f"VIBEZEN Context: {vibezen_context}")
    
    # Mock spec reading
    spec = {
        "name": "Example Project",
        "requirements": ["REQ-001: User authentication", "REQ-002: Data validation"],
        "constraints": ["Python 3.12+", "Async support"]
    }
    
    return spec


async def mock_phase_2_task_planning(spec: dict, vibezen_context=None):
    """Mock Phase 2: Generate implementation tasks."""
    print(f"\n=== Phase 2: Planning tasks ===")
    
    if vibezen_context:
        print(f"VIBEZEN Context: {vibezen_context}")
    
    tasks = [
        {"id": "TASK-001", "description": "Implement user model", "complexity": "medium"},
        {"id": "TASK-002", "description": "Create authentication service", "complexity": "high"},
        {"id": "TASK-003", "description": "Add validation middleware", "complexity": "low"}
    ]
    
    return tasks


async def mock_phase_3_implementation(tasks: list, vibezen_context=None):
    """Mock Phase 3: Implement the code."""
    print(f"\n=== Phase 3: Implementing {len(tasks)} tasks ===")
    
    if vibezen_context:
        print(f"VIBEZEN Context: {vibezen_context}")
    
    implementation = """
class User:
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email

class AuthService:
    async def authenticate(self, username: str, password: str) -> bool:
        # Implementation here
        return True

def validate_email(email: str) -> bool:
    return '@' in email
"""
    
    return {"code": implementation, "files_created": 3}


async def mock_phase_4_testing(implementation: dict, vibezen_context=None):
    """Mock Phase 4: Generate and run tests."""
    print(f"\n=== Phase 4: Testing implementation ===")
    
    if vibezen_context:
        print(f"VIBEZEN Context: {vibezen_context}")
    
    test_results = {
        "tests_passed": 10,
        "tests_failed": 0,
        "coverage": 0.85
    }
    
    return test_results


async def mock_phase_5_documentation(results: dict, vibezen_context=None):
    """Mock Phase 5: Generate documentation."""
    print(f"\n=== Phase 5: Generating documentation ===")
    
    if vibezen_context:
        print(f"VIBEZEN Context: {vibezen_context}")
    
    documentation = {
        "readme": "# Example Project\n\nImplementation complete.",
        "api_docs": "API documentation here",
        "metrics": results
    }
    
    return documentation


async def run_workflow_with_vibezen():
    """Run the workflow with VIBEZEN integration."""
    print("Starting spec-to-implementation workflow with VIBEZEN")
    
    # Create VIBEZEN adapter
    vibezen = create_vibezen_adapter(
        enable=True,
        enable_semantic_cache=True,
        enable_sanitization=True,
        primary_provider="openai",
        fallback_providers=["google", "anthropic"]
    )
    
    # Show configuration
    config = vibezen.get_config()
    print(f"\nVIBEZEN Configuration: {config}")
    
    # Run each phase with VIBEZEN enhancement
    spec_path = Path("example_spec.md")
    
    # Phase 1: Spec reading
    spec = await vibezen.enhance_phase(1, mock_phase_1_spec_reading, spec_path)
    
    # Phase 2: Task planning
    tasks = await vibezen.enhance_phase(2, mock_phase_2_task_planning, spec)
    
    # Phase 3: Implementation
    implementation = await vibezen.enhance_phase(3, mock_phase_3_implementation, tasks)
    
    # Phase 4: Testing
    test_results = await vibezen.enhance_phase(4, mock_phase_4_testing, implementation)
    
    # Phase 5: Documentation
    documentation = await vibezen.enhance_phase(5, mock_phase_5_documentation, test_results)
    
    print("\n=== Workflow Complete ===")
    
    # Example AI call with protection
    print("\n=== Testing AI call with VIBEZEN protection ===")
    response = await vibezen.call_ai_with_protection(
        "Explain the benefits of async programming in Python",
        provider="openai"
    )
    print(f"AI Response: {response[:100]}...")
    
    # Validate implementation
    print("\n=== Validating implementation ===")
    validation = await vibezen.validate_implementation(spec, implementation["code"])
    print(f"Validation result: {validation}")
    
    # Get metrics
    print("\n=== VIBEZEN Metrics ===")
    metrics = await vibezen.get_metrics()
    print(f"Metrics: {metrics}")


async def run_workflow_without_vibezen():
    """Run the workflow without VIBEZEN for comparison."""
    print("\n\n=== Running workflow WITHOUT VIBEZEN for comparison ===")
    
    # Create disabled adapter
    vibezen = create_vibezen_adapter(enable=False)
    
    spec_path = Path("example_spec.md")
    
    # Run phases without enhancement
    spec = await vibezen.enhance_phase(1, mock_phase_1_spec_reading, spec_path)
    tasks = await vibezen.enhance_phase(2, mock_phase_2_task_planning, spec)
    implementation = await vibezen.enhance_phase(3, mock_phase_3_implementation, tasks)
    test_results = await vibezen.enhance_phase(4, mock_phase_4_testing, implementation)
    documentation = await vibezen.enhance_phase(5, mock_phase_5_documentation, test_results)
    
    print("\n=== Workflow Complete (No VIBEZEN) ===")


async def main():
    """Run example workflows."""
    # Run with VIBEZEN
    await run_workflow_with_vibezen()
    
    # Run without VIBEZEN for comparison
    await run_workflow_without_vibezen()


if __name__ == "__main__":
    asyncio.run(main())