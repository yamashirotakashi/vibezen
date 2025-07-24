"""
zen-MCP Integration for VIBEZEN.

Provides integration with zen-MCP for:
- Code review and analysis (codeview)
- Challenge mode for critical thinking (challenge)
- Deep thinking and analysis (thinkdeep)
- Consensus building across models (consensus)
"""

from vibezen.external.zen_mcp.client import ZenMCPClient
from vibezen.external.zen_mcp.config import ZenMCPConfig
from vibezen.external.zen_mcp.integration import ZenMCPIntegration
from vibezen.external.zen_mcp.exceptions import ZenMCPError

__all__ = [
    "ZenMCPClient",
    "ZenMCPConfig",
    "ZenMCPIntegration",
    "ZenMCPError",
]