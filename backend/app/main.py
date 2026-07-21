from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_upload
from app.api import routes_eda
from app.api import routes_ml

app = FastAPI(
    title="Customer Intelligence Platform API",
    description="Backend API for the CLV & Customer Intelligence Platform",
    version="1.0.0"
)

# Allow React Frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Customer Intelligence Platform API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "disconnected"} # DB status to be implemented

from app.api import routes_models

app.include_router(routes_upload.router, prefix="/api")
app.include_router(routes_eda.router, prefix="/api")
app.include_router(routes_ml.router, prefix="/api")
app.include_router(routes_models.router, prefix="/api/models")
