"""
Retail BI Dashboard — Streamlit App

Interactive business-intelligence dashboard over the DuckDB star schema.
Run with:  streamlit run app.py
"""

import sys
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Allow importing our queries module
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import queries  # noqa: E402

st.set_page_config(page_title="Retail BI Dashboard", layout="wide",
                   page_icon="📊")

# --------------------------------------------------------------------------- #
# Sidebar filters
# --------------------------------------------------------------------------- #
st.sidebar.title("🎛️ Filters")

con = queries.connect()
regions = con.execute("SELECT DISTINCT region FROM dim_location ORDER BY region").df()["region"].tolist()
categories = con.execute("SELECT DISTINCT category FROM dim_product ORDER BY category").df()["category"].tolist()

sel_region = st.sidebar.selectbox("Region", ["All"] + regions)
sel_category = st.sidebar.selectbox("Category", ["All"] + categories)
sel_segment = st.sidebar.selectbox(
    "Segment",
    ["All"] + con.execute("SELECT DISTINCT segment FROM dim_customer ORDER BY segment").df()["segment"].tolist(),
)
con.close()

st.title("📊 Retail Sales Business Intelligence")
st.caption("Superstore data · 9,994 order lines · 2014–2017 · powered by DuckDB + SQL")

# --------------------------------------------------------------------------- #
# KPI cards
# --------------------------------------------------------------------------- #
kpi = queries.kpi_overview().iloc[0]
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Sales", f"${kpi['total_sales']:,.0f}")
c2.metric("Total Profit", f"${kpi['total_profit']:,.0f}")
c3.metric("Orders", f"{kpi['total_orders']:,}")
c4.metric("Units Sold", f"{kpi['total_units']:,.0f}")
c5.metric("Profit Margin", f"{kpi['profit_margin_pct']:.1f}%")
c6.metric("Avg Discount", f"{kpi['avg_discount_pct']:.1f}%")

st.markdown("---")

# --------------------------------------------------------------------------- #
# Row 1: Monthly trend + category
# --------------------------------------------------------------------------- #
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📈 Sales & Profit Over Time")
    m = queries.monthly_trend()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m["ym"], y=m["sales"], name="Sales",
                             mode="lines", line=dict(color="#2E86AB", width=2)))
    fig.add_trace(go.Scatter(x=m["ym"], y=m["profit"], name="Profit",
                             mode="lines", line=dict(color="#A23B72", width=2)))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.15),
                      xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🏷️ Sales by Category")
    cat = queries.sales_by_category()
    fig = px.bar(cat, x="category", y="sales", color="category",
                 text="sales_share_pct", color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      yaxis_title="Sales ($)")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------- #
# Row 2: Region + segment trend
# --------------------------------------------------------------------------- #
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🗺️ Sales by Region")
    reg = queries.sales_by_region()
    fig = px.bar(reg, x="region", y="sales", color="region",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      yaxis_title="Sales ($)")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("👥 Segment Year-over-Year Growth")
    seg = queries.segment_trend()
    fig = px.line(seg, x="yr", y="sales", color="segment", markers=True,
                  color_discrete_sequence=px.colors.qualitative.Set1)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(orientation="h", y=1.15), xaxis_title="Year")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------- #
# Row 3: Top products + loss makers
# --------------------------------------------------------------------------- #
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏆 Top 10 Products by Sales")
    tp = queries.top_products(10)
    fig = px.bar(tp.sort_values("sales"), x="sales", y="product_name",
                 orientation="h", color="category",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      yaxis_title=None, xaxis_title="Sales ($)", height=420)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🔻 Where We Lose Money")
    lm = queries.top_loss_makers(10)
    lm["display"] = lm["category"] + " — " + lm["sub_category"]
    fig = px.bar(lm.sort_values("total_loss", ascending=False), x="total_loss",
                 y="display", orientation="h", color="total_loss",
                 color_continuous_scale="Reds")
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      yaxis_title=None, xaxis_title="Total Loss ($)", height=420)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Built with Streamlit + Plotly · SQL on DuckDB star schema · "
           "Educational portfolio project — not financial advice.")
