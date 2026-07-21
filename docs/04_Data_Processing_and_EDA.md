# Customer Lifetime Value (CLV) & Customer Intelligence Platform
## Part 1: System Design & Data Foundation
### Section 8: Upload Module, Section 9: Data Cleaning Pipeline, Section 10: Exploratory Data Analysis (EDA)

---

## 8. Upload Module

The Upload Module is the gateway to the platform. It must be resilient, secure, and provide excellent user feedback.

### Complete Upload Workflow
1. **File Reception**: User uploads file via API `/api/upload/{dataset_type}`.
2. **Security Scan**: Check file extension (`.csv`, `.xlsx`), MIME type, and file size (< 500MB).
3. **In-Memory Streaming**: File is loaded in chunks using Pandas (`pd.read_csv(chunksize=10000)`) to prevent RAM exhaustion.
4. **Schema Validation**: Pydantic models verify that required columns exist.
5. **Data Cleaning**: Chunk is passed to the Data Cleaning Pipeline.
6. **Database Insertion**: Cleaned chunk is appended to the MySQL table using SQLAlchemy `bulk_insert_mappings`.
7. **Status Tracking**: Progress is updated in a tracking table (e.g., `Job_Status`).
8. **Summary Generation**: Total rows, accepted rows, rejected rows, and error reasons are compiled and returned to the user.

### Validation & Error Handling
- **Duplicate Detection**: MD5 hash of the row content is compared against recent inserts, or Primary Keys are checked for collisions.
- **Error Reporting**: If Row 50 has a missing `customer_id`, the row is skipped, and an error object `{"row": 50, "issue": "Missing customer_id"}` is logged. The upload continues.
- **Recovery After Failure**: Database transactions are managed per chunk. If a chunk fails completely, it rolls back, but previous successful chunks remain.

---

## 9. Data Cleaning Pipeline

Raw business data is notoriously dirty. The pipeline automates Data Engineering best practices.

### Cleaning Workflow & Strategies

| Issue | Detection Method | Cleaning Strategy Applied |
| :--- | :--- | :--- |
| **Missing Values (Categorical)** | `df.isnull().sum()` | Impute with 'Unknown' or mode (e.g., Missing `location` -> 'Unknown'). |
| **Missing Values (Numerical)** | `df.isnull().sum()` | Impute with Median (to resist outliers) or 0 (e.g., missing `amount` -> 0). |
| **Outliers** | Z-Score > 3 or IQR method | Cap at 99th percentile (Winsorization) to prevent a single $1M transaction from skewing CLV. |
| **Duplicates** | `df.duplicated()` | Drop exact duplicates. Keep `last` for duplicate Primary Keys. |
| **Date Parsing** | `pd.to_datetime(errors='coerce')` | Standardize to ISO 8601 format. Invalid dates become `NaT` and are imputed or dropped. |
| **Currency Formatting** | Regex `[^\d\.]` | Strip `$`, `,`, `€`, then cast to `float64`. |
| **Categorical Encoding** | Standardizing text | Lowercase, strip whitespace. "New York ", "new york" -> "new york". |

### Data Quality Scoring
After cleaning, the system calculates a **Dataset Health Score** (0-100%):
`Score = (Valid Rows / Total Raw Rows) * 100 - (Percentage of Imputed Cells * 0.5)`
This score is returned to the user to grade their data governance.

---

## 10. Exploratory Data Analysis (EDA)

Before running complex ML models, the platform provides out-of-the-box analytical endpoints to help businesses understand their data.

### Core Business KPIs Generated
- **Total MRR / ARR**: Monthly/Annual Recurring Revenue.
- **Overall Churn Rate**: Percentage of customers lost in a given period.
- **Average Customer Lifetime Value (Historic)**: Total revenue / Total unique customers.
- **Customer Acquisition Cohorts**: Retention rates by sign-up month.

### Analytical Domains

1. **Revenue Analysis**
   - *Insight*: Are revenues driven by a few large purchases or many small ones?
   - *Chart*: Time-series line chart of Daily Revenue. Histogram of Order Values.

2. **Customer Analysis**
   - *Insight*: Where are the most valuable customers located?
   - *Chart*: Geo-map of Customer Density overlaid with Average Spend.

3. **Product Analysis**
   - *Insight*: Which products drive the most initial acquisitions vs. repeat purchases?
   - *Chart*: Bar chart comparing "First Purchase Volume" vs "Subsequent Purchase Volume" by Category.

4. **Marketing Analysis**
   - *Insight*: Which channels yield the highest CLV?
   - *Chart*: Box plot of Customer Lifetime Value grouped by Acquisition Channel.

5. **Support Analysis**
   - *Insight*: Does poor support drive churn?
   - *Chart*: Scatter plot of CSAT Score vs. Days until Churn.

### Reports & Decision-Making Examples
- **Example**: The EDA reveals that customers generating Support Tickets with "High Severity" churn at a 40% higher rate within 30 days.
- **Decision**: The business implements a rule in their CRM to automatically offer a 20% discount code upon resolution of any High Severity ticket.
