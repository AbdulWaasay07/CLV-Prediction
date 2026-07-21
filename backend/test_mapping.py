import pandas as pd
import json
import uuid
import math
from app.db.database import SessionLocal
from app.db import models

# simulate chunk from upload
data = {
    'campaign_id': ['M001'],
    'customer_id': ['cust001'],
    'campaign_name': ['Summer Sale'],
    'channel': ['email'],
    'date_sent': ['2026-06-01'],
    'opened': [True],
    'clicked': [True],
    'converted': [True]
}
chunk = pd.DataFrame(data)

# simulate what happens in process_file_in_chunks
column_mapping = {"date_sent": "send_date"}
if column_mapping:
    clean_mapping = {str(k).lower().strip(): str(v).lower().strip() for k, v in column_mapping.items()}
    chunk = chunk.rename(columns=clean_mapping)

if 'send_date' in chunk.columns:
    chunk['send_date'] = pd.to_datetime(chunk['send_date'], errors='coerce')

if 'interaction_id' not in chunk.columns or chunk['interaction_id'].isnull().all():
    chunk['interaction_id'] = [str(uuid.uuid4()) for _ in range(len(chunk))]

# simulate _generic_cleaning
chunk.columns = chunk.columns.str.lower().str.strip()

records = chunk.to_dict(orient="records")
for record in records:
    for key, value in record.items():
        if isinstance(value, float) and math.isnan(value):
            record[key] = None

print("KEYS AFTER CLEANING:", list(records[0].keys()))

db = SessionLocal()
try:
    db.bulk_insert_mappings(models.MarketingCampaign, records)
    db.commit()
    print("SUCCESS")
except Exception as e:
    print("ERROR:", e)
finally:
    db.close()
