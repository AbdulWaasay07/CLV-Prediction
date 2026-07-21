# Customer Lifetime Value (CLV) & Customer Intelligence Platform
## Part 1: System Design & Data Foundation
### Section 11: Feature Engineering

---

## 11. Feature Engineering (Streamlined)

Feature Engineering is the heart of the Customer Intelligence Platform. Raw transactional and behavioral data is transformed into numerical vectors representing customer habits, health, and value. 
To optimize for performance and focus only on the highest-impact predictive signals, we have distilled the pipeline down to the **24 most critical features** that feed downstream machine learning models for Churn Prediction, CLV Forecasting, and Segmentation.

### Category 1: Recency, Frequency, Monetary (RFM) Core

#### 1. Customer Tenure
- **Formula**: `Current_Date - Sign_Up_Date` (in days).
- **Business Meaning**: The total lifespan of the customer relationship to date. Older customers generally have lower churn rates.

#### 2. Total Purchase Frequency
- **Formula**: `COUNT(transaction_id)` where status = 'Completed'.
- **Business Meaning**: Total number of successful orders. Indicates product stickiness.

#### 3. Total Monetary Value (Gross Revenue)
- **Formula**: `SUM(amount)` where status = 'Completed'.
- **Business Meaning**: Total top-line revenue brought in by the customer.

#### 4. Average Order Value (AOV)
- **Formula**: `Total Monetary Value / Total Purchase Frequency`.
- **Business Meaning**: The typical spend per transaction. Helps segment budget vs. premium buyers.

#### 5. Days Since Last Purchase (Recency)
- **Formula**: `Current_Date - MAX(transaction_date)`.
- **Business Meaning**: How long ago the customer last bought something. **The single strongest predictor of churn.**

#### 6. Average Days Between Purchases (Order Velocity)
- **Formula**: `(MAX(transaction_date) - MIN(transaction_date)) / (Total Purchase Frequency - 1)`.
- **Business Meaning**: The natural buying cycle. If a customer deviates from their own velocity, they are a churn risk.

#### 7. Refund Ratio
- **Formula**: `SUM(Refunded Amounts) / (SUM(Completed Amounts) + SUM(Refunded Amounts))`.
- **Business Meaning**: Percentage of revenue returned. High ratios indicate product dissatisfaction.

### Category 2: Product & Catalog Diversity

#### 8. Unique Categories Bought
- **Formula**: `COUNT(DISTINCT category)`.
- **Business Meaning**: Breadth of departments shopped. A massive indicator of platform reliance.

#### 9. Cross-Sell Ratio
- **Formula**: `(Total Purchase Frequency - Unique Categories Bought) / Total Purchase Frequency`.
- **Business Meaning**: Likelihood of buying outside their initial category. Measures the success of recommendation engines.

#### 10. Average Quantity Per Order
- **Formula**: `SUM(quantity) / Total Purchase Frequency`.
- **Business Meaning**: Volume of items per cart. Differentiates bulk buyers from individual retail consumers.

### Category 3: Customer Behavior & Digital Engagement

#### 11. Total Website/App Sessions
- **Formula**: `SUM(sessions)`.
- **Business Meaning**: Overall digital footprint. Drops in engagement usually precede churn.

#### 12. Days Since Last Visit
- **Formula**: `Current_Date - MAX(log_date)`.
- **Business Meaning**: Recency of digital engagement. Stopping browsing is a terminal churn signal.

#### 13. Session to Purchase Conversion Rate
- **Formula**: `Total Purchase Frequency / Total Sessions`.
- **Business Meaning**: How efficiently engagement turns into revenue.

### Category 4: Marketing Engagement

#### 14. Total Campaigns Received
- **Formula**: `COUNT(interaction_id)`.
- **Business Meaning**: Volume of outbound marketing directed at the user. Used as a baseline.

#### 15. Email Click-Through Rate (CTR)
- **Formula**: `SUM(clicked) / SUM(opened)`.
- **Business Meaning**: Effectiveness of the marketing CTA. A reliable indicator of active intent.

#### 16. Marketing Opt-Out Flag
- **Formula**: Binary (1 or 0) if user unsubscribed.
- **Business Meaning**: Total loss of cheap marketing channels. Highly correlated with impending churn.

### Category 5: Support & Friction

#### 17. Total Support Tickets
- **Formula**: `COUNT(ticket_id)`.
- **Business Meaning**: Total friction points experienced by the customer. High volume increases churn risk.

#### 18. Days Since Last Ticket
- **Formula**: `Current_Date - MAX(issue_date)`.
- **Business Meaning**: Recency of customer friction. A fresh ticket + no recent purchases = high churn risk.

#### 19. High Severity Tickets Count
- **Formula**: `COUNT(ticket_id) where severity='High'`.
- **Business Meaning**: Count of critical failures. One high severity ticket causes more churn than ten "how-to" questions.

### Category 6: Derived Composite Indexes & ML Targets

#### 20. Spend Velocity (Trend)
- **Formula**: `(Spend in Last 90 Days) / (Spend in Previous 90 Days)`.
- **Business Meaning**: Is the customer spending more or less? Catches "wallet share" shifting to competitors.

#### 21. Customer Health Score
- **Formula**: `Weighted Algorithm based on Activity vs. Friction`.
- **Business Meaning**: The ultimate pulse of the customer relationship. The primary KPI for Account Managers.

#### 22. Churn Risk Score (Target Proxy)
- **Formula**: Baseline Logistic Regression probability based on Recency and Frequency.
- **Business Meaning**: The probability they will never buy again. Allows preemptive win-back campaigns.

#### 23. Projected Future CLV (Target Metric)
- **Formula**: `AOV * (Purchases per Month) * Expected Lifetime * Profit Margin`.
- **Business Meaning**: The Holy Grail. Dictates exactly how much can be spent to acquire similar lookalike users.

#### 24. Customer Segment Profile
- **Formula**: Rule-based bucketing based on RFM percentiles (e.g., "Champions", "At Risk", "Hibernating").
- **Business Meaning**: Human-readable categorization so marketing teams can build targeted campaigns.
