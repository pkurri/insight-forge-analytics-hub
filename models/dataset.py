from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    file_type: str
    source_type: str = "file"  # file, api, or database
    source_info: Optional[Dict[str, Any]] = None
    status: str = "pending"
    error: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: Optional[list[str]] = None
    file_path: Optional[str] = None
    cleaning_metadata: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    profile_data: Optional[Dict[str, Any]] = None
    anomalies: Optional[Dict[str, Any]] = None

class DatasetCreate(DatasetBase):
    pass

class Dataset(DatasetBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 