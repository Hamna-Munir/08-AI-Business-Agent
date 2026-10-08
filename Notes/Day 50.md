# Day 50 — Business Agent Fundamentals

**Objective:** Understand how a Business Agent differs from a normal chatbot or a traditional analytics script.

---

## 📖 Theory

### What is a Business Agent?

An agent that can take a business question, decide what data it actually needs, go get that data through tools, reason over it, and produce an evidence-based answer — rather than just generating plausible-sounding text about the business. This is the same agent pattern from Weeks 5-7 (goal → tools → decision → action), now applied to business questions instead of emails or meetings.

### Why do businesses need agents (not just dashboards or chatbots)?

A dashboard shows fixed metrics someone else decided were important. A chatbot answers from general knowledge — it has no idea what *your* sales actually did this month. A business agent sits in between: it decides, per question, which of the business's real data is relevant, goes and checks it, and only then answers.

### Agent vs. chatbot

A chatbot asked "why did sales drop?" will produce a fluent, generic-sounding answer from pattern alone — it has no way to know if it's actually true. A business agent calls real tools (`business_tools.py` in this project) against a real database and can only say what the data actually shows.

### Agent vs. traditional automation

A traditional script runs one fixed query and formats the result — useful, but it only ever answers the one question it was written for. An agent decides *which* query (or queries) a new, never-seen-before question needs, which is the actual hard part.

### Business questions → actions

"Which products are losing the most sales?" isn't itself an action — it implies a sequence: figure out what "losing sales" means numerically (month-over-month revenue decline), pull product-level sales data, rank it, and report the losers. Turning a question into that sequence is the agent's first real job.

### Task decomposition

Breaking "why did revenue decline?" into smaller sub-questions (which products? which regions? price or volume driven? any single large account churning?) before trying to answer the big question directly. Covered properly in Day 55; Day 50 is just the classification step that *starts* this process.

### Tool usage

Business questions get answered by calling tools — `get_sales_data()`, `get_top_products()`, etc. — not by the LLM inventing numbers. This project's agent never answers a numeric question without a tool call behind it.

### Business context

The same question means different things in different categories: "performance" for a sales question means revenue; for an operations question it might mean order-processing time. Classifying the category first (this project: `sales`, `marketing`, `customers`, `operations`, `finance`, `inventory`, `general`) is what lets the rest of the pipeline interpret the question correctly.

### Evidence-based decisions

The core discipline this whole project is built around: every claim in the final report has to trace back to a real number from a real tool call. "Insufficient evidence" is a valid, expected answer — not a failure.

---

## 💻 Coding Exercise

Build a **Business Question Classifier**.

**Categories:** sales · marketing · customers · operations · finance · inventory · general

**Input:**
> "Which products are losing the most sales?"

**Output:**
```json
{
  "category": "sales",
  "task": "Product Performance Analysis",
  "required_data": ["sales_data", "product_data"]
}
```

In this project this lives in `prompts.py` (`classification_system_prompt()`) and is called by `agent.py`'s `classify_question()`, which also adds `needs_external_research` and `is_multi_step` flags used later by Day 55's planner.

---

## 🛠 Mini Project

Test the classifier against a spread of real-sounding business questions, e.g.:

- "Which products are losing the most sales?" → sales
- "Which customer segment has the highest value?" → customers
- "Which region generated the most revenue?" → sales
- "What external factors could explain a sales decline?" → sales + `needs_external_research: true`
- "Why did revenue decline and what should we investigate?" → sales + `is_multi_step: true`

---

## 🧠 Quiz

1. What's the actual difference between a business agent and a dashboard that already shows revenue by month?
2. Why does classification happen *before* any data is fetched, instead of just fetching everything and figuring it out after?
3. Give an example of a business question where the "obvious" category is wrong.
4. Why is "insufficient evidence" a correct answer sometimes, rather than something to avoid?

*(Try answering from memory first, then check the theory section above.)*

---

## 🐞 Common Errors

| Error | Likely Cause | Fix |
|---|---|---|
| Classifier invents a category not in the allowed list | No fixed category list enforced | Constrain `category` to `config.QUESTION_CATEGORIES` explicitly in the prompt |
| Treating every question as "sales" | Classifier prompt too narrow/example-biased | Give the LLM the full category list and let it choose, don't hint toward one |
| Required data list too vague to act on (e.g. `["data"]`) | Prompt doesn't require specific data-source names | Ask for specific tool-shaped names (`sales_data`, `product_data`) that Day 55's planner can map to real tools |
| Classifying a vague/off-topic question as a confident business category | No fallback path for unrelated questions | Let `category: "general"` exist and be a legitimate, low-confidence outcome |

---

## ✅ Checklist

- [ ] Business agent vs. chatbot vs. traditional automation understood
- [ ] Business Question Classifier built (`prompts.classification_system_prompt`)
- [ ] Tested against a spread of real business questions
- [ ] Git commit made

---

## 📂 GitHub Push

```bash
git add .
git commit -m "Day 50: Business agent fundamentals + question classifier"
git push
```

---

## 🧠 Skill Learned

Business problem understanding + agent task classification
