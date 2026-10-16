# Week 8 Summary — AI Business Agent

## Goal
Build an agent that answers real business questions by inspecting actual
business data (SQLite, seeded from synthetic but realistic CSVs), using
tools (including a real MCP server) to gather evidence, analyzing that
evidence in plain Python, and producing a structured, grounded report —
never inventing numbers, and saying "insufficient evidence" when the data
doesn't support a conclusion.

## What was built

| Day | Focus | Output |
|-----|-------|--------|
| 50 | Business agent fundamentals | Question classifier (category + task + required data) |
| 51 | Business data + structured analysis | Synthetic `customers/products/orders/sales` CSVs, Pydantic-free but schema-consistent tables |
| 52 | MCP + tool fundamentals | `mcp_server.py` — real MCP server (official `mcp` SDK, `MCPServer`/`.tool()`) exposing 7 business tools |
| 53 | Database + business tools | `database.py` (SQLite build), `business_tools.py` (7 query functions) |
| 54 | Browser + file tools | `browser_tools.py` (Tavily search, graceful no-key fallback), `file_tools.py` (sandboxed file reads) |
| 55 | Agent planning | `planner.py` — maps a classified question + extracted entities (month/region/product) to a concrete tool-call plan |
| 56 | Complete agent + evaluation | `agent.py` (`BusinessAgent.investigate()`), `analyzer.py`, `tests/`, `evaluation/evaluation.csv` |

## Architecture

```
Business question
   │
   ▼
classify_question()         LLM: category, task, required_data, needs_research?
   │
   ▼
planner.build_plan()         entity extraction (month/region/product) + tool selection
   │
   ▼
run_tools()                  calls business_tools.* (same functions MCP exposes)
   │
   ▼
analyze_results()            analyzer.py turns raw rows into cited, numeric findings
   │
   ▼
maybe_research()             optional: browser_tools external search, if requested
   │
   ▼
synthesize_report()          LLM writes the structured report FROM the findings only
```

## Key decisions

- **The analysis arithmetic happens in Python, not the LLM.** `analyzer.py`
  computes percentage changes and the price-driven-vs-demand-driven
  diagnosis directly from the SQL results. The LLM only writes prose around
  numbers it's handed — this is what keeps the report from hallucinating
  figures.
- **A real MCP server, used honestly.** `mcp_server.py` exposes the same
  `business_tools` functions over the actual MCP protocol (`mcp` SDK v2,
  `MCPServer`) so any MCP client (Claude Desktop, Claude Code, MCP
  Inspector) can query this business data too. The in-app Streamlit agent
  calls the same underlying functions in-process for its own reasoning
  loop — a deliberate simplicity choice for a single-process app, not a
  gap in the MCP implementation.
- **The dataset has a real, discoverable story in it.** One product
  (UrbanTote Backpack) has an engineered June price cut: order volume and
  units stay roughly flat while average price drops ~31%, so "why did
  revenue drop?" has a genuine, non-obvious, data-grounded answer — a
  price-driven decline, not a demand-driven one — matching the roadmap's
  own worked example almost exactly.
- **External research is opt-in and honestly labelled.** `browser_tools.py`
  only fires when the classifier flags `needs_external_research`, and if no
  `TAVILY_API_KEY` is configured it returns a clear "not configured" signal
  that the report explicitly notes, rather than silently proceeding without
  it or inventing external causes.

## Known limitations / next steps
- Entity extraction (month/region/product) in `planner.py` is regex/keyword
  based, not LLM-based — good enough for this dataset's vocabulary, but
  would need a proper NER step for messier real-world phrasing.
- `BusinessAgent` is stateless per question (no multi-turn follow-up memory,
  unlike Week 7's `MeetingAgent`) — a deliberate scope choice since a
  business investigation is naturally single-shot, but a "drill into this
  finding" follow-up mode would be a good extension.
- The synthetic dataset covers 6 months (Jan–Jun 2026) and 4 Pakistani
  regions; real deployment would point `database.py` at a real warehouse or
  CSV export instead of synthetic generation.
