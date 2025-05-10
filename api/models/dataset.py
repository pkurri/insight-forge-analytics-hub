from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PARQUET = "parquet"

class SourceType(str, Enum):
    FILE = "file"
    API = "api"
    DATABASE = "database"

class DatasetStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class DataType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    ARRAY = "array"

class ColumnStats(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    unique_count: Optional[int] = None
    null_count: Optional[int] = None
    value_counts: Optional[Dict[str, int]] = None

class DatasetColumn(BaseModel):
    name: str
    data_type: DataType
    nullable: bool = True
    stats: Optional[ColumnStats] = None
    
    class Config:
        orm_mode = True

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    user_id: int
    source_type: SourceType
    source_info: Dict[str, Any]
    status: DatasetStatus = DatasetStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class DatasetCreate(DatasetBase):
    pass

class Dataset(DatasetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DatasetDetail(Dataset):
    columns: List[DatasetColumn] = []

class DatasetSummary(BaseModel):
    id: str
    name: str
    recordCount: int
    columnCount: int
    createdAt: str
    updatedAt: str
    status: str

class PipelineStepType(str, Enum):
    CLEAN = "clean"
    VALIDATE = "validate"
    PROFILE = "profile"
    TRANSFORM = "transform"
    ENRICH = "enrich"
    LOAD = "load"
    SUGGESTIONS = "suggestions"
    BUSINESS_RULES = "business_rules"
    ANALYZE = "analyze"

class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineStep(BaseModel):
    id: int
    pipeline_run_id: int
    step_type: PipelineStepType
    status: PipelineRunStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    pipeline_metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class PipelineRun(BaseModel):
    id: int
    dataset_id: int
    status: PipelineRunStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    pipeline_metadata: Optional[Dict[str, Any]] = None
    steps: Optional[List[PipelineStep]] = None

    class Config:
        orm_mode = True

class BusinessRuleSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class BusinessRuleBase(BaseModel):
    name: str
    condition: str
    severity: BusinessRuleSeverity = BusinessRuleSeverity.MEDIUM
    message: Optional[str] = None

class BusinessRuleCreate(BusinessRuleBase):
    dataset_id: int
    model_generated: bool = False
    confidence: float = 1.0

class BusinessRule(BusinessRuleBase):
    id: int
    dataset_id: int
    is_active: bool = True
    model_generated: bool = False
    confidence: float = 1.0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
