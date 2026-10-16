"""
test_analysis.py
Tests analyzer.py's finding-generation against known inputs — including the
exact price-vs-demand diagnostic that's the point of the Day 56 demo.
"""

from src import analyzer


def test_price_driven_decline_is_flagged():
    rows = [
        {"month": "2026-05", "product": "Widget", "revenue": 10000, "units": 100, "orders": 20, "avg_unit_price": 100},
        {"month": "2026-06", "product": "Widget", "revenue": 6800, "units": 97, "orders": 19, "avg_unit_price": 70},
    ]
    findings = analyzer.analyze_product_trend(rows)
    joined = " ".join(findings)
    assert "price-driven" in joined
    assert "Widget" in joined


def test_demand_driven_decline_is_flagged():
    rows = [
        {"month": "2026-05", "product": "Gadget", "revenue": 10000, "units": 100, "orders": 20, "avg_unit_price": 100},
        {"month": "2026-06", "product": "Gadget", "revenue": 6000, "units": 60, "orders": 12, "avg_unit_price": 100},
    ]
    findings = analyzer.analyze_product_trend(rows)
    joined = " ".join(findings)
    assert "demand-driven" in joined


def test_stable_product_produces_no_false_diagnosis():
    rows = [
        {"month": "2026-05", "product": "Steady", "revenue": 10000, "units": 100, "orders": 20, "avg_unit_price": 100},
        {"month": "2026-06", "product": "Steady", "revenue": 10200, "units": 101, "orders": 20, "avg_unit_price": 101},
    ]
    findings = analyzer.analyze_product_trend(rows)
    joined = " ".join(findings)
    assert "price-driven" not in joined
    assert "demand-driven" not in joined


def test_regional_trend_flags_only_significant_moves():
    rows = [
        {"month": "2026-05", "region": "Sindh", "revenue": 10000, "orders": 10},
        {"month": "2026-06", "region": "Sindh", "revenue": 9900, "orders": 10},   # <1% — not significant
        {"month": "2026-05", "region": "Punjab", "revenue": 10000, "orders": 10},
        {"month": "2026-06", "region": "Punjab", "revenue": 7000, "orders": 9},   # -30% — significant
    ]
    findings = analyzer.analyze_regional_trend(rows)
    joined = " ".join(findings)
    assert "Sindh" not in joined
    assert "Punjab" in joined


def test_empty_input_returns_no_findings():
    assert analyzer.analyze_product_trend([]) == []
    assert analyzer.analyze_regional_trend([]) == []
    assert analyzer.analyze_top_products([]) == []
    assert analyzer.analyze_customer_segments([]) == []
