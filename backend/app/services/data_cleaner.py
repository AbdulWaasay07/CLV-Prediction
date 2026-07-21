import pandas as pd
from sqlalchemy.orm import Session
from app.db import models
from typing import Dict, Any
import math
import uuid

class DataCleanerService:
    def __init__(self, db: Session):
        self.db = db
        
    def _get_expected_columns(self, dataset_type: str) -> list:
        if dataset_type == "customers":
            return ["customer_id", "name", "email", "phone", "location", "sign_up_date"]
        elif dataset_type == "transactions":
            return ["transaction_id", "customer_id", "product_id", "transaction_date", "amount", "quantity", "payment_method", "status"]
        elif dataset_type == "products":
            return ["product_id", "product_name", "price"]
        elif dataset_type == "customer_behavior":
            return ["behavior_id", "customer_id", "log_date", "website_visits", "app_sessions", "page_views", "avg_session_duration"]
        elif dataset_type == "support":
            return ["ticket_id", "customer_id", "issue_date", "resolution_date", "category", "severity", "status", "csat_score"]
        elif dataset_type == "marketing":
            return ["interaction_id", "customer_id", "campaign_id", "channel", "send_date", "opened", "clicked", "converted"]
        return []

    def process_file_in_chunks(self, file_path: str, dataset_type: str, column_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Reads a CSV file in chunks to prevent memory exhaustion,
        applies dynamic column mapping, cleaning logic, and inserts into the database.
        """
        chunk_size = 10000
        total_rows = 0
        inserted = 0
        rejected = 0
        errors = []
        imputed_cells = 0

        # Mapping dataset_type to SQLAlchemy models
        model_mapping = {
            "customers": models.Customer,
            "transactions": models.Transaction,
            "products": models.Product,
            "customer_behavior": models.CustomerBehavior,
            "support": models.SupportTicket,
            "marketing": models.MarketingCampaign
        }

        if dataset_type not in model_mapping:
            raise ValueError(f"Unknown dataset_type: {dataset_type}")
            
        target_model = model_mapping[dataset_type]

        # Read CSV in chunks
        try:
            with pd.read_csv(file_path, chunksize=chunk_size) as reader:
                for chunk_index, chunk in enumerate(reader):
                    total_rows += len(chunk)
                    
                    # 1. Standardize column names first
                    chunk.columns = chunk.columns.str.lower().str.strip()
                    
                    # 1.5 Dynamic Column Mapping
                    if column_mapping:
                        clean_mapping = {str(k).lower().strip(): str(v).lower().strip() for k, v in column_mapping.items()}
                        chunk = chunk.rename(columns=clean_mapping)
                        
                    # 2. Specific cleaning (runs first to cast strings like currency to floats)
                    if dataset_type == "customers":
                        chunk = self._clean_customers(chunk)
                    elif dataset_type == "transactions":
                        chunk = self._clean_transactions(chunk)
                    elif dataset_type == "marketing":
                        chunk = self._clean_marketing(chunk)
                    elif dataset_type == "support":
                        chunk = self._clean_support(chunk)
                    elif dataset_type == "customer_behavior":
                        chunk = self._clean_behavior(chunk)
                    
                    # 3. Advanced Generic Cleaning (IQR, Imputation, Text Encoding, Duplicates)
                    chunk = self._generic_cleaning(chunk)
                    
                    # Count NaNs for health score after some drops but before final imputation
                    imputed_cells += int(chunk.isnull().sum().sum())
                    
                    # 2. Convert DataFrame to List of Dicts for SQLAlchemy
                    records = chunk.to_dict(orient="records")
                    
                    # Fix NaNs and NaTs at the dictionary level to avoid SQLAlchemy insertion errors
                    for record in records:
                        for key, value in record.items():
                            if pd.isna(value):
                                record[key] = None
                    
                    # 3. Bulk Insert
                    try:
                        # using bulk_insert_mappings is extremely fast in SQLAlchemy 2.0
                        self.db.bulk_insert_mappings(target_model, records)
                        self.db.commit()
                        inserted += len(records)
                    except Exception as e:
                        self.db.rollback()
                        rejected += len(records)
                        errors.append({"row_number": chunk_index * chunk_size, "issue": f"Bulk insert failed: {str(e)}"})
                        
        except pd.errors.EmptyDataError:
            pass # Handle empty file

        # Calculate Health Score
        # Score = (Valid Rows / Total Raw Rows) * 100 - (Percentage of Imputed Cells * 0.5)
        if total_rows > 0:
            total_cells = total_rows * len(chunk.columns)
            imputed_pct = (imputed_cells / total_cells) * 100
            score = (inserted / total_rows) * 100 - (imputed_pct * 0.5)
        else:
            score = 0.0

        return {
            "dataset_type": dataset_type,
            "total_rows_processed": total_rows,
            "rows_inserted": inserted,
            "rows_rejected": rejected,
            "dataset_health_score": round(max(0, min(100, score)), 2),
            "errors": errors[:100] # Return max 100 errors to avoid massive payloads
        }

    def _generic_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        # Drop exact duplicates
        df = df.drop_duplicates()
        
        # Categorical Encoding (lowercase, strip whitespace)
        for col in df.select_dtypes(include=['object']).columns:
            # We don't want to convert true NaNs to string "nan" just yet
            mask = df[col].notna()
            df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip().str.lower()
            
        # Numerical Imputation (Median) & Winsorization (99th percentile capping)
        for col in df.select_dtypes(include=['number']).columns:
            # Impute missing with Median
            median_val = df[col].median()
            if pd.isna(median_val): 
                median_val = 0
            df[col] = df[col].fillna(median_val)
            
            # Winsorization (Cap at 99th percentile to remove extreme outliers)
            upper_limit = df[col].quantile(0.99)
            if not pd.isna(upper_limit):
                df[col] = df[col].clip(upper=upper_limit)
                
        return df

    def _clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        # Impute missing categorical values
        if 'name' in df.columns:
            df['name'] = df['name'].fillna("Unknown")
        if 'location' in df.columns:
            df['location'] = df['location'].fillna("Unknown")
        
        # Standardize dates
        if 'sign_up_date' in df.columns:
            df['sign_up_date'] = pd.to_datetime(df['sign_up_date'], errors='coerce')
        # Drop rows where sign_up_date is invalid or missing email
        subset_drop = [col for col in ['sign_up_date', 'email'] if col in df.columns]
        if subset_drop:
            df = df.dropna(subset=subset_drop)
        
        return df

    def _clean_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        # Strip currency symbols and cast to float
        if 'amount' in df.columns and df['amount'].dtype == 'O':
            df['amount'] = df['amount'].replace(r'[^\d\.-]', '', regex=True).replace('', '0').astype(float)
            
        # Ensure quantities are numeric, fill missing with 1
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(1)
        
        # Standardize dates
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
        
        subset_drop = [col for col in ['transaction_date', 'customer_id'] if col in df.columns]
        if subset_drop:
            df = df.dropna(subset=subset_drop)
        
        return df

    def _clean_marketing(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'send_date' in df.columns:
            df['send_date'] = pd.to_datetime(df['send_date'], errors='coerce')
            
        # Generate a unique interaction_id if missing (since it is the Primary Key)
        if 'interaction_id' not in df.columns:
            df['interaction_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        else:
            # If the column exists but some values are missing, fill only the missing ones
            mask = df['interaction_id'].isnull() | (df['interaction_id'] == '')
            if mask.any():
                df.loc[mask, 'interaction_id'] = [str(uuid.uuid4()) for _ in range(mask.sum())]
            
        return df
        
    def _clean_support(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'issue_date' in df.columns:
            df['issue_date'] = pd.to_datetime(df['issue_date'], errors='coerce')
        if 'resolution_date' in df.columns:
            df['resolution_date'] = pd.to_datetime(df['resolution_date'], errors='coerce')
        return df
        
    def _clean_behavior(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'log_date' in df.columns:
            df['log_date'] = pd.to_datetime(df['log_date'], errors='coerce')
        return df
