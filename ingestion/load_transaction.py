import pandas as pd, os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()
 
engine = create_engine(f"postgresql://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}:{os.getenv('PGPORT','5432')}/{os.getenv('PGDATABASE')}?sslmode=require")
df = pd.read_csv("data/transaction.csv", dtype=str, keep_default_na=False)
df["transaction_date"] = pd.to_datetime(df["transaction_date"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
df["load_ts"] = pd.Timestamp.now("UTC")
df = df.replace("", None)
 
with engine.begin() as conn:
    conn.execute(text("TRUNCATE raw_lok.transaction"))
    df.to_sql("transaction", conn, schema="raw_lok", if_exists="append", index=False)
print(f"Loaded {len(df)} rows into raw_lok.transaction")