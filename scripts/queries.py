"""
Retail BI Dashboard — SQL Analytics Layer

A library of production-style SQL queries against the DuckDB star schema.
These are the exact queries the Streamlit dashboard runs, and they double as
proof of SQL skill: CTEs, window functions, joins, aggregation, and ranking.

Every function returns a pandas DataFrame.
"""

import pathlib

import duckdb
import pandas as pd

DB_PATH = pathlib.Path("data/retail.db")


def connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH))


# --------------------------------------------------------------------------- #
# 1. Top-level KPIs (total sales, profit, orders, avg discount, margin)
# --------------------------------------------------------------------------- #
KPI_SQL = """
SELECT
    ROUND(SUM(sales), 2)                                AS total_sales,
    ROUND(SUM(profit), 2)                               AS total_profit,
    COUNT(DISTINCT order_id)                            AS total_orders,
    ROUND(AVG(discount) * 100, 2)                       AS avg_discount_pct,
    ROUND(SUM(profit) / NULLIF(SUM(sales), 0) * 100, 2) AS profit_margin_pct,
    ROUND(SUM(quantity), 0)                             AS total_units
FROM fact_sales
"""


def kpi_overview() -> pd.DataFrame:
    return connect().execute(KPI_SQL).df()


# --------------------------------------------------------------------------- #
# 2. Sales & profit over time (monthly) — time trend with a running total
# --------------------------------------------------------------------------- #
MONTHLY_SQL = """
WITH monthly AS (
    SELECT
        strftime(order_date, '%Y-%m') AS ym,
        ROUND(SUM(sales), 2)          AS sales,
        ROUND(SUM(profit), 2)         AS profit,
        COUNT(DISTINCT order_id)      AS orders
    FROM fact_sales
    GROUP BY 1
)
SELECT
    ym,
    sales,
    profit,
    orders,
    ROUND(SUM(sales) OVER (ORDER BY ym ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2)
        AS running_sales
FROM monthly
ORDER BY ym
"""


def monthly_trend() -> pd.DataFrame:
    return connect().execute(MONTHLY_SQL).df()


# --------------------------------------------------------------------------- #
# 3. Sales by category, with rank + share of total (window functions)
# --------------------------------------------------------------------------- #
CATEGORY_SQL = """
WITH cat AS (
    SELECT
        p.category,
        ROUND(SUM(s.sales), 2)  AS sales,
        ROUND(SUM(s.profit), 2) AS profit,
        SUM(s.quantity)         AS units
    FROM fact_sales s
    JOIN dim_product p ON s.product_id = p.product_id
    GROUP BY p.category
)
SELECT
    category,
    sales,
    profit,
    units,
    ROUND(sales / SUM(sales) OVER () * 100, 1) AS sales_share_pct,
    RANK() OVER (ORDER BY sales DESC)           AS sales_rank
FROM cat
ORDER BY sales DESC
"""


def sales_by_category() -> pd.DataFrame:
    return connect().execute(CATEGORY_SQL).df()


# --------------------------------------------------------------------------- #
# 4. Sales by region — geographic performance with share
# --------------------------------------------------------------------------- #
REGION_SQL = """
WITH reg AS (
    SELECT
        l.region,
        ROUND(SUM(s.sales), 2)  AS sales,
        ROUND(SUM(s.profit), 2) AS profit
    FROM fact_sales s
    JOIN dim_location l ON s.postal_code = l.postal_code
    GROUP BY l.region
)
SELECT
    region,
    sales,
    profit,
    ROUND(sales / SUM(sales) OVER () * 100, 1) AS sales_share_pct,
    ROUND(profit / NULLIF(sales, 0) * 100, 2)  AS margin_pct
FROM reg
ORDER BY sales DESC
"""


def sales_by_region() -> pd.DataFrame:
    return connect().execute(REGION_SQL).df()


# --------------------------------------------------------------------------- #
# 5. Top 10 products by sales (ranking)
# --------------------------------------------------------------------------- #
TOP_PRODUCTS_SQL = """
SELECT
    p.product_name,
    p.category,
    ROUND(SUM(s.sales), 2)  AS sales,
    ROUND(SUM(s.profit), 2) AS profit
FROM fact_sales s
JOIN dim_product p ON s.product_id = p.product_id
GROUP BY p.product_name, p.category
ORDER BY sales DESC
LIMIT 10
"""


def top_products(n: int = 10) -> pd.DataFrame:
    q = TOP_PRODUCTS_SQL.replace("LIMIT 10", f"LIMIT {int(n)}")
    return connect().execute(q).df()


# --------------------------------------------------------------------------- #
# 6. Segment analysis — customer segment sales/profit + YoY growth (window)
# --------------------------------------------------------------------------- #
SEGMENT_SQL = """
WITH seg AS (
    SELECT
        c.segment,
        CAST(strftime(s.order_date, '%Y') AS INT) AS yr,
        ROUND(SUM(s.sales), 2)  AS sales,
        ROUND(SUM(s.profit), 2) AS profit
    FROM fact_sales s
    JOIN dim_customer c ON s.customer_id = c.customer_id
    GROUP BY c.segment, yr
),
with_prev AS (
    SELECT
        segment,
        yr,
        sales,
        profit,
        LAG(sales) OVER (PARTITION BY segment ORDER BY yr) AS prev_sales
    FROM seg
)
SELECT
    segment,
    yr,
    sales,
    profit,
    ROUND((sales - prev_sales) / NULLIF(prev_sales, 0) * 100, 1) AS yoy_growth_pct
FROM with_prev
ORDER BY segment, yr
"""


def segment_trend() -> pd.DataFrame:
    return connect().execute(SEGMENT_SQL).df()


# --------------------------------------------------------------------------- #
# 7. Loss analysis — which products lose money (negative profit) & by how much
# --------------------------------------------------------------------------- #
LOSS_SQL = """
WITH loss AS (
    SELECT
        p.category,
        p.sub_category,
        COUNT(*)            AS loss_rows,
        ROUND(SUM(s.profit), 2) AS total_loss,
        ROUND(SUM(s.sales), 2)  AS sales_at_loss
    FROM fact_sales s
    JOIN dim_product p ON s.product_id = p.product_id
    WHERE s.profit < 0
    GROUP BY p.category, p.sub_category
)
SELECT
    category,
    sub_category,
    loss_rows,
    total_loss,
    sales_at_loss,
    RANK() OVER (ORDER BY total_loss ASC) AS loss_rank
FROM loss
ORDER BY total_loss ASC
LIMIT 10
"""


def top_loss_makers(n: int = 10) -> pd.DataFrame:
    q = LOSS_SQL.replace("LIMIT 10", f"LIMIT {int(n)}")
    return connect().execute(q).df()


if __name__ == "__main__":
    pd.set_option("display.width", 120)
    pd.set_option("display.max_columns", 20)
    print("=== KPI Overview ===")
    print(kpi_overview().to_string(index=False))
    print("\n=== Sales by Category ===")
    print(sales_by_category().to_string(index=False))
    print("\n=== Sales by Region ===")
    print(sales_by_region().to_string(index=False))
    print("\n=== Top 5 Products ===")
    print(top_products(5).to_string(index=False))
    print("\n=== Top Loss Makers ===")
    print(top_loss_makers(5).to_string(index=False))
