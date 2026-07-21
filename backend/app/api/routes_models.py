from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import CustomerFeature
from app.services.ml_engine import MLEngineService

router = APIRouter()

@router.get("/customers")
def get_all_customers(db: Session = Depends(get_db)):
    """
    Returns a list of all customer IDs available for ML predictions.
    """
    try:
        customers = db.query(CustomerFeature.customer_id).all()
        return {"customers": [c[0] for c in customers]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-segmentation")
def train_segmentation(db: Session = Depends(get_db)):
    """
    Trains the K-Means clustering model and assigns personas.
    """
    try:
        result = MLEngineService.train_segmentation_model(db)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-churn")
def train_churn_model(db: Session = Depends(get_db)):
    """
    Trains the XGBoost Churn Prediction model.
    """
    try:
        result = MLEngineService.train_churn_model(db)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict")
def generate_predictions(db: Session = Depends(get_db)):
    """
    Loads saved models and updates all customers with their ML probabilities.
    """
    try:
        result = MLEngineService.generate_predictions(db)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{customer_id}")
def get_recommendations(customer_id: str, db: Session = Depends(get_db)):
    """
    Returns Business Rules Engine recommendations for a specific customer.
    """
    try:
        result = MLEngineService.get_business_recommendations(customer_id.lower(), db)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
