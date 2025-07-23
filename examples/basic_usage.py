"""
Basic usage example of VIBEZEN V2.

Shows how the prompt intervention system guides AI through
the development process.
"""

import asyncio
from pathlib import Path

from vibezen.core.guard_v2 import VIBEZENGuardV2


async def main():
    """Demonstrate VIBEZEN usage."""
    # Initialize VIBEZEN
    guard = VIBEZENGuardV2()
    await guard.initialize()
    
    # Example specification
    specification = {
        "name": "User Authentication Service",
        "description": "A service to handle user login and logout",
        "features": [
            "Login with username and password",
            "Logout current user",
            "Check if user is authenticated",
        ],
        "requirements": [
            "Passwords must be hashed",
            "Sessions should timeout after 30 minutes",
            "Support concurrent users",
        ],
        "constraints": [
            "Use JWT for session management",
            "Must be stateless",
        ],
    }
    
    print("=== VIBEZEN AI Code Generation Demo ===\n")
    
    # Step 1: Guide specification understanding
    print("Step 1: Understanding Specification...")
    understanding_result = await guard.guide_specification_understanding(
        specification=specification,
        provider="mock",
        model="mock-smart",
    )
    
    if understanding_result["success"]:
        print("✓ Specification understood")
        print(f"  Confidence: {understanding_result['understanding']['confidence']}")
        print(f"  Requirements identified: {len(understanding_result['understanding']['requirements'])}")
    else:
        print("✗ Failed to understand specification")
        return
    
    # Step 2: Guide implementation choice
    print("\nStep 2: Choosing Implementation Approach...")
    choice_result = await guard.guide_implementation_choice(
        specification=specification,
        understanding=understanding_result["understanding"],
    )
    
    if choice_result["success"]:
        print("✓ Implementation approach selected")
        print(f"  Approaches considered: {len(choice_result['approaches'])}")
        print(f"  Selected: {choice_result['selected_approach']['name']}")
    else:
        print("✗ Failed to choose approach")
        return
    
    # Step 3: Guide implementation
    print("\nStep 3: Implementing with Quality Checks...")
    impl_result = await guard.guide_implementation(
        specification=specification,
        approach=choice_result["selected_approach"],
    )
    
    if impl_result["success"]:
        print("✓ Implementation completed")
        print(f"  Code length: {len(impl_result['code'])} characters")
        print(f"  Violations: {len(impl_result['violations'])}")
    else:
        print("✗ Implementation has issues")
        for violation in impl_result["violations"]:
            print(f"  - {violation.description}")
        return
    
    # Step 4: Guide test design
    print("\nStep 4: Designing Tests...")
    test_result = await guard.guide_test_design(
        specification=specification,
        code=impl_result["code"],
    )
    
    if test_result["success"]:
        print("✓ Tests designed")
        print(f"  Test cases: {len(test_result['tests'])}")
        print(f"  Coverage estimate: {test_result['coverage_estimate']:.0%}")
    else:
        print("✗ Test design failed")
        return
    
    # Step 5: Perform quality review
    print("\nStep 5: Quality Review...")
    review_result = await guard.perform_quality_review(
        code=impl_result["code"],
        tests=test_result["tests"],
        specification=specification,
    )
    
    print(f"\n{'='*50}")
    print("FINAL QUALITY REPORT")
    print(f"{'='*50}")
    print(f"Quality Score: {review_result['quality_score']:.2f}/1.00")
    print(f"Status: {'✓ PASSED' if review_result['success'] else '✗ FAILED'}")
    
    if review_result["findings"]:
        print("\nFindings:")
        for finding in review_result["findings"]:
            print(f"  - [{finding['severity']}] {finding['description']}")
    
    print("\nRecommendations:")
    for rec in review_result["recommendations"]:
        print(f"  - {rec}")
    
    print(f"\n{'='*50}")
    print("Development process completed with VIBEZEN guidance!")


async def demonstrate_prompt_intervention():
    """Show how VIBEZEN intervenes at the prompt level."""
    guard = VIBEZENGuardV2()
    await guard.initialize()
    
    print("\n=== Prompt Intervention Demo ===\n")
    
    # Show what happens when AI tries to hardcode
    bad_code = """
def connect_to_database():
    host = "localhost"  # Hardcoded!
    port = 5432  # Hardcoded!
    password = "admin123"  # VERY BAD!
    return f"postgresql://{host}:{port}"
"""
    
    print("Original (problematic) code:")
    print(bad_code)
    
    # VIBEZEN would detect this and generate a correction prompt
    violations = await guard._validate_code(bad_code, {})
    
    if violations:
        print(f"\nVIBEZEN detected {len(violations)} issues:")
        for v in violations:
            print(f"  - {v.description}")
        
        # Generate correction prompt
        correction_prompt = await guard._create_correction_prompt(bad_code, violations)
        print("\nVIBEZEN generates this correction prompt:")
        print("-" * 50)
        print(correction_prompt)
        print("-" * 50)


if __name__ == "__main__":
    # Run basic usage demo
    asyncio.run(main())
    
    # Run prompt intervention demo
    asyncio.run(demonstrate_prompt_intervention())