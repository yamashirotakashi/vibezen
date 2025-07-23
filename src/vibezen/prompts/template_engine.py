"""
VIBEZEN Prompt Template Engine.

Generates dynamic prompts to guide AI thinking at each phase.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
from pathlib import Path
import asyncio
from datetime import datetime

from vibezen.core.models import (
    ThinkingPhase,
    ThinkingContext,
    PromptMetadata,
)


@dataclass
class PromptVariable:
    """Variable that can be injected into prompts."""
    name: str
    value: Any
    description: str = ""
    required: bool = True
    default: Any = None
    
    def resolve(self, context: Dict[str, Any]) -> Any:
        """Resolve variable value from context."""
        if self.name in context:
            return context[self.name]
        elif self.default is not None:
            return self.default
        elif self.required:
            raise ValueError(f"Required variable '{self.name}' not found in context")
        return None


@dataclass
class PromptSection:
    """A section of a prompt template."""
    name: str
    content: str
    variables: List[PromptVariable] = field(default_factory=list)
    condition: Optional[str] = None  # Python expression to evaluate
    order: int = 0
    
    def should_include(self, context: Dict[str, Any]) -> bool:
        """Check if this section should be included."""
        if not self.condition:
            return True
        try:
            # Safe evaluation with limited context
            return eval(self.condition, {"__builtins__": {}}, context)
        except Exception:
            return False
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render section with variables replaced."""
        rendered = self.content
        for var in self.variables:
            value = var.resolve(context)
            if value is not None:
                placeholder = f"{{{var.name}}}"
                rendered = rendered.replace(placeholder, str(value))
        return rendered


class PromptTemplate(ABC):
    """Base class for prompt templates."""
    
    def __init__(self, name: str, phase: ThinkingPhase):
        self.name = name
        self.phase = phase
        self.sections: List[PromptSection] = []
        self.metadata = PromptMetadata(
            template_name=name,
            phase=phase,
            created_at=datetime.utcnow(),
        )
    
    @abstractmethod
    def build_sections(self) -> List[PromptSection]:
        """Build template sections. Must be implemented by subclasses."""
        pass
    
    def add_section(self, section: PromptSection) -> None:
        """Add a section to the template."""
        self.sections.append(section)
        self.sections.sort(key=lambda s: s.order)
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render the complete prompt."""
        if not self.sections:
            self.sections = self.build_sections()
        
        rendered_sections = []
        for section in self.sections:
            if section.should_include(context):
                rendered = section.render(context)
                if rendered.strip():
                    rendered_sections.append(rendered)
        
        return "\n\n".join(rendered_sections)
    
    def get_required_variables(self) -> List[str]:
        """Get list of required variables for this template."""
        required = []
        for section in self.sections:
            for var in section.variables:
                if var.required and var.name not in required:
                    required.append(var.name)
        return required


class SpecUnderstandingTemplate(PromptTemplate):
    """Template for specification understanding phase."""
    
    def __init__(self):
        super().__init__("spec_understanding", ThinkingPhase.SPEC_UNDERSTANDING)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="introduction",
                content="""You are about to implement a feature based on a specification. 
Before writing any code, you must thoroughly understand what is being asked.

IMPORTANT: Take time to think step-by-step about this specification.""",
                order=1,
            ),
            PromptSection(
                name="specification",
                content="## Specification\n\n{specification}",
                variables=[
                    PromptVariable("specification", "", "The specification to understand", required=True)
                ],
                order=2,
            ),
            PromptSection(
                name="thinking_requirements",
                content="""## Required Thinking Steps

You MUST think through AT LEAST {min_steps} steps before proceeding:

1. **Core Requirements**: What exactly is being asked? List each requirement explicitly.
2. **Implicit Requirements**: What requirements are implied but not stated?
3. **Constraints**: What limitations or boundaries exist?
4. **Edge Cases**: What edge cases need to be handled?
5. **Dependencies**: What external systems or components are involved?
{additional_steps}

For each step, you must:
- State your current understanding
- Identify any ambiguities
- Note any assumptions you're making
- Consider if you need to revise previous steps""",
                variables=[
                    PromptVariable("min_steps", 5, "Minimum thinking steps", default=5),
                    PromptVariable("additional_steps", "", "Additional custom steps", required=False),
                ],
                order=3,
            ),
            PromptSection(
                name="anti_patterns",
                content="""## Anti-Patterns to Avoid

DO NOT:
- Skip understanding to start coding immediately
- Make assumptions without stating them explicitly
- Ignore edge cases because they seem unlikely
- Add features not in the specification
- Hardcode values that should be configurable""",
                order=4,
            ),
            PromptSection(
                name="previous_violations",
                content="""## Learn from Previous Issues

Previous violations in similar contexts:
{violations}

Make sure not to repeat these mistakes.""",
                variables=[
                    PromptVariable("violations", "", "Previous violations", required=False)
                ],
                condition="violations is not None and len(violations) > 0",
                order=5,
            ),
        ]


class ImplementationChoiceTemplate(PromptTemplate):
    """Template for implementation choice phase."""
    
    def __init__(self):
        super().__init__("implementation_choice", ThinkingPhase.IMPLEMENTATION_CHOICE)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="introduction",
                content="""Now that you understand the specification, you need to choose 
the best implementation approach.

IMPORTANT: Consider multiple approaches and think through trade-offs.""",
                order=1,
            ),
            PromptSection(
                name="context",
                content="""## Context

Specification Summary: {spec_summary}
Technology Stack: {tech_stack}
Constraints: {constraints}""",
                variables=[
                    PromptVariable("spec_summary", "", "Summary of specification"),
                    PromptVariable("tech_stack", "", "Technology stack", default="Not specified"),
                    PromptVariable("constraints", "", "Implementation constraints", default="None"),
                ],
                order=2,
            ),
            PromptSection(
                name="approach_requirements",
                content="""## Implementation Approach Analysis

You MUST consider AT LEAST {min_approaches} different approaches:

For each approach:
1. **Description**: What is the approach?
2. **Pros**: What are the advantages?
3. **Cons**: What are the disadvantages?
4. **Complexity**: How complex is this approach?
5. **Maintainability**: How easy will it be to maintain?
6. **Performance**: What are the performance implications?
7. **Testability**: How easy will it be to test?

After analyzing all approaches, choose the best one and explain WHY.""",
                variables=[
                    PromptVariable("min_approaches", 3, "Minimum approaches to consider", default=3),
                ],
                order=3,
            ),
            PromptSection(
                name="quality_criteria",
                content="""## Quality Criteria

Your chosen approach MUST:
- Implement ONLY what's in the specification
- Avoid hardcoded values
- Be testable with clear boundaries
- Handle errors gracefully
- Be maintainable and readable
- Follow established patterns in the codebase""",
                order=4,
            ),
        ]


class CodeValidationTemplate(PromptTemplate):
    """Template for code validation phase."""
    
    def __init__(self):
        super().__init__("code_validation", ThinkingPhase.IMPLEMENTATION)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="introduction",
                content="""Before finalizing this code, you must validate it against 
the specification and quality standards.

STOP and THINK: Does this code truly meet the requirements?""",
                order=1,
            ),
            PromptSection(
                name="code_to_validate",
                content="""## Code to Validate

```{language}
{code}
```""",
                variables=[
                    PromptVariable("language", "python", "Programming language", default="python"),
                    PromptVariable("code", "", "Code to validate", required=True),
                ],
                order=2,
            ),
            PromptSection(
                name="validation_checklist",
                content="""## Validation Checklist

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

For any unchecked items, you MUST fix them before proceeding.""",
                order=3,
            ),
            PromptSection(
                name="improvement_prompt",
                content="""## Required Improvements

Based on your validation, what needs to be fixed?
Be specific and provide corrected code.""",
                order=4,
            ),
        ]


class TestDesignTemplate(PromptTemplate):
    """Template for test design phase."""
    
    def __init__(self):
        super().__init__("test_design", ThinkingPhase.TEST_DESIGN)
    
    def build_sections(self) -> List[PromptSection]:
        return [
            PromptSection(
                name="introduction",
                content="""You need to design comprehensive tests that verify the 
implementation meets the specification.

IMPORTANT: Tests should verify behavior, not implementation details.""",
                order=1,
            ),
            PromptSection(
                name="test_categories",
                content="""## Required Test Categories

You MUST include tests for:

1. **Happy Path**: Normal expected usage
2. **Edge Cases**: Boundary conditions and limits
3. **Error Cases**: Invalid inputs and error conditions
4. **Integration**: How components work together
5. **Performance**: If there are performance requirements

For each category, list specific test cases.""",
                order=2,
            ),
            PromptSection(
                name="test_design_principles",
                content="""## Test Design Principles

Your tests MUST:
- Test behavior, not implementation
- Be independent and isolated
- Have clear assertions
- Use descriptive names
- Cover all specification requirements
- NOT test features that weren't specified""",
                order=3,
            ),
        ]


class PromptTemplateEngine:
    """Engine for managing and rendering prompt templates."""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._initialize_default_templates()
        self.context_stack: List[Dict[str, Any]] = []
    
    def _initialize_default_templates(self):
        """Initialize default templates."""
        self.register_template(SpecUnderstandingTemplate())
        self.register_template(ImplementationChoiceTemplate())
        self.register_template(CodeValidationTemplate())
        self.register_template(TestDesignTemplate())
    
    def register_template(self, template: PromptTemplate) -> None:
        """Register a prompt template."""
        key = f"{template.phase.value}:{template.name}"
        self.templates[key] = template
    
    def get_template(self, phase: ThinkingPhase, name: Optional[str] = None) -> Optional[PromptTemplate]:
        """Get template for a phase."""
        if name:
            key = f"{phase.value}:{name}"
        else:
            # Find first template for phase
            for key, template in self.templates.items():
                if key.startswith(f"{phase.value}:"):
                    return template
            return None
        
        return self.templates.get(key)
    
    def push_context(self, context: Dict[str, Any]) -> None:
        """Push context onto stack."""
        self.context_stack.append(context)
    
    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop context from stack."""
        return self.context_stack.pop() if self.context_stack else None
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get merged current context."""
        merged = {}
        for ctx in self.context_stack:
            merged.update(ctx)
        return merged
    
    async def generate_prompt(
        self,
        phase: ThinkingPhase,
        context: Dict[str, Any],
        template_name: Optional[str] = None,
    ) -> str:
        """Generate a prompt for a specific phase."""
        template = self.get_template(phase, template_name)
        if not template:
            raise ValueError(f"No template found for phase {phase}")
        
        # Merge with current context
        full_context = self.get_current_context()
        full_context.update(context)
        
        # Add phase-specific context
        full_context["phase"] = phase.value
        full_context["timestamp"] = datetime.utcnow().isoformat()
        
        # Render template
        prompt = template.render(full_context)
        
        # Log for debugging
        await self._log_prompt_generation(phase, template.name, prompt)
        
        return prompt
    
    async def _log_prompt_generation(self, phase: ThinkingPhase, template_name: str, prompt: str) -> None:
        """Log prompt generation for debugging."""
        # In production, this would log to a proper logging system
        print(f"[VIBEZEN] Generated prompt for {phase.value} using {template_name}")
        if len(prompt) > 200:
            print(f"[VIBEZEN] Prompt preview: {prompt[:200]}...")
        else:
            print(f"[VIBEZEN] Prompt: {prompt}")
    
    def create_checkpoint_prompt(self, checkpoint_name: str, context: Dict[str, Any]) -> str:
        """Create a checkpoint prompt for validation."""
        prompt = f"""## Checkpoint: {checkpoint_name}

Before proceeding, validate your current state:

1. What have you accomplished so far?
2. Does it align with the specification?
3. Are there any issues or concerns?
4. What needs to be done next?

Current context:
- Phase: {context.get('phase', 'Unknown')}
- Progress: {context.get('progress', 'Unknown')}
- Confidence: {context.get('confidence', 'Unknown')}

If you have any concerns, you must address them before continuing."""
        
        return prompt
    
    def create_intervention_prompt(self, issue_type: str, details: Dict[str, Any]) -> str:
        """Create an intervention prompt when issues are detected."""
        prompt = f"""## ATTENTION REQUIRED: {issue_type}

An issue has been detected that requires your attention:

{details.get('description', 'No description provided')}

You MUST:
1. Acknowledge the issue
2. Explain how you will address it
3. Provide corrected approach/code

Do not proceed until this issue is resolved."""
        
        if "suggestions" in details:
            prompt += f"\n\nSuggestions:\n{details['suggestions']}"
        
        return prompt
    
    def save_templates(self, path: Path) -> None:
        """Save templates to file."""
        data = {}
        for key, template in self.templates.items():
            data[key] = {
                "name": template.name,
                "phase": template.phase.value,
                "sections": [
                    {
                        "name": section.name,
                        "content": section.content,
                        "variables": [
                            {
                                "name": var.name,
                                "description": var.description,
                                "required": var.required,
                                "default": var.default,
                            }
                            for var in section.variables
                        ],
                        "condition": section.condition,
                        "order": section.order,
                    }
                    for section in template.sections
                ],
            }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_templates(self, path: Path) -> None:
        """Load templates from file."""
        with open(path, "r") as f:
            data = json.load(f)
        
        # Clear existing templates
        self.templates.clear()
        
        # Create templates from data
        for key, template_data in data.items():
            # This would need more sophisticated reconstruction
            # For now, just use defaults
            pass