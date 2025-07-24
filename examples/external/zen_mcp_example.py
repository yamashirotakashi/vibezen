#!/usr/bin/env python3
"""
Example of VIBEZEN zen-MCP integration.

This example demonstrates how zen-MCP enhances VIBEZEN's
quality assurance capabilities through deep thinking,
code review, and consensus building.
"""

import asyncio
from vibezen.external.zen_mcp import (
    ZenMCPClient,
    ZenMCPConfig,
    ZenMCPIntegration,
)
from vibezen.core.types import (
    CodeContext,
    SpecificationAnalysis,
    IntrospectionTrigger,
    QualityReport,
)
from vibezen.core.guard_v2_introspection import VIBEZENGuardV2WithIntrospection


# Example problematic code
EXAMPLE_CODE = '''
def process_user_data(users):
    """Process user data and send to API."""
    api_url = "https://api.example.com/v1/users"
    api_key = "sk-1234567890abcdef"
    timeout = 30
    
    results = []
    for user in users:
        # Complex nested logic
        if user["age"] > 18:
            if user["country"] == "US":
                if user["subscription"] == "premium":
                    if user["verified"]:
                        score = 100
                    else:
                        score = 80
                else:
                    score = 60
            else:
                if user["subscription"] == "premium":
                    score = 70
                else:
                    score = 50
        else:
            score = 0
        
        # Send to API (simplified)
        data = {
            "user_id": user["id"],
            "score": score,
            "api_key": api_key
        }
        # response = requests.post(api_url, json=data, timeout=timeout)
        results.append({"user_id": user["id"], "score": score})
    
    return results
'''

EXAMPLE_SPECIFICATION = {
    "name": "User Scoring System",
    "version": "1.0.0",
    "description": "Score users based on their profile and subscription",
    "requirements": [
        "Calculate user scores based on age, location, and subscription",
        "Integrate with external API for score submission",
        "Handle different user types appropriately",
        "Ensure secure API communication",
        "Provide clear scoring logic"
    ],
    "constraints": [
        "Must not hardcode sensitive data",
        "Score calculation should be maintainable",
        "API calls should handle errors gracefully"
    ]
}


async def demonstrate_zen_mcp_integration():
    """Demonstrate zen-MCP integration with VIBEZEN."""
    print("=" * 60)
    print("VIBEZEN zen-MCP Integration Demo")
    print("=" * 60)
    
    # Configure zen-MCP
    zen_config = ZenMCPConfig(
        enable_challenge=True,
        enable_consensus=True,
        enable_websearch=True,
        thinking_mode="high",
        default_model="gemini-2.5-pro"
    )
    
    # Create integration
    integration = ZenMCPIntegration(zen_config)
    
    # Initialize VIBEZEN guard
    guard = VIBEZENGuardV2WithIntrospection(
        enable_introspection=True,
        quality_threshold=80.0
    )
    
    async with integration:
        # Step 1: Enhance specification analysis
        print("\n📋 Step 1: Analyzing specification with zen-MCP...")
        
        initial_analysis = SpecificationAnalysis(
            specification_id="user-scoring-v1",
            confidence=0.7,
            clarity_score=0.8,
            completeness_score=0.7,
            testability_score=0.8,
            key_requirements=[
                "Score calculation",
                "API integration",
                "Security"
            ],
            potential_issues=[
                "Scoring logic not fully specified"
            ],
            implementation_hints={
                "approach": "Implement scoring engine with API client"
            },
            metadata={}
        )
        
        enhanced_analysis = await integration.enhance_specification_analysis(
            EXAMPLE_SPECIFICATION,
            initial_analysis
        )
        
        print(f"  Initial confidence: {initial_analysis.confidence:.2f}")
        print(f"  Enhanced confidence: {enhanced_analysis.confidence:.2f}")
        print(f"  New issues found: {len(enhanced_analysis.potential_issues) - len(initial_analysis.potential_issues)}")
        
        # Step 2: Generate thinking steps
        print("\n🤔 Step 2: Generating thinking steps...")
        
        context = CodeContext(
            code="",
            specification=EXAMPLE_SPECIFICATION
        )
        
        thinking_steps = await integration.generate_thinking_steps(context, min_steps=4)
        
        print(f"  Generated {len(thinking_steps)} thinking steps:")
        for step in thinking_steps:
            print(f"    {step.step_number}. {step.thought[:50]}... (confidence: {step.confidence:.2f})")
        
        # Step 3: Analyze the problematic code
        print("\n🔍 Step 3: Analyzing code with introspection...")
        
        # First, use VIBEZEN to detect triggers
        triggers = await guard.analyze_code_with_triggers(
            EXAMPLE_CODE,
            EXAMPLE_SPECIFICATION
        )
        
        print(f"  Found {len(triggers)} quality issues:")
        for trigger in triggers[:5]:
            print(f"    - [{trigger.severity}] {trigger.trigger_type}: {trigger.message}")
        
        # Step 4: Review code quality with zen-MCP
        print("\n📊 Step 4: Deep code review with zen-MCP...")
        
        quality_report = await integration.review_code_quality(
            EXAMPLE_CODE,
            EXAMPLE_SPECIFICATION,
            triggers
        )
        
        print(f"  Quality score: {quality_report.score:.1f}/100")
        print(f"  Assessment: {quality_report.overall_assessment}")
        print(f"  Strengths: {len(quality_report.strengths)}")
        print(f"  Issues: {len(quality_report.issues)}")
        
        # Step 5: Challenge if confidence is low
        print("\n🤨 Step 5: Challenging implementation decisions...")
        
        challenge_result = await integration.challenge_implementation(
            EXAMPLE_CODE,
            "Simple nested if-else implementation for scoring",
            confidence=0.6
        )
        
        if challenge_result.get("challenged"):
            print(f"  Original confidence: {challenge_result['original_confidence']:.2f}")
            print(f"  Should reconsider: {challenge_result['should_reconsider']}")
        
        # Step 6: Generate improvement strategy
        print("\n🎯 Step 6: Generating improvement strategy...")
        
        strategy = await integration.generate_improvement_strategy(
            EXAMPLE_CODE,
            triggers,
            quality_report.score
        )
        
        print(f"  Current score: {strategy['current_score']:.1f}")
        print(f"  Target score: {strategy['target_score']:.1f}")
        print(f"  Immediate actions: {len(strategy['immediate_actions'])}")
        print(f"  Estimated effort: {strategy['estimated_effort']}")
        
        if strategy['immediate_actions']:
            print("\n  Top priority actions:")
            for action in strategy['immediate_actions'][:3]:
                print(f"    • {action['issue']}")
                print(f"      → {action['action']}")
        
        # Step 7: Build consensus (if multiple assessments)
        print("\n🤝 Step 7: Building consensus on quality...")
        
        # Create another quality report for demonstration
        alternative_report = QualityReport(
            overall_assessment="needs_improvement",
            score=55.0,
            strengths=["Clear intent"],
            issues=["Security risks", "Poor maintainability"],
            recommendations=["Major refactoring needed"]
        )
        
        consensus = await integration.build_consensus_on_quality(
            EXAMPLE_CODE,
            [quality_report, alternative_report]
        )
        
        print(f"  Average score: {consensus['average_score']:.1f}")
        print(f"  Score variance: {consensus['score_variance']:.1f}")
        
        # Step 8: Show improved code suggestion
        print("\n✨ Step 8: Suggested improvements...")
        
        print("\nKey improvements needed:")
        print("1. Extract configuration (API URL, credentials)")
        print("2. Simplify scoring logic with a scoring matrix")
        print("3. Add error handling for API calls")
        print("4. Implement proper logging")
        print("5. Add input validation")
        
        print("\nExample refactored structure:")
        print("""
```python
@dataclass
class ScoringConfig:
    age_threshold: int = 18
    score_matrix: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "US": {"premium_verified": 100, "premium": 80, "standard": 60},
        "OTHER": {"premium": 70, "standard": 50}
    })

class UserScoringService:
    def __init__(self, config: ScoringConfig, api_client: APIClient):
        self.config = config
        self.api_client = api_client
    
    def calculate_score(self, user: Dict[str, Any]) -> int:
        if user.get("age", 0) <= self.config.age_threshold:
            return 0
        
        country_key = "US" if user.get("country") == "US" else "OTHER"
        subscription_key = f"{user.get('subscription', 'standard')}"
        if user.get("verified") and subscription_key == "premium":
            subscription_key = "premium_verified"
        
        return self.config.score_matrix.get(country_key, {}).get(subscription_key, 0)
```
        """)


async def main():
    """Run the demonstration."""
    try:
        await demonstrate_zen_mcp_integration()
        print("\n✅ Demo completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())