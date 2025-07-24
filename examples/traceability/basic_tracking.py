#!/usr/bin/env python3
"""
Basic traceability tracking example.

This example shows how to set up basic traceability tracking
for a small project with specifications, implementations, and tests.
"""

import asyncio
from pathlib import Path

from vibezen.core.guard_v2_traceability import VIBEZENGuardV2WithTraceability
from vibezen.traceability import (
    SpecificationItem,
    ImplementationItem,
    TestItem,
    TraceLink,
    TraceLinkType,
)


async def main():
    """Run basic traceability tracking example."""
    print("VIBEZEN Basic Traceability Tracking Example")
    print("=" * 50)
    
    # Initialize guard with traceability
    guard = VIBEZENGuardV2WithTraceability()
    
    # Example 1: Track a specification through the development process
    print("\n1. Adding Specification...")
    spec = {
        "id": "REQ-001",
        "name": "User Registration",
        "description": "Users should be able to register with email and password",
        "priority": 8,
        "acceptance_criteria": [
            "Email must be valid format",
            "Password must be at least 8 characters",
            "Email must be unique in the system"
        ],
        "tags": ["authentication", "user-management"]
    }
    
    # Guide specification understanding (automatically adds to traceability)
    spec_analysis = await guard.guide_specification_understanding(spec)
    print(f"   ✓ Added specification: {spec['id']}")
    
    # Example 2: Track implementation
    print("\n2. Adding Implementation...")
    impl_choice = await guard.guide_implementation_choice(spec, spec_analysis)
    print(f"   ✓ Implementation approach: {impl_choice.approach['name']}")
    print(f"   ✓ Automatically linked to {spec['id']}")
    
    # Example 3: Manually add a test
    print("\n3. Adding Test...")
    test = TestItem(
        name="test_user_registration",
        test_type="integration",
        test_file="tests/test_auth.py",
        test_method="test_user_registration",
        description="Test complete user registration flow"
    )
    guard.tracker.matrix.add_test(test)
    
    # Create test links manually
    # Link test to implementation
    impl_id = impl_choice.metadata["impl_id"]
    for iid, impl in guard.tracker.matrix.implementations.items():
        if str(iid) == impl_id:
            test_impl_link = TraceLink(
                source_id=test.id,
                target_id=iid,
                link_type=TraceLinkType.TESTS,
                confidence=0.9
            )
            guard.tracker.matrix.add_link(test_impl_link)
            print(f"   ✓ Linked test to implementation")
            break
    
    # Link test to specification
    spec_id = spec_analysis.metadata["spec_id"]
    for sid, s in guard.tracker.matrix.specifications.items():
        if str(sid) == spec_id:
            test_spec_link = TraceLink(
                source_id=test.id,
                target_id=sid,
                link_type=TraceLinkType.VERIFIES,
                confidence=0.95
            )
            guard.tracker.matrix.add_link(test_spec_link)
            print(f"   ✓ Linked test to specification")
            break
    
    # Example 4: Check coverage
    print("\n4. Coverage Analysis...")
    report = guard.get_coverage_report()
    
    print(f"   Specifications: {report.implemented_specifications}/{report.total_specifications} implemented")
    print(f"   Implementations: {report.tested_implementations}/{report.total_implementations} tested")
    print(f"   Coverage: {report.specification_coverage:.1f}% specs, {report.test_coverage:.1f}% tests")
    
    # Example 5: Add another spec without implementation (gap)
    print("\n5. Adding Unimplemented Specification...")
    spec2 = SpecificationItem(
        requirement_id="REQ-002",
        name="Password Reset",
        description="Users should be able to reset forgotten passwords",
        priority=9  # High priority!
    )
    guard.tracker.matrix.add_specification(spec2)
    print(f"   ✓ Added specification: {spec2.requirement_id}")
    
    # Example 6: Check for gaps
    print("\n6. Gap Analysis...")
    unimplemented = guard.get_unimplemented_specs()
    if unimplemented:
        print("   ⚠️  Unimplemented specifications:")
        for spec in unimplemented:
            priority_marker = "🔴" if spec.priority >= 8 else "🟡" if spec.priority >= 5 else "🟢"
            print(f"      {priority_marker} {spec.requirement_id}: {spec.name} (Priority: {spec.priority})")
    
    untested = guard.get_untested_implementations()
    if untested:
        print("   ⚠️  Untested implementations:")
        for impl in untested:
            print(f"      - {impl.name} in {impl.file_path}")
    
    # Example 7: Validate traceability
    print("\n7. Traceability Validation...")
    validation = await guard.validate_traceability()
    
    if validation["valid"]:
        print("   ✅ Traceability is valid!")
    else:
        print("   ❌ Traceability has issues:")
    
    for error in validation["issues"]["errors"]:
        print(f"   🚨 ERROR: {error}")
    
    for warning in validation["issues"]["warnings"]:
        print(f"   ⚠️  WARNING: {warning}")
    
    for info in validation["issues"]["info"]:
        print(f"   ℹ️  INFO: {info}")
    
    # Example 8: Generate simple text summary
    print("\n8. Traceability Summary")
    print("-" * 50)
    metrics = guard.analyzer.get_traceability_metrics()
    
    print("Specifications:")
    print(f"  Total: {metrics['specification_metrics']['total']}")
    print(f"  Implemented: {metrics['specification_metrics']['implemented']}")
    print(f"  Coverage: {metrics['specification_metrics']['coverage_percentage']:.1f}%")
    
    print("\nImplementations:")
    print(f"  Total: {metrics['implementation_metrics']['total']}")
    print(f"  Tested: {metrics['implementation_metrics']['tested']}")
    print(f"  Coverage: {metrics['implementation_metrics']['test_coverage_percentage']:.1f}%")
    
    print("\nTests:")
    print(f"  Total: {metrics['test_metrics']['total']}")
    print(f"  Pass Rate: {metrics['test_metrics']['pass_rate']:.1f}%")
    
    print("\nLinks:")
    print(f"  Total: {metrics['link_metrics']['total_links']}")
    print(f"  Implements: {metrics['link_metrics']['implements_links']}")
    print(f"  Tests: {metrics['link_metrics']['tests_links']}")
    print(f"  Verifies: {metrics['link_metrics']['verifies_links']}")


if __name__ == "__main__":
    asyncio.run(main())