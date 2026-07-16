import os,json,requests,psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
import pandas as pd
import uuid
import io
#from pathlib import Path

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(SCRIPT_DIR, "data", "address_src.csv")



#SCRIPT_DIR = Path(__file__).resolve().parent
#csv_path = SCRIPT_DIR / "data" / "address_src.csv"


table_name = "flipkart_raw.address_raw"
run_id = str(uuid.uuid4())
batch_id = str(uuid.uuid4())
created_by = "python_ingestion_script"


def build_dataframe_from_csv(csv_path):
    dataset = pd.read_csv(csv_path)
    dataset['run_id'] = run_id
    dataset['batch_id'] = batch_id
    dataset['dw_created_by'] = created_by
    dataset['dw_modified_by'] = created_by
    dataset['dw_created_date'] = datetime.now(timezone.utc)
    dataset['dw_modified_date'] = datetime.now(timezone.utc)
    return dataset

def load_to_postgres(dataset: pd.DataFrame):
    conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    dbname=os.environ["DB_NAME"],
    sslmode="require",
    )
    cur = conn.cursor()

    try:
        cur.execute(f"TRUNCATE TABLE {table_name};")

        buffer = io.StringIO()
        dataset.to_csv(buffer, index=False, header=True)
        buffer.seek(0)

        columns_sql = ", ".join(dataset.columns)

        copy_sql = f"""
                COPY {table_name} ({columns_sql})
                FROM STDIN
                WITH (FORMAT csv, HEADER true)
            """
        cur.copy_expert(copy_sql, buffer)

        conn.commit()
        print(f"Loaded {len(dataset)} rows into {table_name}. batch_id={batch_id}")

    except Exception as e:
        conn.rollback()
        print(f"Load failed, rolled back. Error: {e}")
        raise

    finally:
        conn.close()
if __name__ == "__main__":
    dataset = build_dataframe_from_csv(csv_path)
    load_to_postgres(dataset)