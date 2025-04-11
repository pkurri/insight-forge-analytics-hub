
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DatasetStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class FileType(str, Enum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"
    DATABASE = "database"
    API = "api"

class DataType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"

class ColumnStats(BaseModel):
    min: Optional[Any] = None
    max: Optional[Any] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    std_dev: Optional[float] = None
    unique_count: Optional[int] = None
    null_count: Optional[int] = None
    sample_values: Optional[List[Any]] = None

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
    file_type: FileType

class DatasetCreate(DatasetBase):
    pass

class Dataset(DatasetBase):
    id: int
    user_id: Optional[int] = None
    file_path: Optional[str] = None
    record_count: int = 0
    column_count: int = 0
    status: DatasetStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}
    
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
    VALIDATE = "validate"
    TRANSFORM = "transform"
    ENRICH = "enrich"
    LOAD = "load"

class PipelineStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineStep(BaseModel):
    id: int
    pipeline_run_id: int
    step_name: PipelineStepType
    status: PipelineStepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    results: Dict[str, Any] = {}
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True

class PipelineRun(BaseModel):
    id: int
    dataset_id: int
    status: PipelineRunStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    steps: List[PipelineStep] = []
    
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
