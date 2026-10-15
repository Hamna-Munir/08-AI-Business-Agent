"""
agent.py
Day 56: the complete Business Agent. Ties together classification (LLM),
planning (planner.py), tool execution (business_tools.py), analysis
(analyzer.py), optional external research (browser_tools.py), and report
synthesis (LLM) into one pipeline.

Pipeline:
    question -> classify -> plan -> run tools -> analyze -> (research?) ->
    synthesize report
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI

from . import analyzer, business_tools, config, planner
from .browser_tools import ResearchUnavailable, search_external_information
from .prompts import classification_system_prompt, report_system_prompt, research_query_prompt

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.OPENAI_API_KEY or "not-set", base_url=config.OPENAI_BASE_URL)
    return _client


def _chat_json(system_prompt: str, user_message: str) -> dict:
    response = _get_client().chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
        temperature=0,
        max_tokens=400,
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def _chat_text(system_prompt: str, user_message: str, max_tokens: int = 1200) -> str:
    response = _get_client().chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


@dataclass
class InvestigationTrace:
    """Everything gathered for one question — kept around so the UI can show
    its work, not just the final report (helps the eval/transparency goal)."""
    question: str
    classification: Dict[str, Any] = field(default_factory=dict)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    research: List[dict] = field(default_factory=list)
    research_note: str = ""
    report: str = ""


def classify_question(question: str) -> Dict[str, Any]:
    try:
        return _chat_json(classification_system_prompt(), question)
    except (json.JSONDecodeError, Exception):
        return {
            "category": "general",
            "task": "General business analysis",
            "required_data": ["sales_data"],
            "needs_external_research": False,
            "is_multi_step": False,
        }


def run_tools(plan: List[planner.PlanStep]) -> List[Dict[str, Any]]:
    results = []
    for step in plan:
        try:
            # Resolve the function on business_tools by name at call time
            # (rather than using step.tool_fn's captured reference) so this
            # always calls whatever is currently bound there.
            fn = getattr(business_tools, step.tool_name)
            data = fn(**step.kwargs)
        except Exception as e:  # a tool failing shouldn't crash the whole report
            data = {"error": str(e)}
        results.append({"tool": step.tool_name, "label": step.label, "kwargs": step.kwargs, "data": data})
    return results


def analyze_results(tool_calls: List[Dict[str, Any]]) -> List[str]:
    findings: List[str] = []
    for call in tool_calls:
        data = call["data"]
        if isinstance(data, dict) and "error" in data:
            continue
        if call["tool"] == "get_product_sales" and data:
            by_product: Dict[str, list] = {}
            for row in data:
                by_product.setdefault(row["product"], []).append(row)
            for rows in by_product.values():
                rows.sort(key=lambda r: r["month"])
                findings.extend(analyzer.analyze_product_trend(rows))
        elif call["tool"] == "get_regional_trend" and data:
            findings.extend(analyzer.analyze_regional_trend(data))
        elif call["tool"] == "get_top_products" and data:
            findings.extend(analyzer.analyze_top_products(data))
        elif call["tool"] == "get_customer_metrics" and data:
            findings.extend(analyzer.analyze_customer_segments(data))
    return findings


def maybe_research(question: str, findings: List[str], needs_research: bool):
    if not needs_research:
        return [], ""
    try:
        summary = " ".join(findings[:4]) or "No strong internal pattern found yet."
        query = _chat_text(
            "You write short, precise web search queries. Return ONLY the query text.",
            research_query_prompt(question, summary),
            max_tokens=40,
        )
        results = search_external_information(query)
        return results, ""
    except ResearchUnavailable as e:
        return [], str(e)


def synthesize_report(question: str, findings: List[str], research: List[dict], research_note: str) -> str:
    if not findings and not research:
        return (
            f"## Executive Summary\n{config.INSUFFICIENT_EVIDENCE_MESSAGE}\n\n"
            "## Confidence & Limitations\nNo matching data was found in the business database for this question."
        )

    evidence_lines = [f"- {f}" for f in findings]
    if research:
        evidence_lines.append("\nExternal research findings:")
        for r in research:
            evidence_lines.append(f"- [{r['source']}] {r['title']}: {r['snippet'][:200]} ({r['url']})")
    elif research_note:
        evidence_lines.append(f"\nExternal research was requested but unavailable: {research_note}")

    evidence_text = "\n".join(evidence_lines)
    user_message = f"Business question: {question}\n\nEvidence gathered:\n{evidence_text}"
    return _chat_text(report_system_prompt(), user_message, max_tokens=1200)


class BusinessAgent:
    """One call per question — stateless between questions (unlike the
    multi-turn MeetingAgent from Week 7), since a business investigation is
    naturally a single request/response rather than an ongoing dialogue."""

    def investigate(self, question: str) -> InvestigationTrace:
        trace = InvestigationTrace(question=question)

        trace.classification = classify_question(question)
        plan = planner.build_plan(question, trace.classification)
        trace.tool_calls = run_tools(plan)
        trace.findings = analyze_results(trace.tool_calls)

        trace.research, trace.research_note = maybe_research(
            question, trace.findings, trace.classification.get("needs_external_research", False)
        )

        trace.report = synthesize_report(question, trace.findings, trace.research, trace.research_note)
        return trace
