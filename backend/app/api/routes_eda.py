from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract, text
from app.db.database import get_db
from app.db import models
from datetime import datetime, timedelta

router = APIRouter(tags=["Exploratory Data Analysis (EDA)"])

@router.get("/eda/kpis")
def get_core_kpis(db: Session = Depends(get_db)):
    try:
        total_customers = db.query(func.count(models.Customer.customer_id)).scalar() or 0
        total_revenue = db.query(func.sum(models.Transaction.amount)).filter(models.Transaction.status == "Completed").scalar() or 0.0
        
        # Historic CLV
        historic_clv = (total_revenue / total_customers) if total_customers > 0 else 0.0

        # Approximate MRR (Revenue in the last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        mrr = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.status == "Completed",
            models.Transaction.transaction_date >= thirty_days_ago
        ).scalar() or 0.0

        return {
            "total_customers": total_customers,
            "total_revenue": round(total_revenue, 2),
            "total_mrr": round(mrr, 2),
            "historic_clv": round(historic_clv, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/eda/revenue-trends")
def get_revenue_trends(db: Session = Depends(get_db)):
    try:
        daily_revenue = db.query(
            func.date(models.Transaction.transaction_date).label("date"),
            func.sum(models.Transaction.amount).label("revenue")
        ).filter(models.Transaction.status == "Completed").group_by(
            func.date(models.Transaction.transaction_date)
        ).order_by(func.date(models.Transaction.transaction_date)).all()

        return [{"date": str(row.date), "revenue": round(row.revenue, 2)} for row in daily_revenue]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/eda/customer-locations")
def get_customer_locations(db: Session = Depends(get_db)):
    """Customer Analysis: Customer Density and average spend by location"""
    try:
        locations = db.query(
            models.Customer.location,
            func.count(models.Customer.customer_id).label("customer_count")
        ).group_by(models.Customer.location).all()
        
        return [{"location": row.location, "density": row.customer_count} for row in locations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/eda/marketing-clv")
def get_marketing_clv(db: Session = Depends(get_db)):
    """Marketing Analysis: CLV grouped by Acquisition Channel"""
    try:
        # We need a complex join: MarketingCampaign -> Customer -> Transaction
        query = db.query(
            models.MarketingCampaign.channel,
            func.avg(models.Transaction.amount).label("avg_transaction_value"),
            func.count(func.distinct(models.Customer.customer_id)).label("acquired_customers")
        ).join(
            models.Customer, models.Customer.customer_id == models.MarketingCampaign.customer_id
        ).join(
            models.Transaction, models.Transaction.customer_id == models.Customer.customer_id
        ).filter(
            models.MarketingCampaign.converted == True
        ).group_by(models.MarketingCampaign.channel).all()
        
        return [{"channel": row.channel, "avg_spend": round(row.avg_transaction_value or 0, 2), "customers": row.acquired_customers} for row in query]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/eda/support-csat")
def get_support_csat(db: Session = Depends(get_db)):
    """Support Analysis: CSAT Score vs Ticket Volume"""
    try:
        data = db.query(
            models.SupportTicket.severity,
            func.avg(models.SupportTicket.csat_score).label("avg_csat"),
            func.count(models.SupportTicket.ticket_id).label("volume")
        ).group_by(models.SupportTicket.severity).all()
        
        return [{"severity": row.severity, "avg_csat": round(row.avg_csat or 0, 2), "volume": row.volume} for row in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
