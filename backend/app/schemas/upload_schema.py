from pydantic import BaseModel
from typing import List, Optional

class ErrorLog(BaseModel):
    row_number: int
    issue: str

class UploadResponse(BaseModel):
    filename: str
    dataset_type: str
    total_rows_processed: int
    rows_inserted: int
    rows_rejected: int
    dataset_health_score: float
    errors: Optional[List[ErrorLog]] = []
