# Day 53 — Database + Business Tools

**Objective:** Connect the Business Agent to an actual database and give it read-only business tools to query it.

---

## 📖 Theory

### SQLite

SQLite is a full SQL database stored in a single file (`data/business.db`). There is no server to install or run, and Python ships with the `sqlite3` module, so it is a good fit for a project of this size. The same SQL carries over to PostgreSQL or MySQL later.

### Database schema

```
customers(customer_id, name, region, segment, signup_date)
products(product_id, name, category, base_price)
orders(order_id, customer_id, order_date, region)
sales(sale_id, order_id, product_id, quantity, unit_price, revenue)
```

`database.py` creates these tables plus indexes on `orders.order_date`, `sales.product_id` and `sales.order_id`, so the month and product filters stay fast.

### Queries

Almost every business question here is a `SELECT` with a `JOIN`, a `GROUP BY` and an aggregate:

```sql
SELECT o.region, SUM(s.revenue) AS revenue
FROM sales s JOIN orders o ON s.order_id = o.order_id
GROUP BY o.region
ORDER BY revenue DESC;
```

### CRUD basics

CRUD = Create, Read, Update, Delete. `database.py` creates and fills the tables once (Create). Everything the agent does afterwards is Read.

### Read-only vs write operations

A business investigation agent should only read. All 7 functions in `business_tools.py` run `SELECT` statements and nothing else. Two protections matter:

- **Parameterized queries.** Filters (month, region, product name) are passed as `?` parameters, never pasted into the SQL string, so a question like `"; DROP TABLE sales;--` cannot become SQL.
- **No write tool exists.** The agent can only call what is registered in `TOOL_REGISTRY`, and none of those tools modify data.

Honest limitation: the connection itself is opened normally, not in SQLite's read-only mode. Opening it with `file:data/business.db?mode=ro` (URI mode) would enforce read-only at the database level too. That is a good hardening step.

### Database as an agent tool

The LLM never touches the database. It asks for a tool by name, a normal Python function runs the SQL, and the rows come back as plain dicts. This keeps the numbers real and the agent testable.

### Tool selection

Seven tools means the agent must pick the right ones. Rule of thumb used in this project:

| Question is about | Tool |
|---|---|
| Revenue by month/region | `get_sales_data`, `get_regional_trend` |
| One product over time | `get_product_sales` |
| Best sellers | `get_top_products` |
| Segments / who buys | `get_customer_metrics`, `get_customer_data` |
| What we sell | `get_product_data` |

Day 55 automates this choice in `planner.py`.

---

## 💻 Coding Exercise

Build the database and the business tools.

**Create `business.db`:**

```bash
python -m src.database
```

Expected output:

```
Database built at .../data/business.db
{'customers': 60, 'products': 10, 'orders': 492, 'sales': 736}
```

**Business tools** (`src/business_tools.py`). The roadmap's names map to this project like this:

| Roadmap name | Implemented as |
|---|---|
| `get_sales()` | `get_sales_data(month, region)` |
| `get_product_sales()` | `get_product_sales(product_name, months)` |
| `get_customer_metrics()` | `get_customer_metrics(month)` |
| `get_top_products()` | `get_top_products(month, limit)` |

Plus `get_customer_data`, `get_product_data`, `get_regional_trend`, and a `TOOL_REGISTRY` dict that lists them all by name.

---

## 🛠 Mini Project

**Question:** "Which region generated the most revenue?"

Flow:

```
Business Question
        ↓
Agent
        ↓
Business Tool  (get_regional_trend / get_sales_data)
        ↓
Database
        ↓
Result
        ↓
Agent Analysis
```

Real result from this project's database (all six months, Jan to Jun 2026):

| Region | Revenue (PKR) | Orders |
|---|---|---|
| Sindh | 1,962,905 | 164 |
| Punjab | 1,732,988 | 148 |
| Balochistan | 1,119,303 | 85 |
| KPK | 955,197 | 95 |

Sindh leads over the full period. Do not assume the largest region is the biggest earner: the data generator weights *customers* by region, but each order is random, so the revenue ranking comes from the data, not from an assumption. Always let the tool answer.

Verify it yourself:

```bash
python -c "from src.business_tools import get_regional_trend; print(get_regional_trend())"
```

---

## 🧠 Quiz

1. Why are filters passed as `?` parameters instead of building the SQL string with an f-string?
2. Why does the agent get tools that call SQL instead of writing its own SQL?
3. What would you change so the database connection itself is read-only?
4. Why is "Which region has the most revenue?" better answered by a tool than by the LLM's general knowledge?

*(Try answering from memory first, then check the theory section above.)*

---

## 🐞 Common Errors

| Error | Likely Cause | Fix |
|---|---|---|
| `no such table: sales` | Database not built | Run `python -m src.database` |
| Revenue numbers look inflated | Summing after a join that repeats rows | Sum only `sales.revenue`; count orders with `COUNT(DISTINCT order_id)` |
| Empty result for a product name | `LIKE` pattern did not match the name | Use part of the name (`UrbanTote`); the tool wraps it in `%...%` |
| Month filter returns nothing | Month not in the data | Valid months are `2026-01` to `2026-06`; call `list_available_months()` |
| Foreign keys not enforced | SQLite ignores them by default | Run `PRAGMA foreign_keys = ON` per connection if you need enforcement |
| Assumed answer differs from the data | Guessing the result before querying | Query first, then explain (as with the region ranking above) |

---

## ✅ Checklist

- [ ] SQLite schema understood (4 tables + indexes)
- [ ] `business.db` built with `python -m src.database`
- [ ] 7 read-only business tools working
- [ ] Region revenue question answered from a real query
- [ ] Git commit made

---

## 📂 GitHub Push

```bash
git add .
git commit -m "Day 53: SQLite business database + business tools"
git push
```

---

## 🧠 Skill Learned

Agent + database + tool calling
