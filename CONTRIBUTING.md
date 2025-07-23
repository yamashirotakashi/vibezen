# Contributing to VIBEZEN

Thank you for your interest in contributing to VIBEZEN! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Issues

1. Check if the issue already exists
2. Create a new issue with a clear title and description
3. Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version, etc.)

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create an issue with the "enhancement" label
3. Clearly describe the feature and its benefits
4. Provide examples of how it would work

### Pull Requests

#### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/vibezen.git
cd vibezen

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,all]"

# Run tests to ensure everything works
pytest
```

#### Development Workflow

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards

3. Write tests for new functionality

4. Run tests and linting:
   ```bash
   pytest
   black src/ tests/
   ruff check src/ tests/
   mypy src/
   ```

5. Commit with clear messages:
   ```bash
   git commit -m "feat: add new prompt template for security analysis"
   ```

6. Push and create a pull request

### Coding Standards

#### Python Style

- Follow PEP 8
- Use Black for formatting
- Use type hints for all functions
- Maximum line length: 88 characters (Black default)

#### Documentation

- All public functions must have docstrings
- Use Google-style docstrings:
  ```python
  def function(param: str) -> bool:
      """Brief description.
      
      Args:
          param: Description of param.
          
      Returns:
          Description of return value.
          
      Raises:
          ValueError: When param is invalid.
      """
  ```

#### Testing

- Write tests for all new functionality
- Maintain or improve code coverage
- Use descriptive test names
- Group related tests in classes

### Areas for Contribution

#### 🎯 High Priority

1. **Prompt Templates**
   - Domain-specific templates (security, performance, etc.)
   - Language-specific templates (JavaScript, Go, etc.)
   - Framework-specific templates (React, Django, etc.)

2. **Provider Integrations**
   - Azure OpenAI support
   - Local LLM support (Ollama, etc.)
   - Custom provider framework

3. **Quality Checks**
   - New violation patterns
   - Language-specific checks
   - Security vulnerability detection

#### 🔧 Medium Priority

1. **Performance Optimizations**
   - Response caching
   - Parallel provider calls
   - Token usage optimization

2. **Integration Examples**
   - VS Code extension
   - GitHub Actions
   - GitLab CI/CD

3. **Documentation**
   - Tutorials and guides
   - Video demonstrations
   - API documentation improvements

#### 💡 Ideas Welcome

1. **Analytics and Reporting**
   - Quality metrics dashboard
   - Cost tracking
   - Thinking pattern analysis

2. **Advanced Features**
   - A/B testing framework
   - Template learning system
   - Multi-language support

## Testing Guidelines

### Unit Tests

```python
# test_example.py
import pytest
from vibezen.core import SomeClass

class TestSomeClass:
    def test_basic_functionality(self):
        """Test that basic functionality works."""
        obj = SomeClass()
        assert obj.method() == expected_value
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        obj = SomeClass()
        result = await obj.async_method()
        assert result == expected_value
```

### Integration Tests

- Test with mock providers by default
- Use `@pytest.mark.integration` for real provider tests
- Real provider tests require API keys in environment

### Test Coverage

- Aim for >80% coverage
- Focus on critical paths
- Don't test for the sake of coverage

## Documentation

### Code Documentation

- Update docstrings when changing functionality
- Keep examples up to date
- Document breaking changes clearly

### User Documentation

- Update README.md for user-facing changes
- Add to docs/ for detailed explanations
- Include examples for new features

## Release Process

1. **Version Bumping**
   - Follow Semantic Versioning
   - Update version in setup.py
   - Update CHANGELOG.md

2. **Release Checklist**
   - [ ] All tests pass
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   - [ ] Version bumped
   - [ ] PR approved by maintainer

## Getting Help

- **Discord**: Join our community for discussions
- **GitHub Discussions**: For questions and ideas
- **Email**: dev@vibezen.ai for private concerns

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for helping make VIBEZEN better! 🚀