from hashlib import sha256
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    port=os.getenv('DB_PORT', 5432),
    database=os.getenv('DB_NAME', 'whale_tracker'),
    user=os.getenv('DB_USER', 'sean'),
    password=os.getenv('DB_PASSWORD', 'whale123')
)
cursor = conn.cursor()
cursor.execute("SELECT charge_id, amount FROM donations WHERE type='crypto'")
for row in cursor:
    charge_id, amount = row
    checksum = sha256(f"{charge_id}:{amount}".encode()).hexdigest()
    with open('/mnt/bridge/core_data_backups/donations.sha256', 'a') as f:
        f.write(f"{charge_id}:{checksum}\n")
conn.close()
