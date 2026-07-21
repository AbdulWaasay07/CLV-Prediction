import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.db.database import engine
from app.db.models import CustomerFeature, Customer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib
import os
import shap

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

class MLEngineService:
    @staticmethod
    def train_segmentation_model(db: Session):
        """
        Trains K-Means clustering on the RFM features and assigns personas.
        """
        df = pd.read_sql("SELECT * FROM customer_features", engine)
        if len(df) < 3:
            return {"status": "error", "message": "Need at least 3 customers to train segmentation."}

        # Select RFM features for clustering
        features = ["days_since_last_purchase", "total_purchase_frequency", "total_monetary_value"]
        X = df[features].copy()

        # Scale data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train K-Means (Assuming 3 clusters: Champions, At Risk, Hibernating)
        kmeans = KMeans(n_clusters=min(3, len(X)), random_state=42, n_init=10)
        df['cluster'] = kmeans.fit_predict(X_scaled)

        # Basic persona mapping based on cluster centroids (simplified logic)
        centroids = kmeans.cluster_centers_
        # Find the cluster with highest monetary value (Champions)
        champ_cluster = np.argmax(centroids[:, 2])
        # Find the cluster with highest recency days (Hibernating/At Risk)
        risk_cluster = np.argmax(centroids[:, 0])

        def map_persona(cluster_id):
            if cluster_id == champ_cluster:
                return "Champions"
            elif cluster_id == risk_cluster:
                return "At Risk"
            else:
                return "Active"

        df['predicted_segment'] = df['cluster'].apply(map_persona)

        # Save models for future inference
        joblib.dump(scaler, os.path.join(MODELS_DIR, "segmentation_scaler.joblib"))
        joblib.dump(kmeans, os.path.join(MODELS_DIR, "segmentation_kmeans.joblib"))

        # Update DB
        updated_count = 0
        for index, row in df.iterrows():
            customer = db.query(CustomerFeature).filter(CustomerFeature.customer_id == row['customer_id']).first()
            if customer:
                customer.customer_segment = row['predicted_segment']
                updated_count += 1
        db.commit()

        return {"status": "success", "message": f"Successfully segmented {updated_count} customers.", "clusters_found": len(np.unique(df['cluster']))}

    @staticmethod
    def train_churn_model(db: Session):
        """
        Trains an XGBoost model to predict churn.
        Since we don't have historical labels, we synthesize 'is_churned' 
        as days_since_last_purchase > 15 (for demo purposes) or similar proxy.
        """
        df = pd.read_sql("SELECT * FROM customer_features", engine)
        if len(df) < 5:
            # We need more data to reliably train a model, but for demo we will allow it if we synthesize
            pass

        # For enterprise demo, let's define churn target dynamically:
        # If they haven't purchased in 30 days, they are churned.
        threshold = df['days_since_last_purchase'].median() if len(df) > 0 else 30
        if threshold == 0: threshold = 1
        
        df['is_churned'] = (df['days_since_last_purchase'] > threshold).astype(int)

        # If we have only 1 class (e.g., everyone is active), XGBoost will crash.
        # Synthesize dummy data to ensure model can train.
        if df['is_churned'].nunique() < 2:
            dummy_churn = df.iloc[0:1].copy()
            dummy_churn['days_since_last_purchase'] = threshold + 100
            dummy_churn['is_churned'] = 1
            
            dummy_active = df.iloc[0:1].copy()
            dummy_active['days_since_last_purchase'] = 0
            dummy_active['is_churned'] = 0
            
            df = pd.concat([df, dummy_churn, dummy_active], ignore_index=True)

        features = [
            "tenure_days", "total_purchase_frequency", "total_monetary_value", 
            "avg_order_value", "order_velocity_days", "refund_ratio", 
            "unique_categories_bought", "cross_sell_ratio", "avg_quantity_per_order",
            "total_sessions", "days_since_last_visit", "session_to_purchase_rate",
            "total_campaigns_received", "email_ctr", "marketing_opt_out",
            "total_support_tickets", "days_since_last_ticket", "high_severity_tickets",
            "customer_health_score"
        ]

        X = df[features]
        y = df['is_churned']

        # Train XGBoost
        model = xgb.XGBClassifier(
            n_estimators=100, 
            max_depth=3, 
            learning_rate=0.1, 
            eval_metric='logloss',
            random_state=42
        )
        model.fit(X, y)

        # Save model
        joblib.dump(model, os.path.join(MODELS_DIR, "churn_xgboost.joblib"))
        
        # Save feature list for alignment during inference
        joblib.dump(features, os.path.join(MODELS_DIR, "churn_features.joblib"))

        return {"status": "success", "message": "Churn prediction model trained and saved successfully."}

    @staticmethod
    def generate_predictions(db: Session):
        """
        Loads the trained models and updates the Database with exact ML probability scores.
        """
        model_path = os.path.join(MODELS_DIR, "churn_xgboost.joblib")
        features_path = os.path.join(MODELS_DIR, "churn_features.joblib")

        if not os.path.exists(model_path) or not os.path.exists(features_path):
            return {"status": "error", "message": "Models not found. Train models first."}

        model = joblib.load(model_path)
        feature_cols = joblib.load(features_path)

        df = pd.read_sql("SELECT * FROM customer_features", engine)
        if len(df) == 0:
             return {"status": "error", "message": "No customers to predict."}
             
        X = df[feature_cols]

        # Predict Probabilities
        probabilities = model.predict_proba(X)[:, 1]  # Get probability of class 1 (Churn)

        # Update Database
        updated = 0
        for i, row in df.iterrows():
            customer = db.query(CustomerFeature).filter(CustomerFeature.customer_id == row['customer_id']).first()
            if customer:
                # We override the heuristic churn_risk_score with the exact ML probability
                customer.churn_risk_score = float(probabilities[i])
                updated += 1
        
        db.commit()
        return {"status": "success", "message": f"Generated exact ML churn predictions for {updated} customers."}

    @staticmethod
    def get_business_recommendations(customer_id: str, db: Session):
        """
        Rules-Based Business Recommendation Engine (Module 7).
        Translates ML outputs into actionable CRM text.
        """
        feature = db.query(CustomerFeature).filter(CustomerFeature.customer_id == customer_id).first()
        if not feature:
            return {"status": "error", "message": "Customer not found."}

        actions = []
        
        # Rule 1: High Churn Risk + High CLV
        if feature.churn_risk_score > 0.6 and feature.predicted_clv > 50:
            actions.append({"priority": "HIGH", "action": "VIP Win-back Email + 20% Discount. Customer is highly valuable but at risk."})
        
        # Rule 2: Support Friction
        if feature.high_severity_tickets >= 1:
            actions.append({"priority": "CRITICAL", "action": "Customer Success Manager manual intervention required. High severity ticket detected."})

        # Rule 3: Upsell Ready
        if feature.churn_risk_score < 0.2 and feature.customer_health_score > 80:
            actions.append({"priority": "MEDIUM", "action": "Send Upsell / Cross-sell campaign. Customer is healthy and engaged."})

        # Rule 4: Hibernating/Low Value
        if feature.churn_risk_score > 0.7 and feature.predicted_clv < 50:
            actions.append({"priority": "LOW", "action": "Automated drip campaign. Do not spend aggressive CAC on discounts."})
            
        if not actions:
            actions.append({"priority": "NORMAL", "action": "Maintain standard lifecycle marketing."})

        return {
            "customer_id": customer_id,
            "segment": feature.customer_segment,
            "health_score": round(feature.customer_health_score, 2),
            "ml_churn_probability": round(feature.churn_risk_score * 100, 2),
            "recommendations": actions
        }
