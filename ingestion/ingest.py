import os
import uuid
from datetime import datetime, timezone

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

PG_CONFIG = {
    "host": os.getenv("PGHOST"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "sslmode": "require",
}

SCHEMA = "raw_lok"
CREATED_BY = "python_ingest"
DATA_DIR = "data"

# table_name, csv_filename, load_mode ("truncate" wipes table first, "append" keeps existing rows)
TABLES = [
    ("hospital_employee", "hospital_employee.csv", "truncate"),
    ("doctors_record",    "doctors_record.csv",    "truncate"),
    ("patient",            "patient.csv",           "truncate"),
    ("transaction",        "transaction.csv",       "append"),
]

print("TABLES TO PROCESS:", TABLES)


def get_connection():
    missing = [k for k, v in PG_CONFIG.items() if v in (None, "") and k != "sslmode"]
    if missing:
        raise RuntimeError(f"Missing Postgres connection settings: {missing}")
    return psycopg2.connect(**PG_CONFIG)


def load_table(conn, table_name, csv_filename, load_mode, run_id, batch_id):
    csv_path = os.path.join(DATA_DIR, csv_filename)
    print(f"Reading {csv_path} ...")

    # dtype=str + keep_default_na=False keeps the file EXACTLY as-is:
    # no type coercion, no NaN interpretation of blank strings, no dedup, no cleaning.
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    # Only lineage/metadata columns are added — no changes to the actual data values.
    now = datetime.now(timezone.utc)
    df["load_ts"] = now
    df["modified_ts"] = now
    df["created_by"] = CREATED_BY
    df["modified_by"] = CREATED_BY
    df["run_id"] = run_id
    df["batch_id"] = batch_id

    # Convert missing-value placeholders to real SQL NULL. This is NOT a data
    # change — it's required so typed columns (date/numeric) can accept them.
    # A literal text "NaN"/"NA"/"null" cannot be inserted into a DATE or NUMERIC
    # column; Postgres needs an actual NULL. The real data values are untouched.
    # Done at row-build time (not via df.map/df.replace) because pandas silently
    # converts a returned None back into float NaN when writing into an object
    # column — that was the actual cause of the "NaN"::float8 insert errors.
    MISSING_MARKERS = {"", "nan", "na", "n/a", "null", "none"}

    def _to_null(v):
        if v is None:
            return None
        if isinstance(v, float) and pd.isna(v):
            return None
        if isinstance(v, str) and v.strip().lower() in MISSING_MARKERS:
            return None
        return v

    columns = list(df.columns)
    rows = [tuple(_to_null(v) for v in row) for row in df.itertuples(index=False, name=None)]

    with conn.cursor() as cur:
        if load_mode == "truncate":
            cur.execute(f"TRUNCATE {SCHEMA}.{table_name};")
            print(f"  Truncated {SCHEMA}.{table_name}")

        col_list = ", ".join(columns)
        insert_sql = f"INSERT INTO {SCHEMA}.{table_name} ({col_list}) VALUES %s"
        execute_values(cur, insert_sql, rows, page_size=500)

    conn.commit()
    print(f"  Loaded {len(rows)} rows into {SCHEMA}.{table_name} ({load_mode}) — no dedup/cleaning applied")


def main():
    run_id = str(uuid.uuid4())
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"Starting RAW ingestion  run_id={run_id}  batch_id={batch_id}")

    conn = get_connection()
    try:
        for table_name, csv_filename, load_mode in TABLES:
            load_table(conn, table_name, csv_filename, load_mode, run_id, batch_id)
    finally:
        conn.close()

    print("Raw ingestion complete.")


if __name__ == "__main__":
    main()
