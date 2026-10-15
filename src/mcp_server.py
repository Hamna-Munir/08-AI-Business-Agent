"""
mcp_server.py
Day 52: a real MCP (Model Context Protocol) server exposing the business
data tools, built with the official `mcp` Python SDK's FastMCP helper.

This is runnable standalone and connectable from any MCP client (Claude
Desktop, Claude Code, the MCP Inspector, etc.):

    python -m src.mcp_server

The Streamlit agent in this project (agent.py / planner.py) calls the same
underlying functions in business_tools.py directly, in-process, for its own
reasoning loop — that's a deliberate simplicity choice for a single-process
Streamlit app, not a limitation of the tools themselves. This file is what
demonstrates the Day 52 MCP skill: the exact same business logic, exposed
over the standard protocol for *external* MCP clients to use too.

Built on `mcp` v2's `MCPServer` (the renamed successor to the earlier
`FastMCP` helper — same `.tool()` / `.run()` shape, new import path).
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from . import business_tools

mcp = MCPServer("business-data")


@mcp.tool()
def get_sales_data(month: Optional[str] = None, region: Optional[str] = None) -> list:
    """Monthly revenue, units, and order count. Filter by month ('2026-06') and/or region."""
    return business_tools.get_sales_data(month=month, region=region)


@mcp.tool()
def get_customer_data(region: Optional[str] = None, segment: Optional[str] = None) -> list:
    """Customer counts by region and segment (Retail/Wholesale)."""
    return business_tools.get_customer_data(region=region, segment=segment)


@mcp.tool()
def get_customer_metrics(month: Optional[str] = None) -> list:
    """Revenue, order count, and average order value per customer segment."""
    return business_tools.get_customer_metrics(month=month)


@mcp.tool()
def get_product_data(category: Optional[str] = None) -> list:
    """The product catalog, optionally filtered by category."""
    return business_tools.get_product_data(category=category)


@mcp.tool()
def get_product_sales(product_name: Optional[str] = None, months: int = 6) -> list:
    """Month-by-month revenue, units, orders, and average unit price for a product
    (or all products). Use this to tell a price-driven decline from a demand-driven one."""
    return business_tools.get_product_sales(product_name=product_name, months=months)


@mcp.tool()
def get_top_products(month: Optional[str] = None, limit: int = 5) -> list:
    """Top products by revenue, optionally for one month."""
    return business_tools.get_top_products(month=month, limit=limit)


@mcp.tool()
def get_regional_trend(months: int = 6) -> list:
    """Revenue and order count by region, month by month."""
    return business_tools.get_regional_trend(months=months)


if __name__ == "__main__":
    mcp.run()
