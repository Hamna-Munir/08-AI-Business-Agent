"""
planner.py
Day 55: decides WHICH tools to call and with WHAT arguments, given a
classified business question. Pure logic, no LLM calls here — this is the
"task decomposition + tool selection" layer; agent.py (Day 56) is what adds
the LLM reasoning on top of what this returns.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from . import business_tools, config

MONTH_NAMES = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


@dataclass
class PlanStep:
    tool_name: str
    tool_fn: Callable
    kwargs: Dict[str, Any] = field(default_factory=dict)
    label: str = ""


def _extract_month(question: str) -> Optional[str]:
    available = business_tools.list_available_months()
    if not available:
        return None

    lowered = question.lower()
    for name, mm in MONTH_NAMES.items():
        if name in lowered:
            for month in available:
                if month.endswith(f"-{mm}"):
                    return month

    if "this month" in lowered or "latest" in lowered or "current month" in lowered:
        return available[-1]
    if "last month" in lowered or "previous month" in lowered:
        return available[-2] if len(available) > 1 else available[-1]

    return None


def _extract_region(question: str) -> Optional[str]:
    lowered = question.lower()
    for region in ("Punjab", "Sindh", "KPK", "Balochistan"):
        if region.lower() in lowered:
            return region
    return None


def _extract_product(question: str) -> Optional[str]:
    lowered = question.lower()
    products = business_tools.get_product_data()
    for product in products:
        name = product["name"]
        # match on the full name or its first word (e.g. "UrbanTote")
        if name.lower() in lowered or name.split()[0].lower() in lowered:
            return name
    return None


def extract_entities(question: str) -> Dict[str, Optional[str]]:
    return {
        "month": _extract_month(question),
        "region": _extract_region(question),
        "product": _extract_product(question),
    }


def build_plan(question: str, classification: Dict[str, Any]) -> List[PlanStep]:
    """Maps the classifier's `required_data` list + extracted entities onto
    concrete business_tools calls."""
    entities = extract_entities(question)
    required = set(classification.get("required_data", []) or [])
    category = classification.get("category", "general")
    steps: List[PlanStep] = []

    def add(tool_name: str, label: str, **kwargs):
        clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        steps.append(PlanStep(tool_name, business_tools.TOOL_REGISTRY[tool_name], clean_kwargs, label))

    needs_sales = bool(required & {"sales_data", "revenue", "sales"}) or category in ("sales", "finance")
    needs_products = bool(required & {"product_data", "products"}) or category in ("sales", "inventory")
    needs_customers = bool(required & {"customer_data", "customers"}) or category == "customers"

    if needs_sales:
        add("get_sales_data", "Overall sales figures", month=entities["month"], region=entities["region"])
        add("get_regional_trend", "Revenue trend by region")

    if entities["product"] or "product_performance" in required or needs_products:
        add(
            "get_product_sales",
            f"Monthly trend for {entities['product']}" if entities["product"] else "Monthly trend, all products",
            product_name=entities["product"],
        )
        add("get_top_products", "Top products by revenue", month=entities["month"])

    if needs_customers:
        add("get_customer_metrics", "Revenue by customer segment", month=entities["month"])
        add("get_customer_data", "Customer counts", region=entities["region"])

    # Fallback: if nothing matched (vague/general question), still ground the
    # agent in *something* real rather than answering from nothing.
    if not steps:
        add("get_sales_data", "Overall sales figures (fallback)", month=entities["month"])
        add("get_top_products", "Top products by revenue (fallback)", month=entities["month"])

    return steps[: config.MAX_TOOL_CALLS_PER_QUESTION]
