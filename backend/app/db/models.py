from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Index, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    location = Column(String(100), nullable=True)
    sign_up_date = Column(Date, nullable=False)
    segment = Column(String(50), nullable=True)

    # Relationships
    transactions = relationship("Transaction", back_populates="customer")
    behaviors = relationship("CustomerBehavior", back_populates="customer")
    tickets = relationship("SupportTicket", back_populates="customer")
    campaigns = relationship("MarketingCampaign", back_populates="customer")
    features = relationship("CustomerFeature", back_populates="customer", uselist=False)

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(50), primary_key=True, index=True)
    product_name = Column(String(150), nullable=False)
    category = Column(String(100), nullable=True)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=True)

    # Relationships
    transactions = relationship("Transaction", back_populates="product")

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=True, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    payment_method = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")

class CustomerBehavior(Base):
    __tablename__ = "customer_behavior"

    behavior_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    log_date = Column(Date, nullable=False)
    website_visits = Column(Integer, default=0)
    app_sessions = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    avg_session_duration = Column(Float, default=0.0)

    # Relationships
    customer = relationship("Customer", back_populates="behaviors")

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    ticket_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    issue_date = Column(DateTime, nullable=False)
    resolution_date = Column(DateTime, nullable=True)
    category = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False)
    csat_score = Column(Integer, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="tickets")

class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"

    interaction_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False, index=True)
    campaign_id = Column(String(100), nullable=False)
    channel = Column(String(50), nullable=True)
    send_date = Column(Date, nullable=False)
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)

    # Relationships
    customer = relationship("Customer", back_populates="campaigns")

class CustomerFeature(Base):
    __tablename__ = "customer_features"

    customer_id = Column(String(50), ForeignKey("customers.customer_id"), primary_key=True, index=True)
    
    # 1. RFM Core
    tenure_days = Column(Integer, nullable=True)
    total_purchase_frequency = Column(Integer, nullable=True)
    total_monetary_value = Column(Float, nullable=True)
    avg_order_value = Column(Float, nullable=True)
    days_since_last_purchase = Column(Integer, nullable=True)
    order_velocity_days = Column(Float, nullable=True)
    refund_ratio = Column(Float, nullable=True)
    
    # 2. Product Diversity
    unique_categories_bought = Column(Integer, nullable=True)
    cross_sell_ratio = Column(Float, nullable=True)
    avg_quantity_per_order = Column(Float, nullable=True)
    
    # 3. Behavior
    total_sessions = Column(Integer, nullable=True)
    days_since_last_visit = Column(Integer, nullable=True)
    session_to_purchase_rate = Column(Float, nullable=True)
    
    # 4. Marketing
    total_campaigns_received = Column(Integer, nullable=True)
    email_ctr = Column(Float, nullable=True)
    marketing_opt_out = Column(Boolean, default=False)
    
    # 5. Support
    total_support_tickets = Column(Integer, nullable=True)
    days_since_last_ticket = Column(Integer, nullable=True)
    high_severity_tickets = Column(Integer, nullable=True)
    
    # 6. ML Targets
    spend_velocity = Column(Float, nullable=True)
    customer_health_score = Column(Float, nullable=True)
    churn_risk_score = Column(Float, nullable=True)
    predicted_clv = Column(Float, nullable=True)
    customer_segment = Column(String(50), nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="features")

class JobStatus(Base):
    __tablename__ = "job_status"
    
    job_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_type = Column(String(50))
    filename = Column(String(255))
    status = Column(String(50)) # e.g. "Processing", "Completed", "Failed"
    total_rows_processed = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_rejected = Column(Integer, default=0)
    dataset_health_score = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
