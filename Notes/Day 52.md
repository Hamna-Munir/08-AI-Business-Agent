# Day 52 — Tools + MCP Fundamentals

**Objective:** Understand how an agent can access external capabilities through a standardized tool interface, and build a first real MCP server.

---

## 📖 Theory

### What is MCP?

MCP (Model Context Protocol) is an open standard for how an AI application discovers and calls external tools and data. Instead of every app writing its own custom glue between an LLM and a database, an MCP **server** describes what it can do ("here are my tools, here are their inputs"), and any MCP **client** can use it.

### Why MCP?

Without a standard, connecting 3 AI apps to 4 data sources means writing up to 12 custom integrations. With MCP, each data source is wrapped once as a server and every MCP-capable app can use it. In this project the same business data becomes usable from Claude Desktop, Claude Code, or the MCP Inspector without extra code.

### MCP client vs MCP server

| | Role | In this project |
|---|---|---|
| MCP server | Exposes tools/resources | `src/mcp_server.py` (business data) |
| MCP client | Connects to a server, lists its tools, calls them | Claude Desktop, Claude Code, MCP Inspector |

### Tools vs resources

- **Tools** are actions the model can call with arguments (`get_top_products(month="2026-06")`).
- **Resources** are read-only data the client can load as context (a file, a document).

This project only uses tools. Resources would be a natural next step, for example exposing the schema or the product catalog as a resource.

### Traditional function calling vs MCP

| | Function calling | MCP |
|---|---|---|
| Where tools are defined | Inside one app's code | In a separate server |
| Reuse across apps | Rewrite per app | One server, many clients |
| Discovery | Hardcoded in the prompt/code | Client asks the server what it offers |

### Architecture

```
AI Agent
   ↓
MCP Client
   ↓
MCP Server        (src/mcp_server.py)
   ↓
Tools / Resources (src/business_tools.py)
   ↓
Business Data     (data/business.db)
```

### An honest note on how this project uses it

The Streamlit agent (`agent.py`) calls the functions in `business_tools.py` **directly, in the same process**, because that is simpler for a single-process app. `mcp_server.py` wraps those same functions so that *external* MCP clients can use them too. The tool logic exists once, and there are two ways to reach it.

---

## 💻 Coding Exercise

Build your first MCP server with the official `mcp` Python SDK.

```python
from mcp.server.mcpserver import MCPServer
from . import business_tools

mcp = MCPServer("business-data")

@mcp.tool()
def get_sales_data(month: Optional[str] = None, region: Optional[str] = None) -> list:
    """Monthly revenue, units, and order count."""
    return business_tools.get_sales_data(month=month, region=region)

if __name__ == "__main__":
    mcp.run()
```

Tools registered in `src/mcp_server.py` (7 total):

```
get_sales_data        get_customer_data     get_customer_metrics
get_product_data      get_product_sales     get_top_products
get_regional_trend
```

The docstring and type hints become the tool description and input schema the client sees, so write them carefully.

Run it standalone from the project root:

```bash
python -m src.mcp_server
```

---

## 🛠 Mini Project

**Business Data MCP Server**

1. Run the server and connect an MCP client (for example the MCP Inspector, or add it as a server in Claude Desktop/Claude Code with `python -m src.mcp_server` as the command, using absolute paths).
2. List the tools and confirm all 7 appear.
3. Call `get_top_products` with `month = 2026-06` and `limit = 3`.
4. Confirm it matches calling `business_tools.get_top_products(...)` directly.

Step 4 is automated in `tests/test_mcp.py`: it checks that the registered tool names equal `business_tools.TOOL_REGISTRY`, and that a call through the server returns the same rows as the direct call.

---

## 🧠 Quiz

1. What problem does MCP solve that plain function calling doesn't?
2. What is the difference between an MCP tool and an MCP resource?
3. In this project, why does the Streamlit agent not go through the MCP server?
4. Why does a tool's docstring matter more in MCP than in a normal Python function?

*(Try answering from memory first, then check the theory section above.)*

---

## 🐞 Common Errors

| Error | Likely Cause | Fix |
|---|---|---|
| `No module named 'mcp.server.fastmcp'` | `mcp` v2 renamed `FastMCP` to `MCPServer` | Use `from mcp.server.mcpserver import MCPServer` (this project requires `mcp>=2.0.0`) |
| Older tutorial code fails on import | Tutorial written for `mcp` v1 | Either update the import, or pin `mcp<2` to keep running v1 code |
| `python -m src.mcp_server` can't find `src` | Run from the wrong folder | Run from the project root; `src/__init__.py` must exist |
| Client shows no tools | Server crashed on start or wrong command path | Run the command by hand first and read the error; use absolute paths in client config |
| Tool results look different from direct calls | Wrapper changed or reshaped the data | Keep wrappers thin, and keep the test in `test_mcp.py` |

---

## ✅ Checklist

- [ ] MCP concepts understood (client, server, tools, resources)
- [ ] MCP server built with 7 business tools
- [ ] Server runs with `python -m src.mcp_server`
- [ ] Tool list and one tool call verified against a client or `test_mcp.py`
- [ ] Git commit made

---

## 📂 GitHub Push

```bash
git add .
git commit -m "Day 52: MCP server exposing business data tools"
git push
```

---

## 🧠 Skill Learned

MCP fundamentals + external tool access
