# Customer Lifetime Value(CLV) Prediction System

A full-stack, data-driven machine learning platform designed to ingest raw, noisy customer data across various touchpoints and translate it into actionable business intelligence. The system employs advanced data cleaning, automated feature engineering, and robust machine learning models to identify at-risk customers and provide deterministic business recommendations.

## 🌟 Key Features

*   **Robust Data Ingestion & Cleaning:** Reads raw CSV files, handles missing values dynamically, applies domain-specific standardizations, and intelligently identifies extreme outliers (Winsorization).
*   **Automated Feature Engineering:** Flattens 6 relational tables into a robust 24-column feature store containing RFM metrics (Recency, Frequency, Monetary), behavioral signals, marketing interactions, and support friction indicators.
*   **Predictive Machine Learning Pipeline:** 
    *   **XGBoost Classifier:** Predicts continuous churn probabilities with high accuracy, automatically handling class imbalances via synthetic boundary sampling.
    *   **K-Means Clustering:** Dynamically segments the user base into actionable personas (e.g., *Champions*, *Active*, *At Risk*).
*   **Business Rules Engine:** Deterministically maps probabilistic ML outputs to prioritized, actionable CRM recommendations (e.g., "Trigger VIP Win-back sequence with 20% discount").
*   **Interactive React Dashboard:** Provides a seamless interface for data mapping/uploading, an Executive Summary EDA (Exploratory Data Analysis) view, and a dedicated ML dashboard for triggering predictions and reviewing individual customer profiles.

---

## 🏗 System Architecture & Tech Stack

The platform follows a modular, decoupled architecture:

*   **Frontend / UI:** React 18, Vite, Recharts (for interactive visualizations), Lucide-React (icons).
*   **Backend API:** Python 3.11, FastAPI (REST API framework).
*   **Database Engine:** MySQL 8.0, SQLAlchemy (ORM), PyMySQL.
*   **Machine Learning Core:** Pandas (Feature processing), Scikit-Learn (K-Means, Preprocessing), XGBoost (Gradient Boosting Classifier).

---

## 📁 Project Structure

```text
d:\churn_Prediction\
├── backend/                  # FastAPI Backend Server
│   ├── app/
│   │   ├── api/              # REST API route handlers (EDA, ML, Upload, Models)
│   │   ├── core/             # Application configuration (config.py)
│   │   ├── db/               # SQLAlchemy Models and Database session setup
│   │   ├── schemas/          # Pydantic schemas for data validation
│   │   ├── services/         # Core Logic: DataCleaner, FeatureEngineering, MLEngine
│   │   └── main.py           # FastAPI application entry point
│   ├── models/               # Directory for serialized ML models (.joblib)
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React Frontend Application
│   ├── src/
│   │   ├── App.jsx           # Main Application Shell & Data Importer
│   │   ├── Dashboard.jsx     # EDA (Exploratory Data Analysis) Dashboard
│   │   ├── MLDashboard.jsx   # AI & Recommendations Engine Dashboard
│   │   └── App.css           # Styling
│   └── package.json          # Node dependencies
├── generate_mock_data.py     # Python script to generate synthetic test datasets
└── README.md                 # This documentation file
```

---

## 🚀 Setup & Installation

### Prerequisites
*   **Python 3.9+** (3.11 recommended)
*   **Node.js 18+** & npm
*   **MySQL Server 8.0+** running locally.

### 1. Database Setup
Ensure you have a local MySQL server running.
Create a new database for the application:
```sql
CREATE DATABASE clv_database;
```
*Note: The application defaults to connecting to `mysql+pymysql://root:12345678@localhost:3306/clv_database`. You can modify these credentials in `backend/app/core/config.py` or via a `.env` file.*

### 2. Backend Setup
Navigate to the project root and start the backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*Upon startup, SQLAlchemy will automatically build the necessary 7 tables in your MySQL database.*

### 3. Frontend Setup
Open a new terminal window, navigate to the frontend directory, and start the development server:
```bash
cd frontend
npm install
npm run dev
```

---

## 📘 Usage Guide

### 1. Generating Mock Data
To test the platform's robustness, you can generate synthetic datasets containing mathematically correlated behaviors and deliberate noise (missing values, typos, outliers).
```bash
python generate_mock_data.py
```
This will produce 6 CSV files (`mock_customers.csv`, `mock_transactions.csv`, etc.) in the project root.

### 2. Ingesting Data
1. Navigate to the React frontend (typically `http://localhost:5173`).
2. Go to the **Data Importer** tab.
3. Select a dataset type (e.g., "Customers").
4. Upload the corresponding CSV. The UI will prompt you to map any unrecognized columns to the expected database schema.
5. Click **Upload & Clean**. The `DataCleanerService` will validate, clean, and insert the rows into MySQL, providing a real-time health score.
*(Note: To maintain referential integrity, upload Customers and Products before Transactions or Support Tickets).*

### 3. Exploratory Data Analysis (EDA)
Once data is ingested, switch to the **EDA Dashboard** tab to view real-time KPI metrics (MRR, Total Revenue) and interactive charts (Customer Density, Support CSAT vs Volume, Marketing Channel ROI).

### 4. Machine Learning & Predictions
Switch to the **AI & Recommendations** tab (ML Dashboard) to execute the pipeline:
1.  **Compile Feature Store:** Triggers the flattening of all raw tables into the 24-feature matrix.
2.  **Train Customer Segments:** Trains the K-Means algorithm to establish personas.
3.  **Train Churn Model:** Trains the XGBoost classifier on historic signals.
4.  **Generate Predictions:** Runs batch inference on all active customers.
5.  Select a specific customer from the dropdown to view their individualized Health Score, Churn Risk Probability, and the prioritized CRM recommendations generated by the Business Rules Engine.

---

## 📄 Documentation Generation

The project includes built-in scripts to generate professional PDF documentation using `fpdf2`.
*   To generate the 20+ page detailed source code breakdown: `python generate_source_code_pdf.py`
*   To generate the 25+ page final project report: `python generate_report_pdf.py`
