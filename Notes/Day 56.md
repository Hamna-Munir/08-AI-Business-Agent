# Day 56 — Complete Business Agent

**Objective:** Combine every Week 8 piece into one working Business Agent, evaluate it, and plan deployment.

---

## 📖 Theory

### Final architecture

```
                  USER
                    ↓
             BUSINESS AGENT          (agent.py)
                    ↓
              Task Planning          (prompts.py classify + planner.py)
                    ↓
              Tool Selection
                    ↓
        ┌───────────┼────────────┐
        ↓           ↓            ↓
   Business tools  Database    Browser/File
   (+ MCP server)  (SQLite)    (Tavily / sandboxed files)
        └───────────┼────────────┘
                    ↓
             Evidence / Data
                    ↓
                Analysis             (analyzer.py)
                    ↓
          Business Recommendations
                    ↓
             Structured Report
```

### The pipeline in code

`BusinessAgent.investigate(question)` in `agent.py`:

| Step | Function | Uses LLM? |
|---|---|---|
| 1. Classify | `classify_question` | Yes (falls back to "general" if it fails) |
| 2. Plan | `planner.build_plan` | No |
| 3. Run tools | `run_tools` | No (a failing tool becomes an error entry) |
| 4. Analyze | `analyze_results` → `analyzer.py` | No |
| 5. Research (optional) | `maybe_research` | Yes, to write the search query |
| 6. Write report | `synthesize_report` | Yes |

All numbers are computed in steps 3 and 4. The LLM only writes prose around them, which is what keeps the report from inventing figures.

### The report structure

The prompt forces these sections, in order: **Executive Summary, Key Findings, Evidence, Likely Causes, Business Impact, Recommendations, Confidence & Limitations.**

### Recommendations must be specific

Generic: "Improve marketing."

Specific and tied to a finding: *"UrbanTote Backpack revenue fell 35.7% while its order count stayed at 17 and its average price fell 31.2%. The decline is price-driven, not demand-driven. Review the June discount before increasing acquisition spend."*

(That sentence is an example of the expected quality, built from this project's real numbers. I have not generated it with a live LLM, see "Status" below.)

### Challenge the question's premise

A good analyst checks whether the question is even true. In this dataset **total revenue rose 7.6% from May to June** (PKR 862,971 → 928,630), so "Why did our revenue drop?" has a false premise at company level. The decline is local:

| Finding (real, from the database) | Value |
|---|---|
| Total revenue, May → June | +7.6% |
| KPK revenue | −12.8% |
| Punjab / Balochistan revenue | +23.4% / +24.8% |
| UrbanTote Backpack | revenue −35.7%, orders flat (17 → 17), price −31.2% → **price-driven** |
| AeroFit Running Shoes | orders −33.3% → **demand-driven** |
| PixelBeam LED Lamp | orders −26.7% → **demand-driven** |

This was a real gap found while writing this note: the agent originally computed no overall total, so the LLM could have accepted the false premise. Fixed with `analyzer.analyze_overall_trend()` (new finding at the top of the list), a prompt rule to state a contradicted premise first, and a regression test.

### Evaluation

Test at least 15 questions across: sales, customers, operations, research, multi-step, and impossible/insufficient. Metrics:

| Metric | What is checked | How in this project |
|---|---|---|
| Intent | Question understood | Read `classification` in the trace |
| Tool selection | Right tool chosen | Compare `tool_calls` with the expected tools |
| Data accuracy | Numbers correct | Compare with a direct SQL query |
| Planning | Problem broken down well | Read the plan in the trace |
| Evidence | Conclusions supported | Every claim traces to a finding |
| Hallucination | Invented facts | Look for any number not in the findings |
| Recommendations | Actionable | Tied to a specific finding |
| Error handling | Fails gracefully | Mock-tested in `test_agent.py` |
| MCP | MCP tools work | `test_mcp.py` (automated) |
| Multi-tool | Combines tools | Plan contains several tools |

### Deployment

Deployment waits until the end of the phase, as planned. For when that time comes, this project is easier to deploy than Week 7: there is no OAuth and no personal secret, and the sample data is committed.

Checklist for later:

- Every package the app imports must be in `requirements.txt` (Week 7's `dateparser` failure was exactly this).
- `OPENAI_API_KEY` goes in the host's secrets, never in the repo. Check the host's docs for how secrets reach `os.getenv`.
- A public app spends your LLM quota. Consider a rate limit or a password.
- `mcp` is only needed for `mcp_server.py`; `app.py` does not import it. I have not tested installing it on the host's Python version.

---

## 💻 Coding Exercise

Run the whole agent and read its trace:

```python
from src.agent import BusinessAgent

trace = BusinessAgent().investigate("Why did our revenue drop this month?")
print(trace.classification)
print([c["tool"] for c in trace.tool_calls])
for f in trace.findings[:6]:
    print("-", f)
print(trace.report)
```

Or run the UI:

```bash
streamlit run src/app.py
```

---

## 🛠 Mini Project

**Final demo.** Ask: *"Our revenue dropped this month. Find the likely reasons and recommend what we should do."*

What a correct answer contains:

1. States that total revenue actually rose 7.6%, so the decline is local.
2. Names the locally declining parts: KPK (−12.8%), UrbanTote (price-driven), AeroFit and PixelBeam (demand-driven).
3. Recommends different actions for price-driven vs demand-driven declines.
4. Lists limitations (no cost or profit data, one month compared, no customer-level data used).

Then run the evaluation: go through `evaluation/evaluation.csv` (17 rows), fill in `result` (PASS/FAIL) and `notes`.

---

## 🧠 Quiz

1. Why are the percentages computed in `analyzer.py` and not by the LLM?
2. The question says revenue dropped, but the data shows it rose. What should the agent do?
3. What is the difference between a price-driven and a demand-driven decline, and why do they need different recommendations?
4. Which "insufficient evidence" cases are guaranteed by code, and which only by the prompt?

*(Try answering from memory first, then check the theory section above.)*

---

## 🐞 Common Errors

| Error | Likely Cause | Fix |
|---|---|---|
| Report accepts a false premise | No overall-total finding existed | Fixed: `analyze_overall_trend` + prompt rule + test |
| Generic recommendations | Report not tied to findings | Keep the prompt rule: each recommendation references a finding |
| LLM quotes a number not in the evidence | Evidence too thin or prompt too loose | Check against `trace.findings`; tighten the prompt |
| Off-topic question gets a business report | Fallback tools return real rows | Known limitation (Day 55); add a relevance check |
| `evaluation.csv` opens with shifted columns | Unquoted commas in a field | Fixed: file rewritten with proper quoting, 7 columns per row |
| App fails on a new machine | Missing dependency in `requirements.txt` | List every import; reinstall in a clean venv to test |

---

## ✅ Checklist

- [ ] Full pipeline runs end to end (`investigate`)
- [ ] UI runs (`streamlit run src/app.py`)
- [ ] All tests pass (`pytest`, currently 36)
- [ ] Premise check verified (overall revenue +7.6%)
- [ ] `evaluation.csv` run with a real LLM and results filled in
- [ ] Screenshots added to `assets/screenshots/`
- [ ] Git commit made

---

## 📂 GitHub Push

```bash
git add .
git commit -m "Day 56: Complete Business Agent + evaluation + premise check"
git push
```

---

## 🧠 Skill Learned

Business Problem Understanding → Structured Data → Business KPIs → Tool Calling → MCP → Database → External Research → Multi-Tool Agents → Agent Planning → Evidence-Based Analysis → Business Recommendations → Evaluation → Deployment

---

## 📌 Status (honest)

- **Verified:** all 36 automated tests pass; the pipeline runs end to end with the LLM calls mocked, using the real database, planner, and analyzer; the numbers in this note come from real queries.
- **Not yet done:** running the 17 evaluation questions with a real LLM (no API key was available while building), live Tavily search, connecting a real external MCP client, and deployment.
