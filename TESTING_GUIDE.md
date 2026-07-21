# Comprehensive Testing Guide: Customer Intelligence Platform

This guide outlines exactly how to manually test the entire end-to-end platform, what behaviors to expect, and how the system handles critical edge cases (bad data).

---

## 1. The Data Importer & Cleaning Engine
**What it does:** Accepts raw CSV files, maps columns, cleans data (imputation, winsorization), and inserts it into MySQL.

### Test A: Happy Path (Perfect Data)
1. **How to test:** Go to the React App $\rightarrow$ "Data Importer" tab. Select "CUSTOMERS". Upload the original `customers.csv` and click **Run Upload**.
2. **What to expect:** The UI will say `Success! Inserted X rows`.
3. **Verification:** Check MySQL: `SELECT * FROM customers;`. Data should be populated perfectly.

### Test B: Missing Primary Keys (Edge Case)
1. **How to test:** Select "MARKETING" in the dropdown. Upload a marketing CSV that does *not* contain an `interaction_id` column.
2. **What to expect:** The backend `DataCleanerService` will detect the missing primary key, automatically generate a `UUID` for every row, and successfully insert the data without crashing the database.
3. **Verification:** Check MySQL: `SELECT * FROM marketing_campaigns;`. Notice the auto-generated long string IDs.

### Test C: Missing Numeric Values (Edge Case)
1. **How to test:** Open your `transactions.csv` in a text editor. Delete the `amount` value for one of the rows (leave it blank, e.g., `...,2024-01-01,,1,Credit Card,...`). Upload it.
2. **What to expect:** The backend will replace that blank value with the **median** transaction amount of the rest of the dataset.
3. **Verification:** Check MySQL. The row will be successfully inserted with an amount like `$13.50` instead of `NULL` or crashing.

### Test D: Extreme Outliers (Edge Case)
1. **How to test:** Edit `transactions.csv`. Make one purchase amount outrageously high: `99999999`. Upload it.
2. **What to expect:** The backend applies **Winsorization**. It calculates the 99th percentile of all normal purchases and caps your massive number at that ceiling.
3. **Verification:** Check MySQL. Your `99999999` transaction will have been clamped down to a reasonable maximum (e.g., `$480` or similar depending on the dataset).

---

## 2. The Feature Engineering Engine
**What it does:** Flattens thousands of relational logs (transactions, tickets, behavior) into 24 mathematical columns per customer.

### Test A: Generating the Features
1. **How to test:** Open Swagger (`http://localhost:8000/docs`). Execute `POST /api/ml/calculate-features`.
2. **What to expect:** `{"status": "success", "features_generated": 3}`.
3. **Verification:** Check MySQL: `SELECT customer_id, customer_health_score, total_sessions FROM customer_features;`.

### Test B: Case Insensitivity (Edge Case)
1. **How to test:** Ensure a transaction was uploaded for `cust001` (lowercase) and the customer account is `CUST001` (uppercase). Run the Feature Engine.
2. **What to expect:** The engine will successfully merge them. The `total_monetary_value` for `CUST001` will accurately reflect the purchases of `cust001`.
3. **Why this matters:** Pandas merges are highly case-sensitive. We built strict standardization (`.astype(str).str.lower().str.strip()`) to prevent data loss.

---

## 3. Exploratory Data Analysis (EDA) Dashboard
**What it does:** Provides high-level business intelligence.

### Test A: SQL Joins on the Fly
1. **How to test:** Go to the React App $\rightarrow$ "EDA Dashboard" tab.
2. **What to expect:** You will see 4 KPI cards and 4 charts. 
3. **Verification:** Look at the "Marketing Channel ROI" chart. This chart proves the backend is successfully performing a massive 3-table `SQL JOIN` on the fly (joining `marketing_campaigns`, `customers`, and `transactions` on `customer_id` to calculate how much money a specific channel brought in).

---

## 4. The Machine Learning Engine (AI Tab)
**What it does:** Trains AI models and generates exact probabilities and CRM actions.

### Test A: K-Means Segmentation Training
1. **How to test:** Go to React App $\rightarrow$ "AI & Recommendations" tab. Click **Train Customer Segments**.
2. **What to expect:** Button goes into a loading state, then says "Success".
3. **Verification:** The backend just saved `segmentation_kmeans.joblib` to your hard drive and updated the `customer_segment` column in the database based on RFM coordinates.

### Test B: XGBoost Churn Training
1. **How to test:** Click **Train Churn Model**.
2. **What to expect:** Success message.
3. **Edge Case Handled:** Because you only have 3 customers, standard XGBoost would crash (it requires both "Churned" and "Active" labels to train). The backend intelligently synthesizes dummy rows to force the training to succeed for demonstration purposes. 

### Test C: Inference & Recommendations
1. **How to test:** Click **Generate New Predictions**. Then, select `CUST001` from the dropdown menu.
2. **What to expect:** 
   - **Health Score:** Will display (e.g., 69/100) with a visual green progress bar.
   - **AI Churn Risk:** Will display (e.g., 33.33%) with a visual red progress bar.
   - **Recommendations:** The Rules-Based engine will output a card. Because `CUST001` has a history of high severity support tickets in the database, the engine will output a **CRITICAL Priority** alert suggesting "Customer Success Manager manual intervention".
3. **Verification:** Change the dropdown to `CUST002`. The recommendation will instantly change to a **MEDIUM Priority** "Upsell / Cross-sell campaign" because they do not have support friction.
