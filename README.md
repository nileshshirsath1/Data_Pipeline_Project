# Data Pipeline Project (Mini Project)

A small end-to-end project simulating a **Data Support** workflow:
extracting data, validating it, loading it into a database, tracking pipeline run history,
raising alerts on bad data, and monitoring everything through a dashboard.

## Why this project

Built to demonstrate core skills relevant to data engineering support roles:
- Basic SQL & data validation
- ETL/ELT concepts (Extract → Validate → Load)
- Pipeline monitoring & first-level checks
- Source-to-target reconciliation
- Incident/alert tracking (similar to ticket-based systems like ServiceNow)
- Documentation & operational reporting

## Tech Stack
- **Python** (pandas) — ETL logic
- **SQLite** — lightweight database for run history, alerts, and loaded data
- **Streamlit** — monitoring dashboard UI

## Project Structure
```
data-pipeline-project/
├── sales_data.csv     # sample source data (includes some bad rows on purpose)
├── etl.py             # Extract -> Validate -> Load, with logging
├── queries.py         # SQL queries: reconciliation, health report, alerts
├── dashboard.py        # Streamlit dashboard (UI on top of queries.py)
├── pipeline.db         # SQLite DB (created automatically after first run)
├── pipeline.log        # log file (created automatically)
└── README.md
```

## How to Run

1. Install dependencies:
   ```
   pip install pandas streamlit
   ```

2. Run the ETL pipeline (loads data + creates tables):
   ```
   python etl.py
   ```

3. Check SQL queries directly (optional):
   ```
   python queries.py
   ```

4. Launch the dashboard:
   ```
   streamlit run dashboard.py
   ```
   Opens in browser — click **"Run Pipeline Now"** to re-run the ETL anytime.

## What It Demonstrates

| JD Requirement | How this project covers it |
|---|---|
| Basic SQL | `queries.py` — reconciliation, aggregation, grouping queries |
| ETL/ELT concepts | `etl.py` — extract, validate/transform, load stages |
| Pipeline monitoring | `pipeline_runs` table + dashboard run history |
| First-level checks / data validation | Null checks, negative value checks, row rejection logic |
| Source-to-target reconciliation | `source_to_target_reconciliation()` query |
| Incident/alert tracking | `alerts` table — logged like a ticketing system |
| Documentation | This README + inline code comments |
| Operational reporting | Daily health report + sales summary by region |

## Sample Data Notes
`sales_data.csv` intentionally includes a few bad rows (missing quantity, missing price,
negative quantity) to demonstrate the validation and alerting logic working correctly.


