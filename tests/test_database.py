"""
test_database.py
Verifies the synthetic dataset builds correctly and the engineered June
price-decline pattern (used as the Day 56 demo question) is actually there.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from src import config, database


@pytest.fixture
def temp_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        monkeypatch.setattr(config, "DATA_DIR", tmp_dir)
        monkeypatch.setattr(config, "DB_PATH", tmp_dir / "business.db")
        monkeypatch.setattr(config, "CUSTOMERS_CSV", tmp_dir / "customers.csv")
        monkeypatch.setattr(config, "PRODUCTS_CSV", tmp_dir / "products.csv")
        monkeypatch.setattr(config, "ORDERS_CSV", tmp_dir / "orders.csv")
        monkeypatch.setattr(config, "SALES_CSV", tmp_dir / "sales.csv")
        database.build_database(force=True)
        yield tmp_dir


def test_tables_populated(temp_db):
    conn = database.get_connection()
    for table in ("customers", "products", "orders", "sales"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count > 0, f"{table} should not be empty"
    conn.close()


def test_urbantote_june_price_decline(temp_db):
    conn = database.get_connection()
    rows = conn.execute(
        """
        SELECT strftime('%Y-%m', o.order_date) AS month,
               COUNT(DISTINCT o.order_id) AS orders,
               SUM(s.quantity) AS units,
               AVG(s.unit_price) AS avg_price
        FROM sales s JOIN orders o ON s.order_id = o.order_id
        WHERE s.product_id = 1
        GROUP BY month ORDER BY month
        """
    ).fetchall()
    conn.close()

    by_month = {r["month"]: dict(r) for r in rows}
    may, june = by_month["2026-05"], by_month["2026-06"]

    # Order volume should stay roughly stable...
    assert abs(june["orders"] - may["orders"]) <= 3
    # ...while price drops noticeably (the engineered anomaly).
    assert june["avg_price"] < may["avg_price"] * 0.85


def test_rebuild_is_idempotent(temp_db):
    conn = database.get_connection()
    before = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()

    database.build_database(force=False)  # should no-op since db already exists

    conn = database.get_connection()
    after = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    assert before == after
