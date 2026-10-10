<p align="center">
  <img src="assets/banner.svg" alt="AI Business Agent Banner" width="100%"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/MCP-Model%20Context%20Protocol-6366f1?style=flat-square" alt="MCP"/>
  <img src="https://img.shields.io/badge/SQLite-Business%20Data-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/Evidence--Based-Reports-10b981?style=flat-square" alt="Evidence Based"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Status-Complete-22c55e?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/Last%20Commit-Week%208-6366f1?style=flat-square" alt="Last Commit"/>
</p>

<div align="center">

[![M8ven Score](https://m8ven.ai/badge/mcp/hamna-munir-08-ai-business-agent-8ykh4h?v=daba5e785527aa39524326a7329fb551)](https://m8ven.ai/mcp/hamna-munir-08-ai-business-agent-8ykh4h?s=readme)

</div>

<p align="center">
  An AI agent that investigates a real business question against a real SQLite database — through a real MCP server — and writes an evidence-grounded report instead of a chatbot guess.<br/>
  Eighth deliverable of a <b>90-day AI Engineering roadmap</b> (Phase 1: Foundation, Week 8).
</p>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Demo](#-demo)
- [Installation](#️-installation)
- [How to Run](#️-how-to-run)
- [Example Question](#-example-question)
- [Architecture](#️-architecture)
- [Why a Real Database + Real MCP Server](#-why-a-real-database--real-mcp-server)
- [Folder Structure](#-folder-structure)
- [Future Improvements](#-future-improvements)
- [Roadmap Context](#-roadmap-context)
- [Author](#-author)
- [License](#-license)

---

## 📖 Overview

**AI Business Agent** (UI codename **Ledger**) takes a plain-English business
question — *"Why did our revenue decrease this month?"* — and actually
investigates it: classifies the question, plans which business data it
needs, queries a real SQLite database (optionally through a real MCP
server), computes grounded findings in plain Python, optionally gathers
external research, and writes a structured report. If the data doesn't
support a conclusion, it says so instead of guessing.

This is **Repo 8 of 10+** in a structured 90-day AI Engineering roadmap.

---

## ✨ Features

- 🧭 **Question Classification** — maps a business question to a category (sales, customers, operations, finance, inventory, marketing, general) and the data it needs
- 🗃️ **Real SQLite Business Database** — `customers`, `products`, `orders`, `sales` tables, generated from realistic synthetic data (Pakistani regions: Punjab, Sindh, KPK, Balochistan)
- 🔌 **Real MCP Server** — `mcp_server.py` exposes 7 business-data tools over the actual Model Context Protocol (official `mcp` SDK), connectable from Claude Desktop, Claude Code, or any MCP client — not just this app
- 🧠 **Deterministic Planning** — `planner.py` extracts the month/region/product mentioned in the question and selects the right tools, with no LLM call needed for that step
- 📊 **Grounded Analysis** — `analyzer.py` computes percentage changes and distinguishes a **price-driven** decline from a **demand-driven** one, directly from the numbers — not from LLM guesswork
- 🌐 **Optional External Research** — `browser_tools.py` (Tavily search), used only when the question asks for external factors, with an honest "not configured" fallback instead of silent failure
- 📁 **Sandboxed File Access** — `file_tools.py` can only read from `data/`, `docs/`, `notes/`; path traversal is structurally blocked
- 🚫 **No Hallucinated Numbers** — the report-writing LLM only works from evidence it's explicitly handed; "Insufficient evidence to determine the cause" is a real, tested fallback
- 🎨 **Evidence-Transparent UI** — every report comes with an expandable "agent's work" panel showing the plan, tool calls, and raw findings
- 🧪 **Evaluated against 15+ real business questions** — sales, customers, operations, research, multi-step, and deliberately impossible/insufficient-evidence questions

---

## 🎥 Demo

*(Add a screenshot or short GIF/video here once available — see `assets/screenshots/`)*

---

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/Hamna-Munir/08-AI-Business-Agent.git
cd 08-AI-Business-Agent

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# then add your Groq/LLM API key (OPENAI_API_KEY, starts with gsk_)
# TAVILY_API_KEY is optional — only needed for external-research questions
```

---

## ▶️ How to Run

```bash
# Build the synthetic business database (safe to re-run; no-ops if it exists)
python -m src.database

# Run the Streamlit app
streamlit run src/app.py
# or: python -m streamlit run src/app.py

# Run the MCP server standalone (for Claude Desktop/Code or the MCP Inspector)
python -m src.mcp_server

# Run the test suite (fully mocked LLM calls — no API key needed)
pytest
```

---

## 💬 Example Question

> "Why did our revenue drop this month?"

The agent finds — for real, from the database, not scripted —:

> *UrbanTote Backpack revenue decreased 35.7% from 2026-05 (PKR 167,162) to
> 2026-06 (PKR 107,464). Order count changed +0.0% and units sold changed
> -6.2% over the same period. Average unit price changed -31.2%. Because
> order volume stayed roughly stable while average price dropped sharply,
> the revenue decline is price-driven, not demand-driven.*

---

## 🏗️ Architecture

```
Business Question
        ↓
   BUSINESS AGENT
        ↓
   Task Planning            (Day 50 classify + Day 55 plan)
        ↓
   Tool Selection
        ↓
┌───────────┼────────────┐
↓           ↓            ↓
MCP Tools  Database    Browser/File
(Day 52)   (Day 53)    (Day 54)
↓           ↓            ↓
└───────────┼────────────┘
        ↓
   Evidence/Data
        ↓
   Analysis               (Day 55-56 — grounded, numeric)
        ↓
   Business Recommendations
        ↓
   Structured Report
```

---

## 🔍 Why a Real Database + Real MCP Server

A toy in-memory dataset with no real pattern in it can't teach — or
demonstrate — anything about evidence-based reasoning, because every
question would have either an obvious or an arbitrary answer. The SQLite
database here has a deliberately engineered, non-obvious story in it (see
`docs/week-08-summary.md`), and `mcp_server.py` exposes the same business
tools over the actual MCP protocol rather than a bespoke function-calling
shim — so the same data is queryable from this app, from Claude Desktop, or
from any other MCP client, which is the actual point of MCP.

---

## 📂 Folder Structure

```
08-AI-Business-Agent/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── .env.example
│
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── agent.py
│   ├── planner.py
│   ├── business_tools.py
│   ├── mcp_server.py
│   ├── database.py
│   ├── browser_tools.py
│   ├── file_tools.py
│   ├── analyzer.py
│   ├── prompts.py
│   └── config.py
│
├── data/
│   ├── customers.csv
│   ├── products.csv
│   ├── orders.csv
│   ├── sales.csv
│   └── business.db
│
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_tools.py
│   ├── test_database.py
│   ├── test_mcp.py
│   └── test_analysis.py
│
├── evaluation/
│   └── evaluation.csv
│
├── docs/
│   └── week-08-summary.md
│
├── notes/
│   ├── day-50.md
│   ├── day-51.md
│   ├── day-52.md
│   ├── day-53.md
│   ├── day-54.md
│   ├── day-55.md
│   └── day-56.md
│
├── assets/
│   ├── banner.svg
│   └── screenshots/
│
└── journal.md
```

---

## 🚀 Future Improvements

- [ ] LLM-based entity extraction in `planner.py` for messier real-world phrasing
- [ ] Multi-turn "drill into this finding" follow-up mode
- [ ] Point `database.py` at a real data warehouse/CSV export instead of synthetic data
- [ ] Add a second external-research provider as a fallback to Tavily
- [ ] Export reports as PDF/Word for sharing with stakeholders

---

## 🧭 Roadmap Context

This project is **Week 8 of Phase 1** in a 90-day AI Engineering roadmap:

| Phase | Focus | Days |
|---|---|---|
| Phase 1 | Foundation — Personal Assistant → ... → Meeting Agent → Business Agent | 1–30 |
| Phase 2 | Agent Engineering — RAG, LangGraph, MCP | 31–60 |
| Phase 3 | Business AI Systems — Multi-Agent, Deployment | 61–90 |

---

## 👩‍💻 Author

**Hamna Munir**
Software Engineering & AI/ML Student | Building deployable AI/ML projects

- GitHub: [@Hamna-Munir](https://github.com/Hamna-Munir)
- Hugging Face: [@Hamna27](https://huggingface.co/Hamna27)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
