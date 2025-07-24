"""
zen-MCP exceptions.
"""


class ZenMCPError(Exception):
    """Base exception for zen-MCP integration."""
    pass


class ZenMCPConnectionError(ZenMCPError):
    """Error connecting to zen-MCP."""
    pass


class ZenMCPTimeoutError(ZenMCPError):
    """zen-MCP operation timed out."""
    pass


class ZenMCPResponseError(ZenMCPError):
    """Invalid response from zen-MCP."""
    pass