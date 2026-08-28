"""
queries.py
"""

import sqlite3
import pandas as pd

DB_FILE = "pipeline.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def source_to_target_reconciliation():
    """
    Compares latest run's source row count vs loaded row count vs rejected count.
    This is the classic 'reconciliation check' mentioned in the JD.
    """
    query = """
        SELECT
            run_id,
            run_time,
            source_row_count,
            loaded_row_count,
            rejected_row_count,
            (source_row_count - loaded_row_count - rejected_row_count) AS unexplained_diff,
            status
        FROM pipeline_runs
        ORDER BY run_time DESC
        LIMIT 1
    """
    return pd.read_sql(query, get_connection())


def failed_runs_summary():
    """Summary of failed / warning runs - for daily status reporting."""
    query = """
        SELECT
            status,
            COUNT(*) AS run_count
        FROM pipeline_runs
        GROUP BY status
        ORDER BY run_count DESC
    """
    return pd.read_sql(query, get_connection())


def daily_pipeline_health_report():
    """Daily health report - how many rows processed/rejected per run."""
    query = """
        SELECT
            DATE(run_time) AS run_date,
            COUNT(*) AS total_runs,
            SUM(source_row_count) AS total_source_rows,
            SUM(loaded_row_count) AS total_loaded_rows,
            SUM(rejected_row_count) AS total_rejected_rows
        FROM pipeline_runs
        GROUP BY DATE(run_time)
        ORDER BY run_date DESC
    """
    return pd.read_sql(query, get_connection())


def recent_alerts(limit=10):
    """Latest alerts - what an on-call engineer would check first."""
    query = """
        SELECT run_time, alert_type, message
        FROM alerts
        ORDER BY run_time DESC
        LIMIT ?
    """
    return pd.read_sql(query, get_connection(), params=(limit,))


def sales_summary_by_region():
    """Basic operational reporting example - revenue by region from loaded data."""
    query = """
        SELECT
            region,
            COUNT(*) AS total_orders,
            SUM(quantity) AS total_quantity,
            SUM(quantity * price) AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
    """
    return pd.read_sql(query, get_connection())


if __name__ == "__main__":
    print("=== Source-to-Target Reconciliation ===")
    print(source_to_target_reconciliation().to_string(index=False))

    print("\n=== Failed Runs Summary ===")
    print(failed_runs_summary().to_string(index=False))

    print("\n=== Daily Pipeline Health Report ===")
    print(daily_pipeline_health_report().to_string(index=False))

    print("\n=== Recent Alerts ===")
    print(recent_alerts().to_string(index=False))

    print("\n=== Sales Summary by Region ===")
    print(sales_summary_by_region().to_string(index=False))
