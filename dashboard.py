"""
dashboard.py
Streamlit dashboard for the mini data pipeline monitoring project.
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import sqlite3
import subprocess
import sys

from queries import (
    source_to_target_reconciliation,
    failed_runs_summary,
    daily_pipeline_health_report,
    recent_alerts,
    sales_summary_by_region,
)

DB_FILE = "pipeline.db"

st.set_page_config(page_title="Data Pipeline Monitoring Dashboard", layout="wide")

st.title("📊 Data Pipeline Monitoring Dashboard")
st.caption("Mini project simulating a data engineering support/monitoring workflow")

# ---------- Run Pipeline Button ----------
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("▶️ Run Pipeline Now"):
        with st.spinner("Running ETL pipeline..."):
            result = subprocess.run([sys.executable, "etl.py"], capture_output=True, text=True)
        st.success("Pipeline run complete!")
        st.text(result.stdout[-500:] if result.stdout else "No output captured.")

st.divider()

# ---------- Helper to safely load data ----------
def safe_query(fn):
    try:
        return fn()
    except Exception as e:
        st.warning(f"No data yet — run the pipeline first. ({e})")
        return pd.DataFrame()

# ---------- Pipeline Run History ----------
st.subheader("Pipeline Run History")
conn = sqlite3.connect(DB_FILE)
try:
    runs_df = pd.read_sql("SELECT * FROM pipeline_runs ORDER BY run_time DESC", conn)
except Exception:
    runs_df = pd.DataFrame()
conn.close()

if not runs_df.empty:
    st.dataframe(runs_df, use_container_width=True)

    # Success vs Failure chart
    status_counts = runs_df["status"].value_counts()
    st.bar_chart(status_counts)
else:
    st.info("No pipeline runs yet. Click 'Run Pipeline Now' to get started.")

st.divider()

# ---------- Alerts Panel ----------
st.subheader("🚨 Alerts")
alerts_df = safe_query(recent_alerts)
if not alerts_df.empty:
    for _, row in alerts_df.iterrows():
        st.error(f"[{row['alert_type']}] {row['message']}  \n*{row['run_time']}*")
else:
    st.success("No active alerts.")

st.divider()

# ---------- Reconciliation ----------
st.subheader("🔍 Source-to-Target Reconciliation (Latest Run)")
recon_df = safe_query(source_to_target_reconciliation)
if not recon_df.empty:
    st.dataframe(recon_df, use_container_width=True)

st.divider()

# ---------- Daily Health Report ----------
st.subheader("📅 Daily Pipeline Health Report")
health_df = safe_query(daily_pipeline_health_report)
if not health_df.empty:
    st.dataframe(health_df, use_container_width=True)

st.divider()

# ---------- Sales Summary (operational reporting example) ----------
st.subheader("💰 Sales Summary by Region (loaded data)")
sales_df = safe_query(sales_summary_by_region)
if not sales_df.empty:
    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(sales_df, use_container_width=True)
    with c2:
        st.bar_chart(sales_df.set_index("region")["total_revenue"])
