"""
Simplified demo of VIBEZEN's prompt intervention approach.

This shows the core concept without requiring external dependencies.
"""

# Simulated problematic AI code generation
PROBLEMATIC_CODE = """
def create_user_service():
    # AI generated this with hardcoded values
    db_host = "localhost"
    db_port = 5432
    db_password = "admin123"
    api_key = "sk-1234567890abcdef"
    timeout = 30
    
    return {
        "host": db_host,
        "port": db_port,
        "password": db_password,
        "api_key": api_key,
        "timeout": timeout
    }
"""

# VIBEZEN's thinking prompt that would be injected BEFORE code generation
VIBEZEN_THINKING_PROMPT = """
You are about to implement a feature based on a specification. 
Before writing any code, you must thoroughly understand what is being asked.

IMPORTANT: Take time to think step-by-step about this specification.

## Required Thinking Steps

You MUST think through AT LEAST 5 steps before proceeding:

1. **Core Requirements**: What exactly is being asked? List each requirement explicitly.
2. **Implicit Requirements**: What requirements are implied but not stated?
3. **Constraints**: What limitations or boundaries exist?
4. **Edge Cases**: What edge cases need to be handled?
5. **Dependencies**: What external systems or components are involved?

For each step, you must:
- State your current understanding
- Identify any ambiguities
- Note any assumptions you're making
- Consider if you need to revise previous steps

## Anti-Patterns to Avoid

DO NOT:
- Skip understanding to start coding immediately
- Make assumptions without stating them explicitly
- Ignore edge cases because they seem unlikely
- Add features not in the specification
- Hardcode values that should be configurable
"""

# VIBEZEN's implementation guidance prompt
VIBEZEN_IMPLEMENTATION_PROMPT = """
Now implement the user service with these CRITICAL REQUIREMENTS:

1. NO hardcoded values - use configuration or parameters
2. Implement ONLY what's specified - no extra features
3. Handle errors appropriately
4. Keep functions small and focused
5. Write clean, readable code

Remember:
- Database connection details should come from configuration
- API keys should NEVER be hardcoded
- Timeouts should be configurable
- Use environment variables or config files

Provide the implementation:
"""

# VIBEZEN's corrected implementation (what AI would generate with proper prompting)
CORRECTED_CODE = """
import os
from typing import Dict, Any

def create_user_service(config: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"
    Create a user service with configuration.
    
    Args:
        config: Configuration dictionary containing:
            - db_host: Database host
            - db_port: Database port  
            - db_password: Database password
            - api_key: API key for external services
            - timeout: Request timeout in seconds
            
    Returns:
        Dictionary with service configuration
    \"\"\"
    # Validate required configuration
    required_keys = ['db_host', 'db_port', 'db_password', 'api_key', 'timeout']
    missing_keys = [key for key in required_keys if key not in config]
    
    if missing_keys:
        raise ValueError(f"Missing required configuration: {missing_keys}")
    
    # Create service configuration
    return {
        "host": config['db_host'],
        "port": config['db_port'],
        "password": config['db_password'],
        "api_key": config['api_key'],
        "timeout": config['timeout']
    }

# Example usage with environment variables
def create_user_service_from_env() -> Dict[str, Any]:
    \"\"\"Create user service from environment variables.\"\"\"
    config = {
        'db_host': os.getenv('DB_HOST', 'localhost'),
        'db_port': int(os.getenv('DB_PORT', '5432')),
        'db_password': os.getenv('DB_PASSWORD'),  # Required, no default
        'api_key': os.getenv('API_KEY'),  # Required, no default
        'timeout': int(os.getenv('TIMEOUT', '30'))
    }
    
    # Check required values
    if not config['db_password']:
        raise ValueError("DB_PASSWORD environment variable is required")
    if not config['api_key']:
        raise ValueError("API_KEY environment variable is required")
    
    return create_user_service(config)
"""

# VIBEZEN's validation prompt
VIBEZEN_VALIDATION_PROMPT = """
Before finalizing this code, you must validate it against 
the specification and quality standards.

STOP and THINK: Does this code truly meet the requirements?

## Validation Checklist

Go through EACH item carefully:

### Specification Compliance
- [ ] Does the code implement ALL required features?
- [ ] Does it implement ONLY the required features (no extras)?
- [ ] Are all edge cases from the spec handled?

### Code Quality
- [ ] Are there any hardcoded values? List them: ___
- [ ] Is error handling implemented properly?
- [ ] Is the code testable?
- [ ] Are functions/classes appropriately sized?

### Anti-Patterns
- [ ] Is the code just trying to pass tests?
- [ ] Are there any shortcuts taken?
- [ ] Is there duplicated logic?

For any unchecked items, you MUST fix them before proceeding.
"""


def demonstrate_prompt_intervention():
    """Demonstrate how VIBEZEN intervenes at the prompt level."""
    print("=== VIBEZEN Prompt Intervention Demo ===\n")
    
    print("❌ WITHOUT VIBEZEN - AI generates problematic code:")
    print("-" * 50)
    print(PROBLEMATIC_CODE)
    print("-" * 50)
    
    print("\nProblems detected:")
    print("- Hardcoded database host: 'localhost'")
    print("- Hardcoded database port: 5432")
    print("- Hardcoded password: 'admin123' (CRITICAL SECURITY ISSUE!)")
    print("- Hardcoded API key: 'sk-1234567890abcdef' (CRITICAL SECURITY ISSUE!)")
    print("- Hardcoded timeout: 30")
    
    print("\n" + "="*70 + "\n")
    
    print("✅ WITH VIBEZEN - Prompt intervention process:")
    
    print("\n1️⃣ THINKING PROMPT (injected before coding):")
    print("-" * 50)
    print(VIBEZEN_THINKING_PROMPT[:500] + "...")
    print("-" * 50)
    
    print("\n2️⃣ IMPLEMENTATION PROMPT (with quality guidelines):")
    print("-" * 50)
    print(VIBEZEN_IMPLEMENTATION_PROMPT)
    print("-" * 50)
    
    print("\n3️⃣ RESULT - AI generates secure, configurable code:")
    print("-" * 50)
    print(CORRECTED_CODE)
    print("-" * 50)
    
    print("\n4️⃣ VALIDATION PROMPT (quality check):")
    print("-" * 50)
    print(VIBEZEN_VALIDATION_PROMPT[:400] + "...")
    print("-" * 50)
    
    print("\n" + "="*70 + "\n")
    print("✨ KEY IMPROVEMENTS:")
    print("- No hardcoded values - everything is configurable")
    print("- Proper error handling and validation")
    print("- Security-conscious implementation")
    print("- Clean, maintainable code structure")
    print("- Environment variable support with sensible defaults")
    
    print("\n🎯 VIBEZEN's Approach:")
    print("1. Intervene BEFORE code is written (not after)")
    print("2. Guide thinking through structured prompts")
    print("3. Enforce quality standards in the prompt")
    print("4. Validate results against requirements")
    print("5. Iterate if quality issues are found")


if __name__ == "__main__":
    demonstrate_prompt_intervention()