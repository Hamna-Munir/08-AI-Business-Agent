# Day 55 — Business Agent Decision-Making

**Objective:** The agent must decide *which tool to use*, instead of blindly calling every tool.

---

## 📖 Theory

### Agent planning

Planning means deciding what to do before doing it. For "Why are sales declining?" a good plan is not "call everything". It is:

```
1. Need sales data
2. Check the sales trend
3. Identify affected products/regions
4. Need customer information?
5. Need external research?
6. Synthesize the evidence
```

### Task decomposition

Break the big question into smaller ones the tools can answer: how much did revenue change, in which region, on which product, and was it price or volume. Each small question maps to one tool.

### Tool selection

In this project tool selection is **plain Python in `planner.py`, with no LLM call**. The LLM does two jobs only: classify the question (Day 50) and write the final report (Day 56). Keeping planning deterministic makes it fast, predictable, and unit-testable.

### How `planner.py` works

Two steps:

**1. Extract entities from the question** (`extract_entities`)

| Entity | How it is found |
|---|---|
| month | month name (whole word), or "this month" / "last month" |
| region | Punjab, Sindh, KPK, Balochistan |
| product | full product name, or its first word (e.g. `UrbanTote`) |

"This month" means the **latest month in the data** (`2026-06`), not today's calendar date. The dataset ends in June 2026.

**2. Map the classification onto tools** (`build_plan`)

| Condition | Tools added |
|---|---|
| sales/finance category, or `sales_data` required | `get_sales_data`, `get_regional_trend` |
| a product is named, or sales/inventory category, or `product_data` required | `get_product_sales`, `get_top_products` |
| customers category, or `customer_data` required | `get_customer_metrics`, `get_customer_data` |
| nothing matched | fallback: `get_sales_data`, `get_top_products` |

The plan is capped at `MAX_TOOL_CALLS_PER_QUESTION = 6`.

Real plans produced by this project:

| Classification | Tools chosen |
|---|---|
| sales | `get_sales_data`, `get_regional_trend`, `get_product_sales`, `get_top_products` |
| customers | `get_customer_metrics`, `get_customer_data` |
| inventory | `get_product_sales`, `get_top_products` |
| vague / general | `get_sales_data`, `get_top_products` |
| sales + customers + products | all of the above, capped at 6 |

### Multi-step reasoning

After the tools return, `analyzer.py` turns rows into findings (revenue change, order change, price change, price-driven vs demand-driven). The report is written only from those findings.

### Tool results and context management

Everything gathered for one question is kept in an `InvestigationTrace` (classification, every tool call with its arguments, findings, research, report). The UI shows it in the "agent's work" panel.

### Failure handling

`run_tools()` wraps each call in try/except. A failing tool becomes `{"error": "..."}`; `analyze_results()` skips it, and the other tools still run. One broken tool does not crash the report. This is tested in `test_agent.py`.

### Important rule: do not invent numbers

If the data does not support a conclusion, the report must say:

> "Insufficient evidence to determine the cause from the available business data."

**What is enforced in code:** if there are zero findings and no research, `synthesize_report()` returns that message directly, without asking the LLM.

**What is enforced only by the prompt:** if there are findings but they are unrelated to the question, the LLM is *told* to say insufficient evidence. Nothing in code verifies that it does.

### Known limitations (honest list)

1. **The plan is one-shot, not adaptive.** All tools are chosen before any result is seen. A real investigator would look at the result ("Punjab fell") and then drill in ("which Punjab products?"). That would need a loop; this is the natural next step.
2. **Off-topic questions are not blocked.** For "What is the airspeed of a swallow?" the planner falls back to sales + top products, which return real rows, so findings are not empty and the code-level guard does not trigger. Evaluation rows 12 and 13 test exactly this and are still PENDING.
3. **Unknown places pass through.** "Why did our Tokyo store underperform?" matches no region, so the plan runs without a region filter. A check "named region not in the data" would be a good addition.
4. **Entity extraction is keyword-based**, so unusual phrasing ("the northern province") will not be understood.

---

## 💻 Coding Exercise

Build the **Business Investigation Agent**'s planning layer.

Possible tools: `get_sales_data()`, `get_customer_data()`, `get_product_data()`, `search_external_information()`, `read_business_file()`.

```python
from src.planner import build_plan, extract_entities

classification = {"category": "sales", "required_data": ["sales_data"]}
plan = build_plan("Why did our revenue drop this month?", classification)
for step in plan:
    print(step.tool_name, step.kwargs, "->", step.label)
```

Output:

```
get_sales_data {'month': '2026-06'} -> Overall sales figures
get_regional_trend {} -> Revenue trend by region
get_product_sales {} -> Monthly trend, all products
get_top_products {'month': '2026-06'} -> Top products by revenue
```

---

## 🛠 Mini Project

**Business Investigation Agent**

**Question:** "Why are sales declining?"

Run the full pipeline (`BusinessAgent.investigate`). The planner picks the tools, the analyzer finds that UrbanTote Backpack's June revenue fell 35.7% while orders stayed at 17 and average price fell 31.2%, and the report concludes the decline is **price-driven, not demand-driven**.

Also test:

- A customers question: confirm no sales tools are called.
- A vague question: confirm the fallback tools are used.
- A broken tool: confirm the report still completes.

---

## 🧠 Quiz

1. Why is the planner free of LLM calls? What is gained and what is lost?
2. What does "this month" mean in this agent, and why can that be misleading?
3. Why is a one-shot plan weaker than an adaptive one for "why did revenue drop?"
4. Which part of the "insufficient evidence" rule is guaranteed by code, and which only by the prompt?

*(Try answering from memory first, then check the theory section above.)*

---

## 🐞 Common Errors

| Error | Likely Cause | Fix |
|---|---|---|
| "Maybe" or "mayor" read as the month May | Month names matched as substrings | Fixed: whole-word match (`\bmay\b`), with regression tests |
| Plan calls every tool | Conditions too loose | Keep tool conditions tied to category/required data (customers question must not pull sales tools) |
| "This month" gives old data | It means the latest month *in the database* | Be aware the dataset ends in 2026-06 |
| Region named but no filter applied | Region not in the known list | Add it to `_extract_region`, or flag unknown regions as insufficient evidence |
| Mocking a tool in a test has no effect | Registry captured the original function at import | `run_tools` now resolves by name at call time (`getattr(business_tools, name)`) |
| Report answers an unrelated question | Fallback tools return real rows | Add a relevance check before synthesis (limitation 2 above) |

---

## ✅ Checklist

- [ ] Planning, decomposition, and tool selection understood
- [ ] `planner.py` built (entities + plan)
- [ ] Plans differ correctly for sales / customers / vague questions
- [ ] Failure handling tested (one broken tool, report still completes)
- [ ] Limitations understood and written down
- [ ] Git commit made

---

## 📂 GitHub Push

```bash
git add .
git commit -m "Day 55: Planner + tool selection, month-matching fix"
git push
```

---

## 🧠 Skill Learned

Agent planning + multi-tool orchestration
