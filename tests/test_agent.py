"""
test_agent.py
End-to-end tests for BusinessAgent.investigate(), with the LLM calls mocked
out (classification + report synthesis) so the test suite needs no API key
and no network access — only the real database and real planning/analysis
logic are exercised.
"""

from unittest.mock import patch

import pytest

from src.agent import BusinessAgent
from src.database import build_database


@pytest.fixture(autouse=True, scope="module")
def ensure_db():
    build_database()


SALES_CLASSIFICATION = {
    "category": "sales",
    "task": "Revenue Decline Analysis",
    "required_data": ["sales_data", "product_data"],
    "needs_external_research": False,
    "is_multi_step": True,
}


@patch("src.agent.classify_question", return_value=SALES_CLASSIFICATION)
@patch("src.agent._chat_text", return_value="## Executive Summary\nMocked report.")
def test_revenue_decline_question_surfaces_the_real_cause(mock_text, mock_classify):
    agent = BusinessAgent()
    trace = agent.investigate("Why did our revenue drop this month?")

    assert trace.tool_calls, "should have made at least one tool call"
    joined_findings = " ".join(trace.findings)
    assert "UrbanTote Backpack" in joined_findings
    assert "price-driven" in joined_findings
    assert trace.report  # report was produced


@patch(
    "src.agent.classify_question",
    return_value={"category": "general", "task": "n/a", "required_data": [], "needs_external_research": False, "is_multi_step": False},
)
def test_question_with_no_matching_data_reports_insufficient_evidence(mock_classify):
    # Force the planner/analyzer path to produce no findings by patching run_tools
    # to return only error results.
    with patch("src.agent.run_tools", return_value=[{"tool": "x", "label": "x", "kwargs": {}, "data": {"error": "boom"}}]):
        agent = BusinessAgent()
        trace = agent.investigate("What is the airspeed velocity of an unladen swallow?")

    assert "Insufficient evidence" in trace.report


@patch("src.agent.classify_question", return_value=SALES_CLASSIFICATION)
@patch("src.agent._chat_text", return_value="## Executive Summary\nMocked report.")
def test_tool_failure_does_not_crash_the_pipeline(mock_text, mock_classify):
    with patch("src.business_tools.get_sales_data", side_effect=RuntimeError("db locked")):
        agent = BusinessAgent()
        trace = agent.investigate("Why did our revenue drop this month?")

    failed = [c for c in trace.tool_calls if c["tool"] == "get_sales_data"]
    assert failed and "error" in failed[0]["data"]
    assert trace.report  # pipeline still completed


@patch("src.agent.classify_question", return_value={**SALES_CLASSIFICATION, "needs_external_research": True})
@patch("src.agent._chat_text", side_effect=["pricing discount trend 2026", "## Executive Summary\nMocked."])
def test_research_unavailable_is_noted_not_hidden(mock_text, mock_classify):
    agent = BusinessAgent()
    trace = agent.investigate("Why did our revenue drop, and are there external pricing trends?")

    assert trace.research == []
    assert "TAVILY_API_KEY" in trace.research_note
