import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime

class FeatureEngineeringService:
    def __init__(self, db: Session):
        self.db = db

    def _get_table_as_df(self, model) -> pd.DataFrame:
        query = self.db.query(model)
        df = pd.read_sql(query.statement, self.db.bind)
        return df

    def calculate_features(self):
        # 1. Fetch raw data
        customers = self._get_table_as_df(models.Customer)
        if customers.empty:
            return {"status": "success", "message": "No customers found."}
            
        transactions = self._get_table_as_df(models.Transaction)
        products = self._get_table_as_df(models.Product)
        behavior = self._get_table_as_df(models.CustomerBehavior)
        marketing = self._get_table_as_df(models.MarketingCampaign)
        support = self._get_table_as_df(models.SupportTicket)

        # Standardize customer_ids for pandas merges (which are case-sensitive)
        customers['customer_id_clean'] = customers['customer_id'].astype(str).str.lower().str.strip()
        for df in [transactions, behavior, marketing, support]:
            if not df.empty and 'customer_id' in df.columns:
                df['customer_id_clean'] = df['customer_id'].astype(str).str.lower().str.strip()

        # Base DataFrame initialized with all customer_ids
        features_df = customers[['customer_id', 'customer_id_clean', 'sign_up_date']].copy()
        current_date = pd.Timestamp(datetime.utcnow().date())
        
        # --- Category 1: RFM Core ---
        features_df['sign_up_date'] = pd.to_datetime(features_df['sign_up_date'])
        features_df['tenure_days'] = (current_date - features_df['sign_up_date']).dt.days

        if not transactions.empty:
            # Merge with products to get category info
            txn_prod = transactions.merge(products[['product_id', 'category']], on='product_id', how='left')
            
            # Filter completed transactions
            completed_txns = txn_prod[txn_prod['status'].str.lower() == 'completed']
            refunded_txns = txn_prod[txn_prod['status'].str.lower() == 'refunded']
            
            # Purchase Frequency, Revenue, AOV
            rfm = completed_txns.groupby('customer_id_clean').agg(
                total_purchase_frequency=('transaction_id', 'count'),
                total_monetary_value=('amount', 'sum'),
                last_purchase_date=('transaction_date', 'max'),
                first_purchase_date=('transaction_date', 'min'),
                avg_quantity_per_order=('quantity', 'mean'),
                unique_categories_bought=('category', 'nunique')
            ).reset_index()

            rfm['avg_order_value'] = rfm['total_monetary_value'] / rfm['total_purchase_frequency']
            rfm['last_purchase_date'] = pd.to_datetime(rfm['last_purchase_date'])
            rfm['first_purchase_date'] = pd.to_datetime(rfm['first_purchase_date'])
            
            rfm['days_since_last_purchase'] = (current_date - rfm['last_purchase_date']).dt.days
            
            # Order Velocity
            rfm['order_velocity_days'] = np.where(
                rfm['total_purchase_frequency'] > 1,
                (rfm['last_purchase_date'] - rfm['first_purchase_date']).dt.days / (rfm['total_purchase_frequency'] - 1),
                0
            )

            # Cross-sell Ratio
            rfm['cross_sell_ratio'] = (rfm['total_purchase_frequency'] - rfm['unique_categories_bought']) / rfm['total_purchase_frequency']
            rfm['cross_sell_ratio'] = rfm['cross_sell_ratio'].clip(lower=0)

            features_df = features_df.merge(rfm.drop(columns=['last_purchase_date', 'first_purchase_date']), on='customer_id_clean', how='left')

            # Refund Ratio
            refunds = refunded_txns.groupby('customer_id_clean').agg(refunded_amount=('amount', 'sum')).reset_index()
            features_df = features_df.merge(refunds, on='customer_id_clean', how='left')
            features_df['refunded_amount'] = features_df['refunded_amount'].fillna(0)
            features_df['total_monetary_value'] = features_df['total_monetary_value'].fillna(0)
            
            # Calculate ratio safely
            total_gross = features_df['total_monetary_value'] + features_df['refunded_amount']
            features_df['refund_ratio'] = np.where(total_gross > 0, features_df['refunded_amount'] / total_gross, 0)
            features_df = features_df.drop(columns=['refunded_amount'])
        else:
            for col in ['total_purchase_frequency', 'total_monetary_value', 'avg_order_value', 'days_since_last_purchase', 'order_velocity_days', 'cross_sell_ratio', 'avg_quantity_per_order', 'unique_categories_bought', 'refund_ratio']:
                features_df[col] = 0

        # --- Category 3: Behavior ---
        if not behavior.empty:
            beh_agg = behavior.groupby('customer_id_clean').agg(
                total_sessions=('website_visits', 'sum'),
                last_visit_date=('log_date', 'max')
            ).reset_index()
            
            beh_agg['last_visit_date'] = pd.to_datetime(beh_agg['last_visit_date'])
            beh_agg['days_since_last_visit'] = (current_date - beh_agg['last_visit_date']).dt.days
            
            features_df = features_df.merge(beh_agg.drop(columns=['last_visit_date']), on='customer_id_clean', how='left')
            features_df['session_to_purchase_rate'] = np.where(
                features_df['total_sessions'] > 0,
                features_df['total_purchase_frequency'] / features_df['total_sessions'],
                0
            )
        else:
            features_df['total_sessions'] = 0
            features_df['days_since_last_visit'] = 0
            features_df['session_to_purchase_rate'] = 0

        # --- Category 4: Marketing ---
        if not marketing.empty:
            mkt_agg = marketing.groupby('customer_id_clean').agg(
                total_campaigns_received=('interaction_id', 'count'),
                total_opened=('opened', 'sum'),
                total_clicked=('clicked', 'sum')
            ).reset_index()
            
            mkt_agg['email_ctr'] = np.where(mkt_agg['total_opened'] > 0, mkt_agg['total_clicked'] / mkt_agg['total_opened'], 0)
            
            features_df = features_df.merge(mkt_agg[['customer_id_clean', 'total_campaigns_received', 'email_ctr']], on='customer_id_clean', how='left')
            features_df['marketing_opt_out'] = False
        else:
            features_df['total_campaigns_received'] = 0
            features_df['email_ctr'] = 0
            features_df['marketing_opt_out'] = False

        # --- Category 5: Support ---
        if not support.empty:
            sup_agg = support.groupby('customer_id_clean').agg(
                total_support_tickets=('ticket_id', 'count'),
                last_ticket_date=('issue_date', 'max')
            ).reset_index()
            
            high_sev = support[support['severity'].str.lower() == 'high'].groupby('customer_id_clean').size().reset_index(name='high_severity_tickets')
            sup_agg = sup_agg.merge(high_sev, on='customer_id_clean', how='left')
            
            sup_agg['last_ticket_date'] = pd.to_datetime(sup_agg['last_ticket_date'])
            sup_agg['days_since_last_ticket'] = (current_date - sup_agg['last_ticket_date']).dt.days
            
            features_df = features_df.merge(sup_agg.drop(columns=['last_ticket_date']), on='customer_id_clean', how='left')
            features_df['high_severity_tickets'] = features_df['high_severity_tickets'].fillna(0)
        else:
            features_df['total_support_tickets'] = 0
            features_df['days_since_last_ticket'] = 0
            features_df['high_severity_tickets'] = 0

        # Fill NAs
        features_df = features_df.fillna(0)

        # --- Category 6: ML Targets & Composites ---
        features_df['spend_velocity'] = 1.0

        activity_score = np.log1p(features_df['total_purchase_frequency']) * 20 + np.log1p(features_df['total_sessions']) * 10
        friction_score = (features_df['total_support_tickets'] * 5) + (features_df['high_severity_tickets'] * 15) + (features_df['refund_ratio'] * 50)
        
        health_raw = activity_score - friction_score
        features_df['customer_health_score'] = np.clip(50 + health_raw, 0, 100)

        recency_penalty = np.clip(features_df['days_since_last_purchase'] / 365, 0, 1)
        freq_bonus = np.clip(features_df['total_purchase_frequency'] / 10, 0, 0.5)
        features_df['churn_risk_score'] = np.clip(recency_penalty - freq_bonus + (features_df['high_severity_tickets'] * 0.1), 0, 1)

        purchases_per_month = features_df['total_purchase_frequency'] / np.clip(features_df['tenure_days'] / 30, 1, None)
        features_df['predicted_clv'] = features_df['avg_order_value'] * purchases_per_month * 12 * 0.3

        def determine_segment(row):
            if row['churn_risk_score'] > 0.7: return 'At Risk'
            if row['churn_risk_score'] < 0.2 and row['customer_health_score'] > 80: return 'Champion'
            if row['days_since_last_purchase'] > 180: return 'Hibernating'
            return 'Active'
            
        features_df['customer_segment'] = features_df.apply(determine_segment, axis=1)

        # --- Upsert to Database ---
        features_df = features_df.drop(columns=['sign_up_date', 'customer_id_clean'])
        
        for col in features_df.select_dtypes(include=[np.number]).columns:
            features_df[col] = features_df[col].replace([np.inf, -np.inf], 0).fillna(0)
            if features_df[col].dtype == 'float64':
                features_df[col] = features_df[col].astype(float)
            elif features_df[col].dtype == 'int64':
                features_df[col] = features_df[col].astype(int)

        records = features_df.to_dict(orient='records')
        
        try:
            self.db.query(models.CustomerFeature).delete()
            self.db.commit()
            
            self.db.bulk_insert_mappings(models.CustomerFeature, records)
            self.db.commit()
            return {"status": "success", "features_generated": len(records)}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
