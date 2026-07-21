# Customer Intelligence \& Churn Prediction Platform: Comprehensive Part 1 Documentation

This document provides an exhaustive, granular breakdown of **Part 1** of the Customer Intelligence and Churn Prediction Platform. It covers the complete journey of data from raw CSV uploads to mathematically engineered Machine Learning features.

Our goal in Part 1 is to solve the classic data engineering problem: *taking messy, disconnected, human-generated business data and transforming it into a pristine, unified numerical matrix that an Artificial Intelligence can interpret.*

\---

## Table of Contents

1. [System Architecture \& Database Design](#1-system-architecture--database-design)
2. [Data Ingestion \& The Cleaning Engine](#2-data-ingestion--the-cleaning-engine)
3. [Exploratory Data Analysis (EDA) Engine](#3-exploratory-data-analysis-eda-engine)
4. [Feature Engineering Pipeline (The 24 Features)](#4-feature-engineering-pipeline-the-24-features)

\---

## 1\. System Architecture \& Database Design

The platform relies on a normalized relational database (MySQL/SQLite) accessed via **SQLAlchemy** (an Object-Relational Mapper) in our FastAPI backend. The schema is divided into 6 core tables:

### The 5 Raw Tables

1. **`customers` (The Hub):** The central table. Every other table links back to this via `customer\_id` (Foreign Key). Contains demographic data (`location`, `sign\_up\_date`, `segment`).
2. **`transactions` (Financials):** Logs every purchase. Tracks `amount`, `quantity`, `payment\_method`, and `status` (e.g., Completed, Refunded).
3. **`products` (Catalog):** Links to transactions via `product\_id`. Stores `category`, `price`, and `cost`.
4. **`support\_tickets` (Friction):** Tracks customer complaints. Contains `issue\_date`, `severity` (Low/Medium/High), and `csat\_score`.
5. **`marketing\_campaigns` (Engagement):** Tracks outbound interactions. Contains flags for `opened`, `clicked`, and `converted`.
6. **`customer\_behavior` (Usage):** Tracks platform usage via `website\_visits`, `app\_sessions`, and `avg\_session\_duration`.

### The Derived Table

* **`customer\_features` (The AI Input):** A strictly numerical table containing 1 row per customer and exactly 24 computed metrics. This is the ultimate output of Part 1.

\---

## 2\. Data Ingestion \& The Cleaning Engine

Real-world CSV data uploaded by businesses is inherently dirty. It contains blanks, string-casing inconsistencies, missing Primary Keys, and extreme typographical errors.

When a user uploads a CSV in the React frontend, it hits our **FastAPI upload routes**. It is immediately intercepted by the `DataCleanerService` (powered by Pandas).

### The 4 Pillars of Data Cleaning Applied:

#### A. ID Generation \& Constraint Satisfaction

Relational databases crash if Primary Keys are missing.

* **Example:** The raw Marketing logs often lack a unique ID for the email sent. The `\_clean\_marketing` function detects this and automatically generates a standard `UUID` (`interaction\_id`) for every single row before inserting it into MySQL.

#### B. Intelligent Imputation (Filling the Blanks)

Machine Learning models cannot process `NULL` values. We use mathematical strategies to fill them:

* **Continuous Variables (Numbers):** If a transaction is missing its `amount` (e.g., `CUST004` had a blank amount), the engine calculates the **median** transaction amount of the entire dataset (e.g., `$13.50`) and injects it. Median is used over Mean because it is resilient to extreme outliers.
* **Categorical Variables (Text):** If a customer is missing a `location` or `segment`, the engine fills it with the string `"Unknown"` to maintain structural integrity.

#### C. Outlier Winsorization (The $9.6 Million T-Shirt)

Outliers destroy average calculations.

* **Real Scenario:** In our raw data, `CUST002` accidentally had a transaction logged for **$9,699,999.48**.
* **The Solution:** We apply statistical *Winsorization*. The engine calculates the 99th percentile of all valid purchases in the dataset (e.g., `$9,600,000`). Any transaction exceeding that amount is forcibly clamped down to that 99th percentile ceiling. This preserves the record without allowing a typo to skew the Average Order Value to infinity.

#### D. Schema Hardening

The pandas dataframe columns are rigidly cast to match the SQLAlchemy `models.py` definitions. Strings are stripped of whitespace, and datetime columns are parsed using `pd.to\_datetime(errors='coerce')` to catch impossible dates (like "Feb 30th").

\---

## 3\. Exploratory Data Analysis (EDA) Engine

Once data is clean, the business needs to see it. We built a React Dashboard (`Dashboard.jsx`) that visualizes the state of the business using `recharts`. The frontend pulls from 5 specific `/api/eda/` endpoints that perform advanced SQL aggregations on the fly.

### The 5 EDA Endpoints:

1. **`/api/eda/kpis`**: Calculates top-level metrics. It queries the `customers` table for total users, and `transactions` for total revenue and average transaction value.
2. **`/api/eda/revenue-trends`**: Groups transactions by month (`DATE\_FORMAT`). It provides a time-series line chart of revenue growth.
3. **`/api/eda/customer-locations`**: Performs a `GROUP BY location` on the customers table to feed a geographic bar chart.
4. **`/api/eda/marketing-clv`**: The most complex endpoint. It joins 3 tables: `marketing\_campaigns`, `customers`, and `transactions`. It groups by marketing `channel` (e.g., Email, Social) and calculates the Average Spend of customers acquired through that channel.
5. **`/api/eda/support-csat`**: Groups by ticket `severity` (High/Medium/Low) and calculates the average `csat\_score` to show how different problem severities impact customer happiness.

\---

## 4\. Feature Engineering Pipeline (The 24 Features)

The ultimate goal of Part 1. The `FeatureEngineeringService` takes thousands of distinct, timestamped logs across 5 tables and mathematically flattens them into a single 24-column vector per customer.

### The Hidden Casing Bug \& Standardization

During development, we encountered a critical data engineering bug: Pandas merges are strictly case-sensitive. The `customers` table used uppercase IDs (`CUST001`), while `transactions` used lowercase (`cust001`). This caused all merges to fail silently, resulting in features being evaluated as `0`.

* **The Fix:** The pipeline now forces a `.astype(str).str.lower().str.strip()` on all `customer\_id` columns across all 5 DataFrames immediately upon loading, ensuring mathematically perfect JOINs.

### The 24 Engineered Features Breakdown

The pipeline categorizes features into 6 distinct groups. Here is exactly how they are calculated:

#### Group 1: RFM Core (Recency, Frequency, Monetary)

1. **`tenure\_days`**: `Current Date` minus `sign\_up\_date`. How long they have been a customer.
2. **`total\_purchase\_frequency`**: A direct `COUNT()` of `Completed` transactions.
3. **`total\_monetary\_value`**: The `SUM()` of the `amount` of all `Completed` transactions.
4. **`avg\_order\_value`**: `total\_monetary\_value` / `total\_purchase\_frequency`.
5. **`days\_since\_last\_purchase`**: `Current Date` minus the `MAX(transaction\_date)`. A highly predictive churn signal.
6. **`order\_velocity\_days`**: The time between their first and last purchase, divided by `(frequency - 1)`. Shows their natural buying rhythm.
7. **`refund\_ratio`**: Total refunded amount divided by total gross amount. (High ratio = high churn risk).

#### Group 2: Product Diversity

8. **`unique\_categories\_bought`**: A count of distinct product categories they have purchased from.
9. **`cross\_sell\_ratio`**: `(Frequency - Unique Categories) / Frequency`. A ratio near 0 means they explore the catalog; a ratio near 1 means they only buy one specific thing.
10. **`avg\_quantity\_per\_order`**: The mean of the `quantity` column.

#### Group 3: Behavioral Engagement

11. **`total\_sessions`**: The sum of `website\_visits` and `app\_sessions`.
12. **`days\_since\_last\_visit`**: `Current Date` minus the last login date.
13. **`session\_to\_purchase\_rate`**: `total\_purchase\_frequency` / `total\_sessions`. Conversion efficiency.

#### Group 4: Marketing Receptivity

14. **`total\_campaigns\_received`**: Count of all emails/ads sent to the user.
15. **`email\_ctr` (Click-Through Rate)**: Total `clicked` flags / Total `opened` flags. Measures engagement with outbound marketing.
16. **`marketing\_opt\_out`**: Boolean flag indicating if they unsubscribed.

#### Group 5: Support Friction

17. **`total\_support\_tickets`**: Count of all tickets opened.
18. **`days\_since\_last\_ticket`**: `Current Date` minus the last ticket `issue\_date`.
19. **`high\_severity\_tickets`**: Count of tickets where `severity == 'High'`.

#### Group 6: Composites \& ML Targets (The "Magic" Scores)

20. **`spend\_velocity`**: Currently set as a baseline trend variable.
21. **`customer\_health\_score` (0-100)**:

    * *Calculation:* Starts at 50. We add an Activity Score (using `log1p(purchases)\*20 + log1p(sessions)\*10`) and subtract a Friction Score (`support\_tickets\*5 + high\_severity\*15 + refund\_ratio\*50`). We use natural logarithms (`log1p`) so that extreme power-users don't break the 0-100 scale.
22. **`churn\_risk\_score` (0-1)**: A baseline proxy heuristic. Penalizes for high `days\_since\_last\_purchase` and boosts for high frequency.
23. **`predicted\_clv`**: An initial heuristic baseline calculation: `avg\_order\_value` \* `purchases\_per\_month` \* `12 months` \* `30% profit margin`.
24. **`customer\_segment`**: A categorical label based on health thresholds (e.g., "Champion", "At Risk", "Active", "Hibernating").

### Final Output \& Ready for Part 2

Once all calculations are performed in Pandas, the script handles `NaN` and `Inf` cleanup (replacing them with `0`) and executes a massive `bulk\_insert\_mappings` via SQLAlchemy back into the `customer\_features` MySQL table.

This completely numerical, highly contextual 24-dimension table is exactly what the Machine Learning models in **Phase 5** will use to train the predictive AI.

