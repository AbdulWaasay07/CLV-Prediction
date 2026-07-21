import os
import shutil
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.upload_schema import UploadResponse
from app.services.data_cleaner import DataCleanerService

router = APIRouter(tags=["Data Upload"])

# Ensure temp directory exists
UPLOAD_DIR = "data/raw"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/{dataset_type}", response_model=UploadResponse)
async def upload_dataset(
    dataset_type: str, 
    file: UploadFile = File(...), 
    column_mapping: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV dataset. 
    Supported types: customers, transactions, products, customer_behavior, support, marketing
    """
    valid_types = ["customers", "transactions", "products", "customer_behavior", "support", "marketing"]
    
    if dataset_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid dataset_type. Must be one of {valid_types}")

    # MIME Type and File Size Security Scan
    if file.content_type not in ["text/csv", "application/vnd.ms-excel"] and not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported currently.")

    # Note: FastAPI/Starlette doesn't provide a direct way to get file size before reading, 
    # but we can check it using seek
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 500 * 1024 * 1024: # 500 MB
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 500MB.")

    # Save the file temporarily
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse the optional column mapping JSON
    mapping_dict = None
    if column_mapping:
        try:
            mapping_dict = json.loads(column_mapping)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON provided in column_mapping.")

    try:
        # Initialize the cleaner service
        cleaner = DataCleanerService(db)
        
        # Run the processing pipeline with the dynamic mapper
        result = cleaner.process_file_in_chunks(file_path, dataset_type, column_mapping=mapping_dict)
        
        # Add the filename to the response
        result['filename'] = file.filename
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data processing failed: {str(e)}")
    finally:
        # Clean up the raw file after processing to save space
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass # Ignore Windows file locking errors so the real error isn't masked
