# Day 54 — Business Research + Browser/File Tools

**Objective:** Stop limiting the agent to internal business data. It should be able to combine internal data with external information, while keeping track of which is which.

---

## 📖 Theory

### Internal data + external information

Internal data tells you **what happened and where** ("UrbanTote revenue fell 35.7% in June"). It cannot tell you about the outside world: competitors, seasons, events, economic conditions. External research can suggest *possible* outside factors. The agent has to treat the two kinds of evidence very differently.

### Browser tools

A browser/search tool lets the agent look things up on the web. In this project `browser_tools.py` has one function, `search_external_information(query)`, built on the Tavily search API. It returns a list of results:

```
{"title": ..., "url": ..., "snippet": ..., "source": "external_web_search"}
```

### File-system tools

`file_tools.py` lets the agent read narrative files (notes, docs) for extra context:

- `list_business_files()` lists readable files
- `read_business_file(relative_path)` reads one, truncated at 4,000 characters

Access is limited to an allow-list: `data/`, `docs/`, `notes/`.

### Internal vs external evidence

| | Internal evidence | External evidence |
|---|---|---|
| Source | Company database | Web search |
| Reliability | Exact numbers, checkable | Varies, may be unrelated |
| What it can show | What changed, where, by how much | Possible outside explanations |
| How the report should treat it | A finding | A hypothesis, with a link |

### Source tracking

Every external result carries `"source": "external_web_search"` plus its URL, so the report can say where a claim came from. A claim with no source should not appear in the report.

### Evidence-based reasoning

External research suggests causes, it does not prove them. If search says "fuel prices rose in Pakistan in June", the agent may mention it as a *possible* factor, but cannot say it caused the decline unless internal data supports the link.

### Data privacy

Two rules this project follows:

1. **File access is sandboxed.** The agent cannot read arbitrary paths, only the three allowed folders.
2. **Be careful what leaves the machine.** The search query is written by the LLM from a summary of the internal findings, then sent to an external service. The prompt asks for a short, generic query, but a product name could still end up in it. For real customer data, filter the query before sending.

### What is and is not wired in

- **External research** is wired into the pipeline: `agent.py` calls it only when the classifier sets `needs_external_research: true`.
- **File tools** exist, are tested, and are available as tools, but the agent's `investigate()` pipeline does not call them yet. Hooking them in (for example, reading a company policy document) is a Day 55+ extension.
- I have **not tested live search with a real Tavily key**; the offline behaviour (no key) is tested.

---

## 💻 Coding Exercise

Build the agent's research capabilities. The roadmap names map to this project like this:

| Roadmap name | Implemented as |
|---|---|
| `read_business_file()` | `file_tools.read_business_file(relative_path)` |
| `search_external_information()` | `browser_tools.search_external_information(query)` |
| `get_business_data()` | the 7 tools in `business_tools.py` (Day 53) |

The important design choice, in `browser_tools.py`:

```python
if not config.TAVILY_API_KEY:
    raise ResearchUnavailable("External research is not configured ...")
```

It raises an explicit error instead of returning an empty list. An empty list would look like "I searched and found nothing relevant", which is a false statement. `agent.py` catches the error and puts it in the report as *"External research was requested but unavailable"*.

To enable it, add a key to `.env`:

```
TAVILY_API_KEY=your_key_here
```

---

## 🛠 Mini Project

**Business Research Assistant**

**Question:** "Our sales dropped in June. What external factors could explain this?"

Expected flow:

```
Internal data   → finds when/where/what changed (get_product_sales, get_regional_trend)
        ↓
External search → LLM writes a short query, Tavily returns sources
        ↓
Analysis        → separates internal findings from external hypotheses
```

Things to check:

1. **Without a Tavily key:** the report says external research was unavailable and does not invent outside causes.
2. **With a key:** external points appear with titles and links, labelled as possible factors.
3. **Internal data first:** in this dataset the strongest finding is internal (UrbanTote's average price fell about 31% while orders stayed flat), so external research should not override it.

---

## 🧠 Quiz

1. Why does `search_external_information` raise an error when no API key is set, instead of returning an empty list?
2. A search result says "demand fell across the region in June". Can the agent say that *caused* the decline? Why or why not?
3. Why does the file tool use an allow-list instead of just warning the agent to be careful with paths?
4. What could leak from the LLM-written search query, and how would you reduce it?

*(Try answering from memory first, then check the theory section above.)*

---

## 🐞 Common Errors

| Error | Likely Cause | Fix |
|---|---|---|
| `ResearchUnavailable: ... no TAVILY_API_KEY set` | Key missing from `.env` | Add `TAVILY_API_KEY` (research is optional; the agent still works without it) |
| `ResearchUnavailable: ... request failed` | Network issue or invalid key | Check connectivity and the key; the agent reports it instead of crashing |
| `FileAccessError: ... outside the allowed directories` | Path outside `data/`, `docs/`, `notes/` | Use a path inside those folders |
| A sibling folder like `docs_private/` was readable | Allow-list used string `startswith`, which matches by name prefix | Fixed: now uses `Path.is_relative_to`, with a regression test |
| Report presents web claims as proven causes | Mixing external hypotheses into "findings" | Keep external results in a separate, labelled section and word them as possibilities |
| Query leaks product names | Query built from internal summary | Make the query generic, or strip internal names before searching |

---

## ✅ Checklist

- [ ] Internal vs external evidence difference understood
- [ ] `search_external_information()` built with an explicit "unavailable" path
- [ ] `read_business_file()` built with a folder allow-list
- [ ] Path-traversal and sibling-folder cases tested
- [ ] Report behaviour checked with and without a Tavily key
- [ ] Git commit made

---

## 📂 GitHub Push

```bash
git add .
git commit -m "Day 54: External research + sandboxed file tools"
git push
```

---

## 🧠 Skill Learned

Multi-source business research
