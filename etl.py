"""
etl.py
Mini Data Pipeline: Extract sales CSV -> Validate -> Load into SQLite
Logs every run's status into the pipeline_runs table (for monitoring/production support demo).
"""

import pandas as pd
import sqlite3
import logging
from datetime import datetime
import os

# ---------- CONFIG ----------
SOURCE_FILE = "sales_data.csv"
DB_FILE = "pipeline.db"
LOG_FILE = "pipeline.log"

# ---------- LOGGING SETUP ----------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
# also print logs to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logging.getLogger().addHandler(console)


def get_connection():
    return sqlite3.connect(DB_FILE)


def setup_tables(conn):
    """Create tables if they don't exist yet."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            order_id INTEGER PRIMARY KEY,
            date TEXT,
            product TEXT,
            quantity INTEGER,
            price REAL,
            region TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time TEXT,
            source_file TEXT,
            source_row_count INTEGER,
            loaded_row_count INTEGER,
            rejected_row_count INTEGER,
            status TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time TEXT,
            alert_type TEXT,
            message TEXT
        )
    """)
    conn.commit()


def extract(source_file):
    """Read the source CSV file."""
    if not os.path.exists(source_file):
        raise FileNotFoundError(f"Source file not found: {source_file}")
    df = pd.read_csv(source_file)
    logging.info(f"Extracted {len(df)} rows from {source_file}")
    return df


def validate_and_transform(df):
    """
    Basic data validation (first-level checks a junior data engineer would do):
    - drop rows with missing required fields
    - drop rows with negative quantity/price
    - return both clean data and rejected rows (for alerting)
    """
    original_count = len(df)

    required_cols = ["order_id", "date", "product", "quantity", "price", "region"]
    missing_mask = df[required_cols].isnull().any(axis=1)

    invalid_mask = pd.Series(False, index=df.index)
    invalid_mask |= df["quantity"].fillna(0) < 0
    invalid_mask |= df["price"].fillna(0) < 0

    reject_mask = missing_mask | invalid_mask
    rejected = df[reject_mask].copy()
    clean = df[~reject_mask].copy()

    logging.info(
        f"Validation complete: {len(clean)} valid rows, {len(rejected)} rejected rows "
        f"(out of {original_count})"
    )
    return clean, rejected


def load(conn, clean_df):
    """Load clean rows into the sales table (replace-safe: ignore duplicates)."""
    loaded = 0
    for _, row in clean_df.iterrows():
        try:
            conn.execute(
                "INSERT OR REPLACE INTO sales (order_id, date, product, quantity, price, region) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (row["order_id"], row["date"], row["product"], row["quantity"], row["price"], row["region"])
            )
            loaded += 1
        except Exception as e:
            logging.error(f"Failed to insert order_id {row['order_id']}: {e}")
    conn.commit()
    logging.info(f"Loaded {loaded} rows into sales table")
    return loaded


def log_run(conn, source_row_count, loaded_row_count, rejected_row_count, status):
    conn.execute(
        "INSERT INTO pipeline_runs (run_time, source_file, source_row_count, loaded_row_count, rejected_row_count, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), SOURCE_FILE, source_row_count, loaded_row_count, rejected_row_count, status)
    )
    conn.commit()


def raise_alert(conn, alert_type, message):
    conn.execute(
        "INSERT INTO alerts (run_time, alert_type, message) VALUES (?, ?, ?)",
        (datetime.now().isoformat(), alert_type, message)
    )
    conn.commit()
    logging.warning(f"ALERT [{alert_type}]: {message}")


def run_pipeline():
    conn = get_connection()
    setup_tables(conn)

    logging.info("===== Pipeline run started =====")
    try:
        df = extract(SOURCE_FILE)
        clean_df, rejected_df = validate_and_transform(df)
        loaded_count = load(conn, clean_df)

        status = "SUCCESS" if len(rejected_df) == 0 else "SUCCESS_WITH_WARNINGS"
        log_run(conn, len(df), loaded_count, len(rejected_df), status)

        if len(rejected_df) > 0:
            raise_alert(
                conn,
                "DATA_VALIDATION",
                f"{len(rejected_df)} row(s) rejected due to missing/invalid values. "
                f"Order IDs: {rejected_df['order_id'].tolist()}"
            )

        logging.info("===== Pipeline run finished successfully =====")

    except Exception as e:
        log_run(conn, 0, 0, 0, "FAILED")
        raise_alert(conn, "PIPELINE_FAILURE", str(e))
        logging.error(f"Pipeline failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    run_pipeline()
