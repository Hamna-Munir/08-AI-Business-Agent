# Journal — Week 8: AI Business Agent

A running log across Days 50–56. Daily technical breakdowns live in
`notes/day-XX.md`; this file is the higher-level narrative.

- **Day 50**: Spent most of today on the conceptual gap between a chatbot
  and an agent that takes a business question and decides what to go check.
  The classifier feels small but it's the first real "decision" the system
  makes.
- **Day 51**: Realized partway through that random synthetic data is
  useless for this project specifically — if nothing in the data actually
  changed, every "why did X happen" question has no real answer to find.
  Went back and deliberately engineered one product's price history so
  Day 56's demo question has a genuine, discoverable story.
- **Day 52**: MCP day. Hit a real version-mismatch error immediately —
  `FastMCP` doesn't exist anymore in the `mcp` package I had installed; it's
  `MCPServer` now. Logged it in day-52 notes since it'll trip up anyone
  following an older MCP tutorial.
- **Day 53**: Database modeling day — splitting `orders` from `sales` (line
  items) instead of one flat table felt like overkill at first, but it's
  exactly what makes "order volume vs. revenue" analysis possible later.
- **Day 54**: Spent real time on what "graceful fallback" should mean for
  the external research tool — decided a silent empty list was worse than
  an explicit "not configured" the report can mention honestly.
- **Day 55**: Kept the planner LLM-free on purpose. Tool selection should
  be fast, predictable, and testable; the judgment calls belong in
  classification and report-writing, not here.
- **Day 56**: Everything came together today. The UrbanTote finding came
  out of the full pipeline exactly matching the roadmap's own worked
  example — satisfying to see the engineered data pay off.

## Why this is a strong portfolio project

This is the first project in the roadmap that genuinely plans before
acting: it decides which data it needs, gathers evidence from a real
database (and optionally a real MCP server + external search), and is
explicitly designed to say "insufficient evidence" rather than invent a
plausible-sounding business explanation. That restraint is the actual
skill being demonstrated.
