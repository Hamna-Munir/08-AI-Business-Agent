"""
test_mcp.py
Verifies the MCP server registers all expected tools and that calling one
through the MCP server returns the same data as calling business_tools
directly (i.e. the MCP wrapper isn't silently diverging from the real logic).
"""

import asyncio
import json

import pytest

from src import business_tools
from src.database import build_database
from src.mcp_server import mcp


@pytest.fixture(autouse=True, scope="module")
def ensure_db():
    build_database()


def test_all_tools_registered():
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == set(business_tools.TOOL_REGISTRY.keys())


def test_mcp_tool_call_matches_direct_call():
    direct = business_tools.get_top_products(month="2026-06", limit=3)

    result = asyncio.run(mcp.call_tool("get_top_products", {"month": "2026-06", "limit": 3}))
    assert result.is_error is False

    # Each row comes back as one TextContent block of JSON.
    via_mcp = [json.loads(block.text) for block in result.content]

    assert via_mcp == direct
