"""
Prompts for Sequential Thinking Engine
"""

# 思考ステップのプロンプトテンプレート
THINKING_STEP_PROMPT = """
You are analyzing a task through sequential thinking. This is step {step_number} of the {phase} phase.

Task: {task}

{context}

Previous thoughts:
{previous_thoughts}

Current confidence: {current_confidence:.2f}
Required confidence: {confidence_threshold:.2f}

Instructions:
1. Analyze the task deeply and methodically
2. Consider what aspects need more exploration
3. Express any uncertainties or concerns
4. Evaluate your confidence in the current understanding (0.0-1.0)
5. Determine if more thinking steps are needed

Provide your analysis in the following format:
THOUGHT: [Your analytical thought for this step]
CONFIDENCE: [0.0-1.0]
NEEDS_MORE_THINKING: [true/false]
REASON: [Why you need or don't need more thinking]
"""

# フェーズ別の追加コンテキスト
PHASE_CONTEXTS = {
    "spec_understanding": """
Focus on:
- Understanding the requirements completely
- Identifying implicit assumptions
- Recognizing potential edge cases
- Clarifying ambiguities
""",
    
    "implementation_choice": """
Focus on:
- Evaluating different implementation approaches
- Considering trade-offs between solutions
- Assessing maintainability and scalability
- Avoiding over-engineering
""",
    
    "code_design": """
Focus on:
- Designing clean, modular architecture
- Avoiding hardcoded values
- Ensuring proper abstraction levels
- Planning for testability
""",
    
    "quality_check": """
Focus on:
- Identifying potential bugs or issues
- Checking for spec compliance
- Evaluating code readability
- Ensuring no unnecessary complexity
""",
    
    "refinement": """
Focus on:
- Optimizing the implementation
- Removing redundancies
- Improving error handling
- Finalizing documentation needs
"""
}

# 思考サマリー生成プロンプト
THINKING_SUMMARY_PROMPT = """
Based on the following thinking steps, provide a comprehensive summary:

{thinking_steps}

Total steps: {total_steps}
Final confidence: {final_confidence:.2f}

Provide:
1. A concise summary of the key insights
2. Top 3-5 recommendations for implementation
3. Any warnings or concerns to address
"""

# 確信度評価プロンプト
CONFIDENCE_EVALUATION_PROMPT = """
Evaluate your confidence in understanding and implementing this task:

Task: {task}
Current analysis: {current_analysis}

Rate your confidence from 0.0 to 1.0 where:
- 0.0-0.3: Very uncertain, many unknowns
- 0.3-0.5: Some understanding but significant gaps
- 0.5-0.7: Moderate confidence with some concerns
- 0.7-0.9: Good confidence with minor uncertainties
- 0.9-1.0: Very confident, ready to implement

Provide a single float value.
"""