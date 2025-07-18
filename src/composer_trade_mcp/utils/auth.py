"""
Authentication utilities for Composer MCP Server.
"""

from fastmcp.server.dependencies import get_http_headers
from typing import Dict

def get_mcp_environment() -> str:
    """
    Get the environment of the MCP server.
    """
    headers = get_http_headers()
    return headers.get("x-composer-mcp-environment", "prod")

def get_optional_headers() -> Dict[str, str]:
    """
    Get headers for optional authentication (read-only operations).
    Always includes x-origin. Only includes API key and secret if both are present.
    """
    headers = get_http_headers()
    headers["x-origin"] = "public-api"
    api_key = headers.get("x-api-key-id")
    secret_key = headers.get("authorization")
    if api_key and secret_key:
        return headers
    else:
        return {"x-origin": "public-api"}


def get_required_headers() -> Dict[str, str]:
    """
    Get headers for required authentication (write operations).
    Requires both API key and secret key to be present.
    """
    headers = get_http_headers()
    headers["x-origin"] = "public-api"
    api_key = headers.get("x-api-key-id")
    secret_key = headers.get("authorization")

    if not api_key:
        raise ValueError("X-Api-Key-Id header is required but not set")
    if not secret_key:
        raise ValueError("Authorization header is required but not set")

    return headers
