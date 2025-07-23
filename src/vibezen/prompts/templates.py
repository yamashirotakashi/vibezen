"""
VIBEZEN Prompt Templates Collection.

Pre-built templates for common scenarios.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from vibezen.prompts.template_engine import (
    PromptTemplate,
    PromptSection,
    PromptVariable,
)
from vibezen.core.models import ThinkingPhase


class HardcodeDetectionTemplate(PromptTemplate):
    """Template for detecting and preventing hardcoded values."""
    
    def __init__(self):
        super().__init__("hardcode_detection", ThinkingPhase.IMPLEMENTATION)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="alert",
                content="""⚠️ HARDCODE DETECTION WARNING ⚠️

The following hardcoded values have been detected in your code:
{hardcoded_values}

Hardcoding values makes code inflexible, unmaintainable, and environment-specific.""",
                variables=[
                    PromptVariable("hardcoded_values", "", "List of hardcoded values", required=True)
                ],
                order=1,
            ),
            PromptSection(
                name="analysis",
                content="""## Required Analysis

For EACH hardcoded value, you must:

1. **Identify**: What is the hardcoded value?
2. **Purpose**: Why does this value exist?
3. **Impact**: What happens if this value needs to change?
4. **Solution**: How should this be made configurable?

Example transformations:
- `port = 8080` → `port = config.get('port', 8080)`
- `api_url = "http://localhost"` → `api_url = os.getenv('API_URL', 'http://localhost')`
- `timeout = 30` → `timeout = settings.TIMEOUT`""",
                order=2,
            ),
            PromptSection(
                name="correction",
                content="""## Provide Corrected Code

Rewrite the code with ALL hardcoded values properly externalized:

```{language}
# Your corrected code here
```

Explain each change you made.""",
                variables=[
                    PromptVariable("language", "python", "Programming language", default="python")
                ],
                order=3,
            ),
        ]


class OverImplementationTemplate(PromptTemplate):
    """Template for detecting features not in specification."""
    
    def __init__(self):
        super().__init__("over_implementation", ThinkingPhase.IMPLEMENTATION)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="alert",
                content="""🚨 OVER-IMPLEMENTATION DETECTED 🚨

The following features are NOT in the specification:
{extra_features}

Adding unspecified features increases complexity, testing burden, and maintenance cost.""",
                variables=[
                    PromptVariable("extra_features", "", "List of extra features", required=True)
                ],
                order=1,
            ),
            PromptSection(
                name="specification_review",
                content="""## Specification Review

Original specification requirements:
{spec_requirements}

Your implementation includes:
{implemented_features}

Features to REMOVE:
{features_to_remove}""",
                variables=[
                    PromptVariable("spec_requirements", "", "Original requirements"),
                    PromptVariable("implemented_features", "", "What was implemented"),
                    PromptVariable("features_to_remove", "", "Features to remove"),
                ],
                order=2,
            ),
            PromptSection(
                name="correction",
                content="""## Required Action

You MUST:
1. Remove all features not in the specification
2. Keep ONLY what was requested
3. Resist the urge to "improve" beyond requirements

Provide the corrected code that implements ONLY the specified features.""",
                order=3,
            ),
        ]


class ComplexityReductionTemplate(PromptTemplate):
    """Template for reducing code complexity."""
    
    def __init__(self):
        super().__init__("complexity_reduction", ThinkingPhase.OPTIMIZATION)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="alert",
                content="""📊 HIGH COMPLEXITY DETECTED 📊

Complexity Score: {complexity_score}
Threshold: {threshold}

Complex code is harder to understand, test, and maintain.""",
                variables=[
                    PromptVariable("complexity_score", "", "Current complexity score"),
                    PromptVariable("threshold", "10", "Complexity threshold", default="10"),
                ],
                order=1,
            ),
            PromptSection(
                name="analysis",
                content="""## Complexity Analysis

Problem areas:
{problem_areas}

Refactoring suggestions:
1. Extract methods for code blocks > 10 lines
2. Reduce nesting levels (max 3)
3. Simplify conditional logic
4. Use early returns
5. Apply Single Responsibility Principle""",
                variables=[
                    PromptVariable("problem_areas", "", "Areas with high complexity")
                ],
                order=2,
            ),
            PromptSection(
                name="refactoring",
                content="""## Refactoring Plan

Break down the complex code:

1. Identify logical units
2. Extract to separate functions
3. Add clear names and documentation
4. Ensure each function does ONE thing

Provide the refactored code with reduced complexity.""",
                order=3,
            ),
        ]


class TestGamingPreventionTemplate(PromptTemplate):
    """Template for preventing test-focused implementation."""
    
    def __init__(self):
        super().__init__("test_gaming_prevention", ThinkingPhase.TEST_DESIGN)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="principle",
                content="""## Implementation Principle

Your code should solve the ACTUAL PROBLEM, not just pass tests.

Tests verify behavior, they don't define it. The specification defines behavior.""",
                order=1,
            ),
            PromptSection(
                name="review",
                content="""## Implementation Review

Current implementation approach:
{implementation_approach}

Ask yourself:
- Does this solve the real problem?
- Would this work in production?
- Am I taking shortcuts just to pass tests?
- Is this maintainable long-term?""",
                variables=[
                    PromptVariable("implementation_approach", "", "Current approach")
                ],
                order=2,
            ),
            PromptSection(
                name="correction",
                content="""## Correct Approach

Focus on:
1. Understanding the business need
2. Implementing a robust solution
3. Handling edge cases properly
4. Making code maintainable

Tests should VERIFY your solution, not DRIVE it.""",
                order=3,
            ),
        ]


class ConsensusTemplate(PromptTemplate):
    """Template for multi-AI consensus building."""
    
    def __init__(self):
        super().__init__("consensus_building", ThinkingPhase.IMPLEMENTATION_CHOICE)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="introduction",
                content="""## Multi-Perspective Analysis

You are one of several AI assistants analyzing this problem.
Provide your independent perspective on the best approach.""",
                order=1,
            ),
            PromptSection(
                name="problem_statement",
                content="""## Problem to Analyze

{problem_description}

Context:
- Specification: {specification}
- Constraints: {constraints}
- Previous attempts: {previous_attempts}""",
                variables=[
                    PromptVariable("problem_description", "", "Problem description"),
                    PromptVariable("specification", "", "Specification summary"),
                    PromptVariable("constraints", "None", "Constraints", default="None"),
                    PromptVariable("previous_attempts", "None", "Previous attempts", default="None"),
                ],
                order=2,
            ),
            PromptSection(
                name="perspective_request",
                content="""## Your Analysis

Provide:
1. Your understanding of the problem
2. Recommended approach
3. Potential risks or concerns
4. Why your approach is optimal

Be specific and justify your reasoning.""",
                order=3,
            ),
            PromptSection(
                name="other_perspectives",
                content="""## Other Perspectives (if available)

{other_perspectives}

After reviewing these, do you want to:
- Maintain your position (explain why)
- Modify your approach (explain changes)
- Support another approach (explain why)""",
                variables=[
                    PromptVariable("other_perspectives", "", "Other AI perspectives", required=False)
                ],
                condition="other_perspectives is not None",
                order=4,
            ),
        ]


class CriticalReviewTemplate(PromptTemplate):
    """Template for critical code review."""
    
    def __init__(self):
        super().__init__("critical_review", ThinkingPhase.QUALITY_REVIEW)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="introduction",
                content="""## Critical Code Review

Review this code with a critical eye. Look for issues, not just syntax.
Focus on correctness, maintainability, and alignment with specifications.""",
                order=1,
            ),
            PromptSection(
                name="code",
                content="""## Code Under Review

```{language}
{code}
```""",
                variables=[
                    PromptVariable("language", "python", "Language", default="python"),
                    PromptVariable("code", "", "Code to review", required=True),
                ],
                order=2,
            ),
            PromptSection(
                name="review_checklist",
                content="""## Review Checklist

### Correctness
- [ ] Does it implement the specification correctly?
- [ ] Are edge cases handled?
- [ ] Is error handling appropriate?

### Quality
- [ ] Is the code readable and well-structured?
- [ ] Are there any code smells?
- [ ] Is it properly documented?

### Maintainability
- [ ] Will this be easy to modify?
- [ ] Are dependencies minimized?
- [ ] Is it testable?

### Security
- [ ] Are inputs validated?
- [ ] Are there any security vulnerabilities?
- [ ] Is sensitive data handled properly?

### Performance
- [ ] Are there obvious performance issues?
- [ ] Is resource usage appropriate?
- [ ] Are there unnecessary operations?""",
                order=3,
            ),
            PromptSection(
                name="findings",
                content="""## Critical Findings

List ALL issues found, ordered by severity:

1. **Critical Issues** (must fix)
2. **Major Issues** (should fix)
3. **Minor Issues** (nice to fix)
4. **Suggestions** (improvements)

For each issue, provide:
- What is wrong
- Why it's a problem
- How to fix it""",
                order=4,
            ),
        ]


class PromptTemplates:
    """Collection of all available prompt templates."""
    
    @staticmethod
    def get_all_templates() -> List[PromptTemplate]:
        """Get all available templates."""
        return [
            HardcodeDetectionTemplate(),
            OverImplementationTemplate(),
            ComplexityReductionTemplate(),
            TestGamingPreventionTemplate(),
            ConsensusTemplate(),
            CriticalReviewTemplate(),
        ]
    
    @staticmethod
    def get_template_by_issue(issue_type: str) -> Optional[PromptTemplate]:
        """Get template for specific issue type."""
        mapping = {
            "hardcode": HardcodeDetectionTemplate,
            "over_implementation": OverImplementationTemplate,
            "complexity": ComplexityReductionTemplate,
            "test_gaming": TestGamingPreventionTemplate,
            "consensus": ConsensusTemplate,
            "review": CriticalReviewTemplate,
        }
        
        template_class = mapping.get(issue_type.lower())
        return template_class() if template_class else None