# 📊 Retail Sales Business Intelligence Dashboard

An end-to-end **SQL-first** data analytics project: a flat retail CSV is modelled into a proper **relational star schema** in DuckDB, queried with production-style SQL (CTEs, window functions, joins, ranking), and surfaced through an **interactive Streamlit dashboard** — plus clean static reports.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-SQL-FFF000?logo=duckdb&logoColor=black)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)

---

## 🧠 What This Project Does

| Step | What | Code |
|------|------|------|
| 1. **Load & model** | Flat CSV → relational **star schema** (fact + 4 dimension tables) | `scripts/build_database.py` |
| 2. **SQL analytics** | KPIs via CTEs, window functions, joins, `RANK()` | `scripts/queries.py` |
| 3. **Dashboard** | Interactive BI dashboard (filters, KPI cards, charts) | `app.py` |
| 4. **Reports** | Static PNG charts + KPI JSON for reporting | `scripts/make_artifacts.py` |

---

## 📈 Key Findings (real, from the data)

- **$2.30M** total sales · **$286K** total profit · **12.5%** overall margin
- **Technology** is the top category (**36.4%** of sales), but **Furniture** has the thinnest margin
- **West** region leads sales (**31.8%**), **South** lags (**17.0%**)
- The single biggest money-loser is **Binders** ($38.5K in losses across 613 unprofitable rows)
- **1,871** order lines (about 19% of all) are sold at a loss

---

## 🗄️ Star Schema Design

```
fact_sales (9,994 rows)  ──┬── dim_customer (793 rows)
                           ├── dim_product  (1,862 rows)
                           ├── dim_location (632 rows)
                           └── dim_date     (3,472 rows)
```

Modelling the raw flat file into facts + dimensions mirrors a real analytics
warehouse and is what makes the downstream SQL clean and meaningful.

---

## 🚀 Quick Start

```bash
# 1. Create + activate environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the database (CSV -> DuckDB star schema)
python scripts/build_database.py

# 4. Run SQL analytics (prints KPIs)
python scripts/queries.py

# 5. Generate static report artifacts
python scripts/make_artifacts.py

# 6. Launch the interactive dashboard
streamlit run app.py
```

### Dependencies
```txt
pandas
duckdb
streamlit
plotly
matplotlib
seaborn
```

---

## 🧮 SQL Highlights

The analytics layer (`scripts/queries.py`) demonstrates:

- **CTEs** (`WITH monthly AS (...)`) for readable multi-step logic
- **Window functions** — `SUM() OVER (...)`, `LAG() OVER (PARTITION BY ...)`, `RANK() OVER (...)`
- **Joins** across the fact + dimension tables
- **Aggregations** with `GROUP BY`, `COUNT(DISTINCT ...)`, and `NULLIF`-guarded ratios

Example — sales share + rank per category:

```sql
WITH cat AS (
    SELECT p.category, SUM(s.sales) AS sales
    FROM fact_sales s
    JOIN dim_product p ON s.product_id = p.product_id
    GROUP BY p.category
)
SELECT
    category,
    sales,
    ROUND(sales / SUM(sales) OVER () * 100, 1) AS sales_share_pct,
    RANK() OVER (ORDER BY sales DESC) AS sales_rank
FROM cat
ORDER BY sales DESC;
```

---

## 📁 Repository Layout

```
retail-bi-dashboard/
├── app.py                       # Streamlit BI dashboard
├── scripts/
│   ├── build_database.py        # CSV -> DuckDB star schema
│   ├── queries.py               # SQL analytics layer
│   └── make_artifacts.py        # static report charts + KPI JSON
├── data/
│   ├── superstore_sales.csv     # raw data (9,994 rows)
│   └── retail.db                # built DuckDB database
├── artifacts/                   # generated PNG charts + KPI summary
└── requirements.txt
```

---

## 📊 Dataset

- **Source:** Classic "Sample Superstore" dataset (public practice data)
- **Records:** 9,994 order lines, 2014–2017
- **Fields:** order/ship dates, customer, product, category, segment, region, sales, quantity, discount, profit

---

## 📬 Contact
Built as part of a data-science portfolio — connect on [X/Twitter (@quant_bit)](https://x.com/quant_bit) or check out my [GitHub](https://github.com/Quantbit-repo).
