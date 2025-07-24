"""
VIBEZEN External System Integration.

This module provides integration with external AI assistance systems:
- zen-MCP: AI model command execution and analysis
- o3-search: Advanced search and best practice collection
- MIS: Memory Integration System for persistent knowledge
"""

from vibezen.external.zen_mcp import (
    ZenMCPClient,
    ZenMCPConfig,
    ZenMCPIntegration,
    ZenMCPError,
)

from vibezen.external.o3_search import (
    O3SearchClient,
    O3SearchConfig,
    O3SearchIntegration,
    O3SearchError,
)

from vibezen.external.mis_integration import (
    MISClient,
    MISConfig,
    MISIntegration,
    MISError,
)

__all__ = [
    # zen-MCP
    "ZenMCPClient",
    "ZenMCPConfig",
    "ZenMCPIntegration",
    "ZenMCPError",
    # o3-search
    "O3SearchClient",
    "O3SearchConfig",
    "O3SearchIntegration",
    "O3SearchError",
    # MIS
    "MISClient",
    "MISConfig",
    "MISIntegration",
    "MISError",
]