import os, json, requests, psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ["postgresql://neondb_owner:npg_uxBcOyEInw23@ep-old-grass-ahacuyb0.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"])
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS bronze.weather_raw (
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
    "INSERT INTO bronze.weather_raw (payload, ingested_at) VALUES (%s, %s)",
    [json.dumps(resp.json()), datetime.now(timezone.utc)]
)
conn.commit()
cur.close()
conn.close()
print("Inserted 1 row into bronze.weather_raw")