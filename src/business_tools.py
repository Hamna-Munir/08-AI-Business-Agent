"""
business_tools.py
Day 51 + 53: the agent's internal business-data tools. Every function here
is read-only and returns plain dict/list data (JSON-serializable), so it can
be handed straight to the LLM as evidence, or exposed over MCP (see
mcp_server.py, which wraps these same functions for external MCP clients).
"""

from typing import List, Optional

from .database import get_connection


def _rows_to_dicts(rows) -> List[dict]:
    return [dict(r) for r in rows]


def get_sales_data(month: Optional[str] = None, region: Optional[str] = None) -> List[dict]:
    """Monthly revenue + units, optionally filtered by month ('2026-06') and/or region."""
    conn = get_connection()
    try:
        query = """
            SELECT strftime('%Y-%m', o.order_date) AS month,
                   o.region AS region,
                   SUM(s.revenue) AS revenue,
                   SUM(s.quantity) AS units,
                   COUNT(DISTINCT o.order_id) AS orders
            FROM sales s JOIN orders o ON s.order_id = o.order_id
            WHERE 1=1
        """
        params = []
        if month:
            query += " AND strftime('%Y-%m', o.order_date) = ?"
            params.append(month)
        if region:
            query += " AND o.region = ?"
            params.append(region)
        query += " GROUP BY month, region ORDER BY month, region"
        return _rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


def get_customer_data(region: Optional[str] = None, segment: Optional[str] = None) -> List[dict]:
    """Customer counts and basic profile breakdown, optionally filtered."""
    conn = get_connection()
    try:
        query = "SELECT region, segment, COUNT(*) AS customers FROM customers WHERE 1=1"
        params = []
        if region:
            query += " AND region = ?"
            params.append(region)
        if segment:
            query += " AND segment = ?"
            params.append(segment)
        query += " GROUP BY region, segment ORDER BY region, segment"
        return _rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


def get_customer_metrics(month: Optional[str] = None) -> List[dict]:
    """Revenue and order count per customer segment, optionally for one month."""
    conn = get_connection()
    try:
        query = """
            SELECT c.segment AS segment,
                   COUNT(DISTINCT o.order_id) AS orders,
                   SUM(s.revenue) AS revenue,
                   ROUND(SUM(s.revenue) * 1.0 / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
            FROM sales s
            JOIN orders o ON s.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE 1=1
        """
        params = []
        if month:
            query += " AND strftime('%Y-%m', o.order_date) = ?"
            params.append(month)
        query += " GROUP BY c.segment ORDER BY revenue DESC"
        return _rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


def get_product_data(category: Optional[str] = None) -> List[dict]:
    """The product catalog, optionally filtered by category."""
    conn = get_connection()
    try:
        query = "SELECT product_id, name, category, base_price FROM products WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        return _rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


def get_product_sales(product_name: Optional[str] = None, months: int = 6) -> List[dict]:
    """Month-by-month revenue, units, order count, and average unit price for
    a product (or all products if product_name is omitted). This is the key
    tool for spotting a price-driven vs. demand-driven revenue change."""
    conn = get_connection()
    try:
        query = """
            SELECT strftime('%Y-%m', o.order_date) AS month,
                   p.name AS product,
                   SUM(s.revenue) AS revenue,
                   SUM(s.quantity) AS units,
                   COUNT(DISTINCT o.order_id) AS orders,
                   ROUND(AVG(s.unit_price), 2) AS avg_unit_price
            FROM sales s
            JOIN orders o ON s.order_id = o.order_id
            JOIN products p ON s.product_id = p.product_id
            WHERE 1=1
        """
        params = []
        if product_name:
            query += " AND p.name LIKE ?"
            params.append(f"%{product_name}%")
        query += " GROUP BY month, p.name ORDER BY product, month"
        rows = _rows_to_dicts(conn.execute(query, params).fetchall())
        if months:
            # keep only the most recent `months` per product
            by_product: dict = {}
            for row in rows:
                by_product.setdefault(row["product"], []).append(row)
            trimmed = []
            for product_rows in by_product.values():
                trimmed.extend(product_rows[-months:])
            return trimmed
        return rows
    finally:
        conn.close()


def get_top_products(month: Optional[str] = None, limit: int = 5) -> List[dict]:
    """Top products by revenue, optionally for a specific month."""
    conn = get_connection()
    try:
        query = """
            SELECT p.name AS product, p.category AS category,
                   SUM(s.revenue) AS revenue, SUM(s.quantity) AS units
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            JOIN orders o ON s.order_id = o.order_id
            WHERE 1=1
        """
        params = []
        if month:
            query += " AND strftime('%Y-%m', o.order_date) = ?"
            params.append(month)
        query += " GROUP BY p.name, p.category ORDER BY revenue DESC LIMIT ?"
        params.append(limit)
        return _rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


def get_regional_trend(months: int = 6) -> List[dict]:
    """Revenue by region per month — for spotting 'which region is declining'."""
    conn = get_connection()
    try:
        query = """
            SELECT strftime('%Y-%m', o.order_date) AS month,
                   o.region AS region,
                   SUM(s.revenue) AS revenue,
                   COUNT(DISTINCT o.order_id) AS orders
            FROM sales s JOIN orders o ON s.order_id = o.order_id
            GROUP BY month, region ORDER BY region, month
        """
        rows = _rows_to_dicts(conn.execute(query).fetchall())
        if months:
            by_region: dict = {}
            for row in rows:
                by_region.setdefault(row["region"], []).append(row)
            trimmed = []
            for region_rows in by_region.values():
                trimmed.extend(region_rows[-months:])
            return trimmed
        return rows
    finally:
        conn.close()


def list_available_months() -> List[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT strftime('%Y-%m', order_date) AS month FROM orders ORDER BY month"
        ).fetchall()
        return [r["month"] for r in rows]
    finally:
        conn.close()


# Registry used by planner.py / mcp_server.py to look tools up by name.
TOOL_REGISTRY = {
    "get_sales_data": get_sales_data,
    "get_customer_data": get_customer_data,
    "get_customer_metrics": get_customer_metrics,
    "get_product_data": get_product_data,
    "get_product_sales": get_product_sales,
    "get_top_products": get_top_products,
    "get_regional_trend": get_regional_trend,
}
