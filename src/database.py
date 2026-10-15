"""
database.py
Day 51 + 53: synthetic business dataset generation + SQLite schema/build.

Generates realistic-looking (but synthetic) business data into data/*.csv,
then loads it into data/business.db. One product (UrbanTote Backpack) has a
deliberately engineered June price-driven revenue decline, so the Day 56
demo question ("why did revenue drop?") has a real, discoverable answer in
the data rather than nothing to find.

Run directly to (re)build everything:
    python -m src.database
"""

import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from . import config

REGIONS = ["Punjab", "Sindh", "KPK", "Balochistan"]
REGION_WEIGHTS = [0.42, 0.30, 0.18, 0.10]
SEGMENTS = ["Retail", "Wholesale"]
SEGMENT_WEIGHTS = [0.75, 0.25]

PRODUCTS = [
    (1, "UrbanTote Backpack", "Apparel", 3500),
    (2, "AeroFit Running Shoes", "Apparel", 4200),
    (3, "PixelBeam LED Lamp", "Home", 1800),
    (4, "CrispAir Fan", "Home", 5200),
    (5, "SonicPods Earbuds", "Electronics", 6500),
    (6, "VoltCharge Power Bank", "Electronics", 2200),
    (7, "GlowSkin Face Serum", "Beauty", 1500),
    (8, "PureMist Diffuser", "Home", 2600),
    (9, "TrailBlaze Water Bottle", "Apparel", 900),
    (10, "NovaView Sunglasses", "Apparel", 1700),
]

MONTHS = [(2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5), (2026, 6)]
ANOMALY_PRODUCT_ID = 1  # UrbanTote Backpack
ANOMALY_MONTH = (2026, 6)
ANOMALY_DISCOUNT = 0.68  # June price = 68% of normal -> ~31% revenue drop at similar volume

FIRST_NAMES = ["Ayesha", "Bilal", "Sara", "Omar", "Zainab", "Hamza", "Fatima", "Ali",
               "Mehwish", "Usman", "Noor", "Hassan", "Amna", "Saad", "Maryam", "Tariq"]
LAST_NAMES = ["Khan", "Malik", "Siddiqui", "Raza", "Qureshi", "Butt", "Shaikh", "Chaudhry"]


def _month_dates(year: int, month: int):
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    days = (end - start).days
    return start, days


def generate_customers(rng: random.Random, n: int = 60):
    rows = []
    start_pool = date(2025, 6, 1)
    for cid in range(1, n + 1):
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        region = rng.choices(REGIONS, weights=REGION_WEIGHTS)[0]
        segment = rng.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        signup = start_pool + timedelta(days=rng.randint(0, 400))
        rows.append((cid, name, region, segment, signup.isoformat()))
    return rows


def generate_orders_and_sales(rng: random.Random, customers):
    orders = []
    sales = []
    order_id = 1
    sale_id = 1
    customer_ids = [c[0] for c in customers]
    customer_region = {c[0]: c[2] for c in customers}

    for (year, month) in MONTHS:
        start, days = _month_dates(year, month)
        n_orders = rng.randint(78, 92)

        for _ in range(n_orders):
            cust_id = rng.choice(customer_ids)
            order_date = start + timedelta(days=rng.randint(0, days - 1))
            region = customer_region[cust_id]
            orders.append((order_id, cust_id, order_date.isoformat(), region))

            n_items = rng.choices([1, 2, 3], weights=[0.55, 0.35, 0.10])[0]
            chosen_products = rng.sample(PRODUCTS, k=min(n_items, len(PRODUCTS)))

            for prod in chosen_products:
                pid, _name, _cat, base_price = prod
                quantity = rng.randint(1, 4)

                price_wobble = rng.uniform(0.95, 1.05)
                unit_price = base_price * price_wobble

                if pid == ANOMALY_PRODUCT_ID and (year, month) == ANOMALY_MONTH:
                    unit_price = base_price * ANOMALY_DISCOUNT * rng.uniform(0.97, 1.03)

                unit_price = round(unit_price, 2)
                revenue = round(unit_price * quantity, 2)

                sales.append((sale_id, order_id, pid, quantity, unit_price, revenue))
                sale_id += 1

            order_id += 1

    return orders, sales


def write_csvs():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(7)

    customers = generate_customers(rng)
    orders, sales = generate_orders_and_sales(rng, customers)

    with open(config.CUSTOMERS_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "name", "region", "segment", "signup_date"])
        w.writerows(customers)

    with open(config.PRODUCTS_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "name", "category", "base_price"])
        w.writerows(PRODUCTS)

    with open(config.ORDERS_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer_id", "order_date", "region"])
        w.writerows(orders)

    with open(config.SALES_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sale_id", "order_id", "product_id", "quantity", "unit_price", "revenue"])
        w.writerows(sales)


SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    segment TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    base_price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    revenue REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_order ON sales(order_id);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def build_database(force: bool = False):
    """Builds data/business.db from the CSVs, generating the CSVs first if
    they don't exist yet. Safe to call repeatedly."""
    if force or not config.CUSTOMERS_CSV.exists():
        write_csvs()

    if config.DB_PATH.exists() and not force:
        return

    if config.DB_PATH.exists():
        config.DB_PATH.unlink()

    conn = get_connection()
    try:
        conn.executescript(SCHEMA)

        with open(config.CUSTOMERS_CSV) as f:
            reader = csv.reader(f)
            next(reader)
            conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", reader)

        with open(config.PRODUCTS_CSV) as f:
            reader = csv.reader(f)
            next(reader)
            conn.executemany("INSERT INTO products VALUES (?,?,?,?)", reader)

        with open(config.ORDERS_CSV) as f:
            reader = csv.reader(f)
            next(reader)
            conn.executemany("INSERT INTO orders VALUES (?,?,?,?)", reader)

        with open(config.SALES_CSV) as f:
            reader = csv.reader(f)
            next(reader)
            conn.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?)", reader)

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    build_database(force=True)
    conn = get_connection()
    counts = {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("customers", "products", "orders", "sales")
    }
    conn.close()
    print("Database built at", config.DB_PATH)
    print(counts)
