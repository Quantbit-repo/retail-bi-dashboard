"""
Retail BI Dashboard — Load raw CSV into DuckDB as a star schema.

Raw CSV is a flat, denormalised file (9,994 rows x 21 cols). We model it
into a proper relational star schema:

    fact_sales      — one row per order line (measures: sales, qty, discount, profit)
    dim_customer    — customer id, name, segment
    dim_product     — product id, name, category, sub-category
    dim_location    — city, state, region, postal code, country
    dim_date        — order/ship date with derived calendar fields

This mirrors how a real BI/analytics warehouse is structured and lets us
write clean, meaningful SQL against it.
"""

import pathlib

import duckdb
import pandas as pd

DATA = pathlib.Path("data")
DB_PATH = DATA / "retail.db"
RAW = DATA / "superstore_sales.csv"


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW, encoding="latin-1")
    # Parse dates up front (keep as string in CSV; DuckDB will cast)
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")
    return df


def build_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("DROP TABLE IF EXISTS fact_sales")
    con.execute("DROP TABLE IF EXISTS dim_customer")
    con.execute("DROP TABLE IF EXISTS dim_product")
    con.execute("DROP TABLE IF EXISTS dim_location")
    con.execute("DROP TABLE IF EXISTS dim_date")

    con.execute("""
        CREATE TABLE dim_customer AS
        SELECT DISTINCT
            "Customer ID"   AS customer_id,
            "Customer Name" AS customer_name,
            "Segment"       AS segment
        FROM raw_sales
    """)

    # The source CSV reuses a Product ID for more than one product name (32 ids).
    # A straight DISTINCT therefore leaves duplicate keys and any join to this
    # dimension inflates measures. Keep one row per product_id, using the most
    # frequent name. All duplicates agree on category and sub category, so no
    # category level analysis changes.
    con.execute("""
        CREATE TABLE dim_product AS
        WITH counts AS (
            SELECT
                "Product ID"   AS product_id,
                "Product Name" AS product_name,
                "Category"     AS category,
                "Sub-Category" AS sub_category,
                COUNT(*)       AS name_count
            FROM raw_sales
            GROUP BY 1, 2, 3, 4
        ),
        ranked AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY product_id
                       ORDER BY name_count DESC, product_name
                   ) AS rn
            FROM counts
        )
        SELECT product_id, product_name, category, sub_category
        FROM ranked
        WHERE rn = 1
    """)

    con.execute("""
        CREATE TABLE dim_location AS
        SELECT DISTINCT
            "Postal Code" AS postal_code,
            "City"        AS city,
            "State"       AS state,
            "Region"      AS region,
            "Country"     AS country
        FROM raw_sales
    """)

    con.execute("""
        CREATE TABLE dim_date AS
        SELECT DISTINCT
            "Order Date" AS order_date,
            "Ship Date"  AS ship_date,
            CAST(strftime("Order Date", '%Y') AS INT)    AS order_year,
            CAST(strftime("Order Date", '%m') AS INT)    AS order_month,
            CAST(strftime("Order Date", '%d') AS INT)    AS order_day,
            strftime("Order Date", '%Y-%m')              AS order_year_month
        FROM raw_sales
    """)

    con.execute("""
        CREATE TABLE fact_sales AS
        SELECT
            "Row ID"      AS order_line_id,
            "Order ID"    AS order_id,
            "Order Date"  AS order_date,
            "Ship Date"   AS ship_date,
            "Ship Mode"   AS ship_mode,
            "Customer ID" AS customer_id,
            "Product ID"  AS product_id,
            "Postal Code" AS postal_code,
            "Sales"       AS sales,
            "Quantity"    AS quantity,
            "Discount"    AS discount,
            "Profit"      AS profit
        FROM raw_sales
    """)


def main() -> None:
    df = load_raw()
    con = duckdb.connect(str(DB_PATH))
    con.register("raw_sales", df)
    build_schema(con)

    # Report row counts
    counts = {}
    for t in ["fact_sales", "dim_customer", "dim_product", "dim_location", "dim_date"]:
        counts[t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]

    print("Star schema built in", DB_PATH)
    for t, c in counts.items():
        print(f"  {t:14s} {c:,} rows")

    con.close()


if __name__ == "__main__":
    main()
