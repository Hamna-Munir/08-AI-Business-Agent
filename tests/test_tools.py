"""
test_tools.py
Tests business_tools.py query functions against the real (committed) sample
database, and file_tools.py's path-safety guard.
"""

import pytest

from src import business_tools, file_tools
from src.database import build_database


@pytest.fixture(autouse=True, scope="module")
def ensure_db():
    build_database()


def test_get_top_products_returns_ranked_results():
    results = business_tools.get_top_products(month="2026-06", limit=3)
    assert len(results) <= 3
    revenues = [r["revenue"] for r in results]
    assert revenues == sorted(revenues, reverse=True)


def test_get_product_sales_filters_by_name():
    results = business_tools.get_product_sales(product_name="UrbanTote", months=6)
    assert all("UrbanTote" in r["product"] for r in results)
    assert len(results) > 0


def test_get_sales_data_filters_by_month():
    results = business_tools.get_sales_data(month="2026-06")
    assert all(r["month"] == "2026-06" for r in results)


def test_get_regional_trend_covers_all_regions():
    results = business_tools.get_regional_trend()
    regions = {r["region"] for r in results}
    assert regions == {"Punjab", "Sindh", "KPK", "Balochistan"}


def test_tool_registry_matches_functions():
    for name, fn in business_tools.TOOL_REGISTRY.items():
        assert callable(fn)
        assert fn.__name__ == name


def test_file_tools_blocks_path_traversal():
    with pytest.raises(file_tools.FileAccessError):
        file_tools.read_business_file("../../etc/passwd")


def test_file_tools_reads_allowed_file():
    content = file_tools.read_business_file("docs/week-08-summary.md")
    assert len(content) > 0


def test_file_tools_lists_only_allowed_dirs():
    files = file_tools.list_business_files()
    assert all(f.startswith(("data/", "docs/", "notes/")) for f in files)
