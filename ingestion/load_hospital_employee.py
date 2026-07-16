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

TABLE_NAME = "hospital_employee"
CSV_FILENAME = "hospital_employee.csv"
LOAD_MODE = "truncate"  # truncate | append


def get_connection():
    missing = [k for k, v in PG_CONFIG.items() if v in (None, "") and k != "sslmode"]
    if missing:
        raise RuntimeError(f"Missing Postgres connection settings: {missing}")
    return psycopg2.connect(**PG_CONFIG)


def load_table(conn, run_id, batch_id):
    csv_path = os.path.join(DATA_DIR, CSV_FILENAME)
    print(f"Reading {csv_path} ...")

    df = pd.read_csv(csv_path, dtype=str)

    now = datetime.now(timezone.utc)
    df["load_ts"] = now
    df["modified_ts"] = now
    df["created_by"] = CREATED_BY
    df["modified_by"] = CREATED_BY
    df["run_id"] = run_id
    df["batch_id"] = batch_id

    df = df.where(pd.notnull(df), None)

    columns = list(df.columns)
    rows = [
        tuple(None if isinstance(v, float) and pd.isna(v) else v for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    with conn.cursor() as cur:
        if LOAD_MODE == "truncate":
            cur.execute(f"TRUNCATE {SCHEMA}.{TABLE_NAME};")
            print(f"  Truncated {SCHEMA}.{TABLE_NAME}")

        col_list = ", ".join(columns)
        insert_sql = f"INSERT INTO {SCHEMA}.{TABLE_NAME} ({col_list}) VALUES %s"
        execute_values(cur, insert_sql, rows, page_size=500)

    conn.commit()
    print(f"  Loaded {len(rows)} rows into {SCHEMA}.{TABLE_NAME} ({LOAD_MODE})")


def main():
    run_id = str(uuid.uuid4())
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    print(f"Starting ingestion for {TABLE_NAME}  run_id={run_id}  batch_id={batch_id}")

    conn = get_connection()
    try:
        load_table(conn, run_id, batch_id)
    finally:
        conn.close()

    print("Ingestion complete.")


if __name__ == "__main__":
    main()
