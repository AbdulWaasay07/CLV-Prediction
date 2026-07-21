import pandas as pd
import random
import uuid
import numpy as np
from datetime import datetime, timedelta

NUM_CUSTOMERS = 150
print(f"Generating 'Dirty' mock data for {NUM_CUSTOMERS} customers to test the Data Cleaner Engine...")

# Helper to randomly decide if we should introduce an error
def flip_coin(probability=0.05):
    return random.random() < probability

# 1. Customers
customers = []
locations = ["New York", "San Francisco", "London", "Austin", "Berlin", "Toronto", "Sydney"]
for i in range(1, NUM_CUSTOMERS + 1):
    cid = f"CUST{i:03d}"
    
    # Introduce case inconsistency error
    if flip_coin(): cid = cid.lower()
    if flip_coin(): cid = f" {cid} "
    
    name = f"Customer {i}" if not flip_coin() else np.nan # Missing name
    location = random.choice(locations) if not flip_coin(0.1) else None # Missing location
    
    customers.append({
        "customer_id": cid,
        "name": name,
        "email": f"customer{i}@example.com",
        "phone": f"555-01{i:02d}",
        "location": location,
        "sign_up_date": (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d')
    })
pd.DataFrame(customers).to_csv("mock_customers.csv", index=False)
print("Created mock_customers.csv (with missing names, missing locations, and case inconsistencies)")

# 2. Products
products = []
for i in range(1, 11):
    price = round(random.uniform(49.99, 499.99), 2)
    if flip_coin(): price = np.nan # Missing price
    
    products.append({
        "product_id": f"PROD{i:03d}",
        "product_name": f"Enterprise Software {i}",
        "price": price
    })
pd.DataFrame(products).to_csv("mock_products.csv", index=False)
print("Created mock_products.csv (with missing prices)")

# 3. Transactions & 4. Support Tickets & 5. Behavior & 6. Marketing
transactions = []
support = []
behavior = []
marketing = []

for cust in customers:
    # Use the clean ID for relation generation so we don't break our own loop, 
    # but we'll inject dirty IDs into the child tables randomly.
    clean_cid = cust["customer_id"].strip().upper()
    
    is_at_risk = random.random() < 0.3 
    
    # Transactions
    num_purchases = random.randint(1, 3) if is_at_risk else random.randint(5, 20)
    for _ in range(num_purchases):
        prod = random.choice(products)
        
        # Inject Dirty Amount
        amt = prod["price"]
        if flip_coin(): amt = np.nan # Missing Amount
        elif flip_coin(0.01): amt = 99999999 # Extreme Outlier (should be Winsorized)
        elif flip_coin(): amt = f"${amt}" # String formatting error (should be stripped)
        
        # Inject Dirty Quantity
        qty = random.randint(1, 3)
        if flip_coin(): qty = np.nan # Missing quantity (should default to 1)
        elif flip_coin(0.02): qty = "two" # Invalid string quantity
        
        dirty_cid = clean_cid.lower() if flip_coin() else clean_cid
        
        transactions.append({
            "transaction_id": str(uuid.uuid4()),
            "customer_id": dirty_cid,
            "product_id": prod["product_id"],
            "transaction_date": (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
            "amount": amt,
            "quantity": qty,
            "payment_method": random.choice(["Credit Card", "PayPal", "Bank Transfer", "   CrEdIt CaRd   "]),
            "status": "Completed"
        })
        
    # Support Tickets
    num_tickets = random.randint(3, 8) if is_at_risk else random.randint(0, 2)
    for _ in range(num_tickets):
        dirty_cid = f" {clean_cid} " if flip_coin() else clean_cid
        
        sev = "High" if is_at_risk else random.choice(["Low", "Medium"])
        if flip_coin(): sev = sev.lower() # Case inconsistency
        if flip_coin(): sev = f" {sev} " # Whitespace inconsistency
        
        support.append({
            "ticket_id": str(uuid.uuid4()),
            "customer_id": dirty_cid,
            "issue_date": (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
            "resolution_date": (datetime.now() - timedelta(days=random.randint(0, 5))).strftime('%Y-%m-%d') if not flip_coin() else np.nan, # Missing resolution date
            "category": random.choice(["Billing", "Technical", "Account"]),
            "severity": sev,
            "status": "Resolved",
            "csat_score": random.randint(1, 3) if is_at_risk else random.randint(4, 5)
        })
        
    # Behavior
    num_sessions = random.randint(10, 20) if is_at_risk else random.randint(50, 200)
    for _ in range(5):
        duration = random.randint(30, 120) if is_at_risk else random.randint(300, 900)
        if flip_coin(): duration = np.nan # Missing duration (should be imputed with median)
        
        views = int((num_sessions * random.randint(2, 5)) / 5)
        if flip_coin(0.02): views = -10 # Impossible negative value
        
        behavior.append({
            "behavior_id": str(uuid.uuid4()),
            "customer_id": clean_cid,
            "log_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
            "website_visits": int(num_sessions / 5),
            "app_sessions": int(num_sessions / 5),
            "page_views": views,
            "avg_session_duration": duration
        })
        
    # Marketing
    for _ in range(random.randint(2, 5)):
        # Deliberately remove interaction_id sometimes to test UUID auto-generation in Data Cleaner
        interaction_id = str(uuid.uuid4()) if not flip_coin(0.3) else np.nan
        
        marketing.append({
            "interaction_id": interaction_id,
            "customer_id": clean_cid.lower() if flip_coin() else clean_cid,
            "campaign_id": f"CAMP{random.randint(1,10):03d}",
            "channel": random.choice(["Email", "Social Media", "Search", "Webinar", " eMail "]),
            "send_date": (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d'),
            "opened": random.choice([True, False]),
            "clicked": random.choice([True, False]) if not is_at_risk else False,
            "converted": random.choice([True, False]) if not is_at_risk else False
        })

pd.DataFrame(transactions).to_csv("mock_transactions.csv", index=False)
print("Created mock_transactions.csv (with outliers, missing amounts, bad currency formats, and case issues)")

pd.DataFrame(support).to_csv("mock_support.csv", index=False)
print("Created mock_support.csv (with whitespace errors, missing dates)")

pd.DataFrame(behavior).to_csv("mock_behavior.csv", index=False)
print("Created mock_behavior.csv (with missing durations and negative views)")

pd.DataFrame(marketing).to_csv("mock_marketing.csv", index=False)
print("Created mock_marketing.csv (with MISSING Primary Keys to test auto-generation)")

print("\nSuccess! 'Dirty' CSV files generated. Time to break the Data Cleaner!")
