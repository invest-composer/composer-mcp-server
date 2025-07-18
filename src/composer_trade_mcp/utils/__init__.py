"""
Utility functions for Composer MCP Server.
"""

from .parsers import parse_stats, parse_dvm_capital, parse_backtest_output, epoch_to_date, epoch_ms_to_date
from .auth import get_optional_headers, get_required_headers, get_mcp_environment

__all__ = [
    "parse_stats",
    "parse_dvm_capital", 
    "parse_backtest_output",
    "epoch_to_date",
    "epoch_ms_to_date",
    "get_optional_headers",
    "get_required_headers",
    "get_mcp_environment"
]

def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to a maximum length.
    """
    return text[:max_length]
