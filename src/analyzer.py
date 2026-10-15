"""
analyzer.py
Turns raw tool results (lists of dicts from business_tools.py) into plain-
English findings with the specific numbers attached, so the LLM synthesizing
the final report has concrete, pre-computed evidence rather than having to
do arithmetic itself (which is where hallucinated numbers creep in).
"""

from typing import List, Optional


def pct_change(old: float, new: float) -> Optional[float]:
    if not old:
        return None
    return round((new - old) / old * 100, 1)


def analyze_product_trend(rows: List[dict]) -> List[str]:
    """rows: output of business_tools.get_product_sales() for one product,
    sorted by month. Returns findings like revenue/price/volume deltas
    between the last two months."""
    findings = []
    if len(rows) < 2:
        return findings

    prev, latest = rows[-2], rows[-1]
    product = latest["product"]

    rev_change = pct_change(prev["revenue"], latest["revenue"])
    unit_change = pct_change(prev["units"], latest["units"])
    order_change = pct_change(prev["orders"], latest["orders"])
    price_change = pct_change(prev["avg_unit_price"], latest["avg_unit_price"])

    if rev_change is not None:
        direction = "decreased" if rev_change < 0 else "increased"
        findings.append(
            f"{product} revenue {direction} {abs(rev_change)}% from {prev['month']} "
            f"(PKR {prev['revenue']:,.0f}) to {latest['month']} (PKR {latest['revenue']:,.0f})."
        )
    if order_change is not None and unit_change is not None:
        findings.append(
            f"{product} order count changed {order_change:+.1f}% and units sold changed "
            f"{unit_change:+.1f}% over the same period (orders: {prev['orders']} -> {latest['orders']}, "
            f"units: {prev['units']} -> {latest['units']})."
        )
    if price_change is not None:
        findings.append(
            f"{product} average unit price changed {price_change:+.1f}% "
            f"(PKR {prev['avg_unit_price']:,.0f} -> PKR {latest['avg_unit_price']:,.0f})."
        )

    # The key diagnostic: is this price-driven or demand-driven?
    if rev_change is not None and order_change is not None and price_change is not None:
        if rev_change < -5 and abs(order_change) < 10 and price_change < -10:
            findings.append(
                f"Because order volume stayed roughly stable ({order_change:+.1f}%) while "
                f"average price dropped {price_change:+.1f}%, the revenue decline in {product} "
                f"is price-driven, not demand-driven."
            )
        elif rev_change < -5 and order_change < -10:
            findings.append(
                f"Because order volume itself dropped {order_change:+.1f}%, the revenue decline "
                f"in {product} looks demand-driven rather than price-driven."
            )

    return findings


def analyze_regional_trend(rows: List[dict]) -> List[str]:
    """rows: output of business_tools.get_regional_trend(), all regions/months."""
    findings = []
    by_region: dict = {}
    for row in rows:
        by_region.setdefault(row["region"], []).append(row)

    for region, region_rows in by_region.items():
        region_rows.sort(key=lambda r: r["month"])
        if len(region_rows) < 2:
            continue
        prev, latest = region_rows[-2], region_rows[-1]
        change = pct_change(prev["revenue"], latest["revenue"])
        if change is not None and abs(change) >= 8:
            direction = "declined" if change < 0 else "grew"
            findings.append(
                f"{region} revenue {direction} {abs(change)}% from {prev['month']} "
                f"(PKR {prev['revenue']:,.0f}) to {latest['month']} (PKR {latest['revenue']:,.0f})."
            )
    return findings


def analyze_top_products(rows: List[dict]) -> List[str]:
    if not rows:
        return []
    lines = [f"{r['product']} ({r['category']}): PKR {r['revenue']:,.0f} from {r['units']} units" for r in rows]
    return ["Top products by revenue: " + "; ".join(lines)]


def analyze_customer_segments(rows: List[dict]) -> List[str]:
    if not rows:
        return []
    findings = []
    for r in rows:
        findings.append(
            f"{r['segment']} segment: PKR {r['revenue']:,.0f} revenue across {r['orders']} orders "
            f"(avg order value PKR {r['avg_order_value']:,.0f})."
        )
    return findings
