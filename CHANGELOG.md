# Changelog

All notable changes to VIBEZEN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-01-23

### Changed
- **IMPORTANT**: Anthropic provider disabled to avoid self-referential usage in VIBEZEN

### Removed
- Anthropic provider from auto-discovery in registry
- Anthropic references from configuration examples
- Anthropic from installation options

## [2.0.0] - 2025-01-23

### Changed
- **BREAKING**: Complete paradigm shift from monitoring to prompt intervention
- **BREAKING**: New API based on VIBEZENGuardV2 class
- **BREAKING**: Configuration structure completely redesigned

### Added
- AI Proxy Layer for transparent prompt intervention
- Multi-provider support (OpenAI, Google)
- Thinking trace extraction from all providers
- Dynamic prompt templates with Jinja2
- Phase-based workflow management
- Provider-specific thinking pattern recognition
- Async/await support throughout
- Comprehensive provider integration guide
- Real-world examples with actual AI providers

### Removed
- Post-generation monitoring approach
- Old VIBEZENGuard class
- Legacy configuration format

### Fixed
- Hardcoding now prevented at generation time
- Surface-level implementations eliminated
- Over-implementation controlled through guided thinking

## [1.0.0] - 2025-01-20 (Initial Design)

### Added
- Initial concept of Sequential Thinking Engine
- Basic monitoring approach (later replaced)
- Core project structure
- Integration with MIS ecosystem
- Basic documentation

### Note
Version 1.0.0 was never released publicly as the project underwent a complete redesign based on insights from sequential thinking analysis, leading directly to version 2.0.0.

## [Unreleased]

### Planned
- Response caching for performance
- Streaming support for real-time feedback
- VS Code extension
- Additional provider support
- Custom template marketplace