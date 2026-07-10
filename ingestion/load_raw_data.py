import os, json, requests, psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    sslmode="require"   # Neon requires SSL
)
cur = conn.cursor()

cur.execute("""
    CREATE SCHEMA IF NOT EXISTS raw;
    CREATE TABLE IF NOT EXISTS raw.weather_raw (
        id SERIAL PRIMARY KEY,
        payload JSONB,
        ingested_at TIMESTAMPTZ
    )
""")

resp = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={"latitude": 28.6, "longitude": 77.4, "current": "temperature_2m,wind_speed_10m"}
)
resp.raise_for_status()

cur.execute(
    "INSERT INTO raw.weather_raw (payload, ingested_at) VALUES (%s, %s)",
    [json.dumps(resp.json()), datetime.now(timezone.utc)]
)
conn.commit()
cur.close()
conn.close()
print("Inserted 1 row into raw.weather_raw")