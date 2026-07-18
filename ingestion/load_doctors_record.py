import pandas as pd, os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()
 
engine = create_engine(f"postgresql://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}:{os.getenv('PGPORT','5432')}/{os.getenv('PGDATABASE')}?sslmode=require")
df = pd.read_csv("data/doctors_record.csv", dtype=str, keep_default_na=False)
df["load_ts"] = pd.Timestamp.now("UTC")
df = df.replace("", None)
 
with engine.begin() as conn:
    conn.execute(text("TRUNCATE raw_lok.doctors_record"))
    df.to_sql("doctors_record", conn, schema="raw_lok", if_exists="append", index=False)
print(f"Loaded {len(df)} rows into raw_lok.doctors_record")