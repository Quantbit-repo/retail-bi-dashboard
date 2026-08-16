"""
Retail BI Dashboard — Generate static artifacts for the X thread & README.

Reads real numbers straight from the DuckDB SQL layer (queries.py) and renders
clean PNG charts + a KPI summary JSON. Nothing is hard-coded — every value
comes from the database.
"""

import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts"))
import queries  # noqa: E402

OUT = pathlib.Path("artifacts")
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

PALETTE = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#6A994E"]


def chart_monthly_trend() -> str:
    m = queries.monthly_trend()
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(m["ym"], m["sales"], label="Sales", linewidth=2, color=PALETTE[0])
    ax.plot(m["ym"], m["profit"], label="Profit", linewidth=2, color=PALETTE[1])
    ax.set_title("Sales & Profit Over Time (monthly, 2014–2017)", fontweight="bold")
    ax.set_ylabel("USD ($)")
    ax.legend(frameon=False)
    ax.set_xticks(m["ym"][::6])
    fig.tight_layout()
    p = OUT / "monthly_trend.png"
    fig.savefig(p)
    plt.close(fig)
    return str(p)


def chart_category() -> str:
    c = queries.sales_by_category()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(c["category"], c["sales"], color=PALETTE[:3])
    for bar, share in zip(bars, c["sales_share_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15000,
                f"{share}%", ha="center", fontweight="bold")
    ax.set_title("Sales by Category", fontweight="bold")
    ax.set_ylabel("Sales ($)")
    fig.tight_layout()
    p = OUT / "sales_by_category.png"
    fig.savefig(p)
    plt.close(fig)
    return str(p)


def chart_region() -> str:
    r = queries.sales_by_region()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(r["region"], r["sales"], color=PALETTE[:4])
    for bar, share in zip(bars, r["sales_share_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10000,
                f"{share}%", ha="center", fontweight="bold")
    ax.set_title("Sales by Region", fontweight="bold")
    ax.set_ylabel("Sales ($)")
    fig.tight_layout()
    p = OUT / "sales_by_region.png"
    fig.savefig(p)
    plt.close(fig)
    return str(p)


def chart_loss_makers() -> str:
    lm = queries.top_loss_makers(10)
    lm = lm.sort_values("total_loss")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(lm["sub_category"], lm["total_loss"], color=PALETTE[3])
    ax.set_title("Where Money Is Lost (top loss-makers)", fontweight="bold")
    ax.set_xlabel("Total Loss ($)")
    fig.tight_layout()
    p = OUT / "loss_makers.png"
    fig.savefig(p)
    plt.close(fig)
    return str(p)


def kpi_summary() -> str:
    k = queries.kpi_overview().iloc[0]
    data = {col: (None if pd.isna(k[col]) else k[col]) for col in k.index}
    # Convert numpy types to native for JSON
    out = {}
    for key, val in data.items():
        if hasattr(val, "item"):
            val = val.item()
        out[key] = val
    p = OUT / "kpi_summary.json"
    with open(p, "w") as f:
        json.dump(out, f, indent=2)
    return str(p)


def main() -> None:
    paths = [
        chart_monthly_trend(),
        chart_category(),
        chart_region(),
        chart_loss_makers(),
        kpi_summary(),
    ]
    print("Generated artifacts:")
    for p in paths:
        print(f"  {p}")

    # Print KPI for the thread
    k = queries.kpi_overview().iloc[0]
    print("\nKPI snapshot:")
    for col in k.index:
        print(f"  {col}: {k[col]}")


if __name__ == "__main__":
    main()
