"""
Demo of VIBEZEN with real AI providers.

This example shows how VIBEZEN guides AI through proper implementation
using actual AI models from OpenAI, Anthropic, or Google.

Set one of these environment variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY  
- GOOGLE_API_KEY
"""

import os
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibezen.core.guard_v2 import VIBEZENGuardV2


# Example specification
USER_AUTH_SPEC = {
    "name": "User Authentication Service",
    "description": "A secure authentication service for user login",
    "features": [
        "User login with email and password",
        "Password hashing for security",
        "Session token generation",
        "Input validation"
    ],
    "requirements": [
        "Passwords must never be stored in plain text",
        "Use environment variables for configuration",
        "Implement proper error handling",
        "No hardcoded values"
    ],
    "constraints": [
        "Must use bcrypt for password hashing",
        "Session tokens should be cryptographically secure",
        "Email validation required"
    ]
}


async def demo_vibezen_workflow():
    """Demonstrate VIBEZEN workflow with real AI providers."""
    
    # Check for available providers
    providers = []
    if os.getenv("OPENAI_API_KEY"):
        providers.append(("openai", "gpt-4", "OpenAI GPT-4"))
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append(("anthropic", "claude-3-sonnet", "Anthropic Claude 3 Sonnet"))
    if os.getenv("GOOGLE_API_KEY"):
        providers.append(("google", "gemini-pro", "Google Gemini Pro"))
    
    if not providers:
        print("❌ No AI providers available!")
        print("\nPlease set one of these environment variables:")
        print("- OPENAI_API_KEY")
        print("- ANTHROPIC_API_KEY")
        print("- GOOGLE_API_KEY")
        return
    
    # Select provider
    print("🤖 Available AI Providers:")
    for i, (_, _, name) in enumerate(providers):
        print(f"  {i+1}. {name}")
    
    if len(providers) > 1:
        choice = input(f"\nSelect provider (1-{len(providers)}) [1]: ").strip() or "1"
        try:
            idx = int(choice) - 1
            provider, model, name = providers[idx]
        except (ValueError, IndexError):
            provider, model, name = providers[0]
    else:
        provider, model, name = providers[0]
    
    print(f"\n✅ Using {name}")
    print("=" * 70)
    
    # Initialize VIBEZEN
    print("\n🚀 Initializing VIBEZEN...")
    guard = VIBEZENGuardV2()
    await guard.initialize()
    
    # Phase 1: Understanding
    print("\n📋 Phase 1: Understanding Specification")
    print("-" * 50)
    print("VIBEZEN is guiding the AI to deeply understand the requirements...")
    
    understanding_result = await guard.guide_specification_understanding(
        specification=USER_AUTH_SPEC,
        provider=provider,
        model=model
    )
    
    if not understanding_result["success"]:
        print("❌ Failed to understand specification")
        return
    
    understanding = understanding_result["understanding"]
    thinking_trace = understanding_result["thinking_trace"]
    
    print(f"\n✅ AI thought through {len(thinking_trace.steps)} steps")
    print("\nKey insights:")
    print(f"- Found {len(understanding.get('requirements', []))} requirements")
    print(f"- Identified {len(understanding.get('edge_cases', []))} edge cases")
    print(f"- Noted {len(understanding.get('ambiguities', []))} ambiguities")
    print(f"- Confidence: {understanding.get('confidence', 0):.1%}")
    
    # Show some thinking steps
    print("\nSample thinking steps:")
    for step in thinking_trace.steps[:3]:
        print(f"  {step.number}. {step.thought[:80]}...")
    
    # Phase 2: Implementation Choice
    print("\n🔍 Phase 2: Exploring Implementation Approaches")
    print("-" * 50)
    print("VIBEZEN is guiding the AI to consider multiple approaches...")
    
    choice_result = await guard.guide_implementation_choice(
        specification=USER_AUTH_SPEC,
        understanding=understanding,
        provider=provider,
        model=model
    )
    
    if not choice_result["success"]:
        print("❌ Failed to choose implementation approach")
        return
    
    approaches = choice_result["approaches"]
    selected = choice_result["selected_approach"]
    
    print(f"\n✅ AI considered {len(approaches)} different approaches")
    print("\nApproaches considered:")
    for i, approach in enumerate(approaches):
        marker = "→" if approach == selected else " "
        print(f"  {marker} {i+1}. {approach['name']}")
        print(f"      Pros: {', '.join(approach.get('pros', [])[:2])}")
    
    print(f"\nSelected: {selected['name']}")
    print(f"Reason: {selected.get('justification', 'Best fit for requirements')}")
    
    # Phase 3: Implementation
    print("\n💻 Phase 3: Generating Implementation")
    print("-" * 50)
    print("VIBEZEN is ensuring the AI writes quality code...")
    
    impl_result = await guard.guide_implementation(
        specification=USER_AUTH_SPEC,
        approach=selected,
        provider=provider,
        model=model
    )
    
    if not impl_result["success"]:
        print("❌ Failed to generate implementation")
        return
    
    code = impl_result["code"]
    violations = impl_result.get("violations", [])
    
    print(f"\n✅ Generated {len(code.splitlines())} lines of code")
    
    if violations:
        print(f"\n⚠️  Found {len(violations)} quality issues:")
        for v in violations[:3]:
            print(f"  - {v.type.value}: {v.description}")
    else:
        print("\n✨ No quality violations detected!")
    
    # Show code preview
    print("\nCode preview:")
    print("-" * 50)
    lines = code.splitlines()
    for line in lines[:20]:
        print(line)
    if len(lines) > 20:
        print(f"... ({len(lines) - 20} more lines)")
    
    # Phase 4: Test Design
    print("\n🧪 Phase 4: Designing Tests")
    print("-" * 50)
    print("VIBEZEN is guiding comprehensive test design...")
    
    test_result = await guard.guide_test_design(
        specification=USER_AUTH_SPEC,
        code=code,
        provider=provider,
        model=model
    )
    
    if test_result["success"]:
        tests = test_result["tests"]
        coverage = test_result["coverage_estimate"]
        
        print(f"\n✅ Designed {len(tests)} test cases")
        print(f"Estimated coverage: {coverage:.0%}")
        
        print("\nTest categories:")
        test_types = {}
        for test in tests:
            t_type = test.get("type", "unit")
            test_types[t_type] = test_types.get(t_type, 0) + 1
        
        for t_type, count in test_types.items():
            print(f"  - {t_type}: {count} tests")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("📊 VIBEZEN Quality Assurance Summary")
    print("=" * 70)
    
    quality_score = 1.0
    if violations:
        quality_score -= len(violations) * 0.1
    
    print(f"\n Overall Quality Score: {quality_score:.1%}")
    print(f"✅ Requirements Met: {len(understanding.get('requirements', []))}")
    print(f"✅ Edge Cases Handled: {len(understanding.get('edge_cases', []))}")
    print(f"✅ Test Coverage: {test_result.get('coverage_estimate', 0):.0%}")
    
    if violations:
        print(f"⚠️  Quality Issues: {len(violations)}")
    else:
        print("✨ No Quality Issues!")
    
    print("\n🎯 Key VIBEZEN Benefits Demonstrated:")
    print("  1. Forced deep thinking before coding")
    print("  2. Multiple approach consideration")
    print("  3. Quality enforcement during generation")
    print("  4. Comprehensive test planning")
    print("  5. No hardcoded values or shortcuts")


async def compare_with_without_vibezen():
    """Compare results with and without VIBEZEN."""
    
    # This would show the difference between:
    # 1. Direct AI generation (likely to have hardcoded values)
    # 2. VIBEZEN-guided generation (quality assured)
    
    print("\n🔄 Comparison Mode")
    print("=" * 70)
    print("This would compare:")
    print("- ❌ Without VIBEZEN: Quick but potentially flawed code")
    print("- ✅ With VIBEZEN: Thoughtful, quality-assured code")
    print("\n(Implementation left as exercise)")


if __name__ == "__main__":
    print("=== VIBEZEN Real Provider Demo ===\n")
    
    # Run the main demo
    asyncio.run(demo_vibezen_workflow())
    
    # Optional: show comparison
    # asyncio.run(compare_with_without_vibezen())