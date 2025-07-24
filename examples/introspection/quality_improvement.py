#!/usr/bin/env python3
"""
Example of VIBEZEN introspection system improving code quality.

This example shows how the introspection system detects issues
and guides improvements through interactive dialogue.
"""

import asyncio
from vibezen.core.guard_v2_introspection import VIBEZENGuardV2WithIntrospection
from vibezen.core.types import CodeContext
from vibezen.introspection import QualityGrade


# Example of problematic code that needs improvement
PROBLEMATIC_CODE = '''
def calculate_user_score(user_data):
    """Calculate user score based on activity."""
    
    # Hardcoded values everywhere!
    api_url = "https://api.example.com/v1/score"
    secret_key = "sk-1234567890abcdef"
    max_score = 1000
    
    score = 0
    
    # Overly complex nested conditions
    if user_data["posts"] > 10:
        if user_data["comments"] > 50:
            if user_data["likes"] > 100:
                if user_data["shares"] > 20:
                    score = 900  # Magic number!
                else:
                    score = 700
            else:
                if user_data["shares"] > 10:
                    score = 600
                else:
                    score = 500
        else:
            if user_data["likes"] > 50:
                score = 400
            else:
                score = 300
    else:
        if user_data["comments"] > 20:
            score = 200
        else:
            score = 100
    
    # More hardcoded paths
    log_file = "/var/log/scoring.log"
    with open(log_file, "a") as f:
        f.write(f"User score: {score}\\n")
    
    return score
'''


async def mock_ai_introspection(prompt: str) -> str:
    """Mock AI response for introspection prompts."""
    print(f"\n🤖 AI Introspection Prompt:\n{prompt[:500]}...")
    
    # Simulate thinking delay
    await asyncio.sleep(1)
    
    # Return improved code based on the issues
    if "hardcode" in prompt.lower():
        return '''
I see several hardcoded values that should be externalized. Let me improve this:

```python
import os
from dataclasses import dataclass
from typing import Dict
import logging

@dataclass
class ScoringConfig:
    """Configuration for user scoring."""
    api_url: str = os.getenv("SCORING_API_URL", "https://api.example.com/v1/score")
    max_score: int = 1000
    
    # Scoring thresholds
    high_activity_threshold = {"posts": 10, "comments": 50, "likes": 100, "shares": 20}
    medium_activity_threshold = {"posts": 10, "comments": 50, "likes": 50, "shares": 10}
    low_activity_threshold = {"posts": 0, "comments": 20, "likes": 0, "shares": 0}
    
    # Score values
    scores = {
        "very_high": 900,
        "high": 700,
        "medium_high": 600,
        "medium": 500,
        "medium_low": 400,
        "low": 300,
        "very_low": 200,
        "minimal": 100
    }

def calculate_user_score(user_data: Dict[str, int], config: ScoringConfig = None) -> int:
    """Calculate user score based on activity."""
    if config is None:
        config = ScoringConfig()
    
    # Still has complexity issues, but hardcoding is fixed
    if user_data["posts"] > config.high_activity_threshold["posts"]:
        if user_data["comments"] > config.high_activity_threshold["comments"]:
            if user_data["likes"] > config.high_activity_threshold["likes"]:
                if user_data["shares"] > config.high_activity_threshold["shares"]:
                    score = config.scores["very_high"]
                else:
                    score = config.scores["high"]
            else:
                if user_data["shares"] > config.medium_activity_threshold["shares"]:
                    score = config.scores["medium_high"]
                else:
                    score = config.scores["medium"]
        else:
            if user_data["likes"] > config.medium_activity_threshold["likes"]:
                score = config.scores["medium_low"]
            else:
                score = config.scores["low"]
    else:
        if user_data["comments"] > config.low_activity_threshold["comments"]:
            score = config.scores["very_low"]
        else:
            score = config.scores["minimal"]
    
    # Use proper logging instead of hardcoded file
    logging.info(f"User score calculated: {score}")
    
    return score
```

The hardcoded values have been moved to configuration, but the complexity remains high.
'''
    
    elif "complexity" in prompt.lower():
        return '''
Now let me simplify the complex nested logic:

```python
import os
from dataclasses import dataclass
from typing import Dict
import logging

@dataclass 
class ScoringConfig:
    """Configuration for user scoring."""
    api_url: str = os.getenv("SCORING_API_URL", "https://api.example.com/v1/score")
    max_score: int = 1000

def calculate_activity_level(user_data: Dict[str, int]) -> str:
    """Determine user's activity level."""
    posts = user_data.get("posts", 0)
    comments = user_data.get("comments", 0) 
    likes = user_data.get("likes", 0)
    shares = user_data.get("shares", 0)
    
    # Clear, simple conditions
    if posts > 10 and comments > 50 and likes > 100 and shares > 20:
        return "very_high"
    elif posts > 10 and comments > 50 and likes > 100:
        return "high"
    elif posts > 10 and comments > 50 and shares > 10:
        return "medium_high"
    elif posts > 10 and comments > 50:
        return "medium"
    elif posts > 10 and likes > 50:
        return "medium_low"
    elif posts > 10:
        return "low"
    elif comments > 20:
        return "very_low"
    else:
        return "minimal"

def calculate_user_score(user_data: Dict[str, int], config: ScoringConfig = None) -> int:
    """
    Calculate user score based on activity.
    
    Args:
        user_data: Dictionary containing user activity metrics
        config: Optional scoring configuration
        
    Returns:
        User score between 0 and max_score
    """
    if config is None:
        config = ScoringConfig()
    
    # Activity level to score mapping
    level_scores = {
        "very_high": 900,
        "high": 700,
        "medium_high": 600,
        "medium": 500,
        "medium_low": 400,
        "low": 300,
        "very_low": 200,
        "minimal": 100
    }
    
    # Determine activity level
    activity_level = calculate_activity_level(user_data)
    
    # Get corresponding score
    score = level_scores.get(activity_level, 0)
    
    # Log the calculation
    logging.info(
        f"User score calculated: {score} "
        f"(activity_level: {activity_level}, metrics: {user_data})"
    )
    
    return score
```

Much better! The code is now:
- Free of hardcoded values
- Has reduced complexity through helper functions
- Is more readable and maintainable
- Properly documented
- Uses appropriate logging
'''
    
    return "No specific improvements suggested."


async def main():
    """Run introspection example."""
    print("=" * 60)
    print("VIBEZEN Introspection System Demo")
    print("=" * 60)
    
    # Initialize guard with introspection
    guard = VIBEZENGuardV2WithIntrospection(
        enable_introspection=True,
        introspection_callback=mock_ai_introspection,
        quality_threshold=80.0,
        max_introspection_rounds=3
    )
    
    # Step 1: Analyze the problematic code
    print("\n📊 Analyzing problematic code...")
    triggers = await guard.analyze_code_with_triggers(PROBLEMATIC_CODE)
    
    print(f"\nFound {len(triggers)} quality issues:")
    for trigger in triggers[:5]:  # Show first 5
        print(f"  - [{trigger.severity.upper()}] {trigger.trigger_type}: {trigger.message}")
    
    # Step 2: Generate improvement plan
    print("\n📋 Generating improvement plan...")
    plan = await guard.generate_quality_improvement_plan(PROBLEMATIC_CODE)
    
    print("\nPriority improvements:")
    for priority in plan["priorities"][:3]:
        print(f"  - {priority['issue']}")
    print(f"\nEstimated quality gain: +{plan['estimated_quality_gain']:.0f} points")
    
    # Step 3: Run interactive introspection
    print("\n🔄 Starting interactive introspection process...")
    
    context = CodeContext(
        code=PROBLEMATIC_CODE,
        specification={
            "name": "User Scoring System",
            "requirements": [
                "Calculate user score based on activity metrics",
                "Score should be between 0 and 1000",
                "Consider posts, comments, likes, and shares"
            ]
        }
    )
    
    # Create mock thinking steps
    from vibezen.core.types import ThinkingStep
    from datetime import datetime
    
    thinking_steps = [
        ThinkingStep(
            step_number=1,
            thought="Need to implement user scoring algorithm",
            confidence=0.7,
            timestamp=datetime.now()
        )
    ]
    
    # Run full introspection
    final_code, final_report = await guard.interactive_system.run_full_introspection(
        context, thinking_steps
    )
    
    # Step 4: Show results
    print("\n✅ Introspection Complete!")
    
    if final_report:
        print(f"\nQuality Report:")
        print(f"  Grade: {final_report.quality_grade.value}")
        print(f"  Score: {final_report.overall_score:.1f}/100")
        
        if final_report.strengths:
            print(f"\nStrengths:")
            for strength in final_report.strengths[:3]:
                print(f"  ✓ {strength}")
        
        if final_report.recommendations:
            print(f"\nRemaining recommendations:")
            for rec in final_report.recommendations[:3]:
                print(f"  → {rec}")
    
    # Show the improved code
    print("\n📝 Final improved code:")
    print("-" * 60)
    print(final_code[:500] + "..." if len(final_code) > 500 else final_code)
    
    # Get session summary
    sessions = list(guard.interactive_system.sessions.values())
    if sessions:
        session = sessions[-1]
        summary = guard.interactive_system.get_session_summary(session.session_id)
        
        print(f"\n📊 Introspection Summary:")
        print(f"  Iterations: {summary['iterations']}")
        print(f"  Triggers found: {summary['triggers_found']}")
        if 'total_improvement' in summary:
            print(f"  Total improvement: +{summary['total_improvement']:.1f} points")


if __name__ == "__main__":
    asyncio.run(main())