
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import shutil
import os
from datetime import datetime

from models.dataset import (
    Dataset, DatasetCreate, DatasetDetail, BusinessRule,
    BusinessRuleCreate, DatasetSummary
)
from repositories.dataset_repository import get_dataset_repository
from services.file_service import process_uploaded_file
from config.settings import get_settings
from routes.auth_router import get_current_active_user, get_user_from_api_key

settings = get_settings()
router = APIRouter()

async def get_current_user_or_api_key(
    current_user = Depends(get_current_active_user),
    api_key_user = Depends(get_user_from_api_key)
):
    """Get the current user from either JWT token or API key."""
    if current_user:
        return current_user
    if api_key_user:
        return api_key_user
    raise HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer or API Key"},
    )

@router.get("/", response_model=List[DatasetSummary])
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Get a list of datasets."""
    datasets = await dataset_repo.get_datasets(user_id=current_user.id, skip=skip, limit=limit)
    
    # Convert to summary format
    return [
        DatasetSummary(
            id=str(ds.id),
            name=ds.name,
            recordCount=ds.record_count,
            columnCount=ds.column_count,
            createdAt=ds.created_at.isoformat(),
            updatedAt=ds.updated_at.isoformat(),
            status=ds.status.value
        )
        for ds in datasets
    ]

@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Get detailed information about a dataset."""
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Check ownership
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Get columns
    columns = await dataset_repo.get_dataset_columns(dataset_id)
    
    # Return detailed dataset info
    return DatasetDetail(
        **dataset.dict(),
        columns=columns
    )

@router.post("/", response_model=Dataset)
async def create_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file_type: str = Form(...),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Upload a new dataset file."""
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{timestamp}_{current_user.id}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create dataset record
    dataset_create = DatasetCreate(
        name=name,
        description=description,
        file_type=file_type
    )
    
    dataset = await dataset_repo.create_dataset(
        dataset=dataset_create,
        user_id=current_user.id,
        file_path=file_path
    )
    
    # Process the file asynchronously
    # This would typically be a background task
    # For now, we'll process it synchronously for simplicity
    try:
        await process_uploaded_file(dataset.id, file_path, file_type)
    except Exception as e:
        # Update dataset status to error
        await dataset_repo.update_dataset_status(dataset.id, "error", str(e))
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    # Return the created dataset
    return await dataset_repo.get_dataset(dataset.id)

@router.get("/{dataset_id}/rules", response_model=List[BusinessRule])
async def get_business_rules(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Get business rules for a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Get rules
    rules = await dataset_repo.get_business_rules(dataset_id)
    return rules

@router.post("/{dataset_id}/rules", response_model=BusinessRule)
async def create_business_rule(
    dataset_id: int,
    rule: BusinessRuleCreate,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Create a business rule for a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Create rule
    rule_data = rule.dict()
    rule_data["dataset_id"] = dataset_id
    created_rule = await dataset_repo.create_business_rule(rule_data)
    return created_rule

@router.post("/{dataset_id}/generate-rules", response_model=List[BusinessRule])
async def generate_business_rules(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Generate business rules for a dataset using AI."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Get dataset columns for context
    columns = await dataset_repo.get_dataset_columns(dataset_id)
    
    # This would call an AI service to generate rules
    # For now, return mock rules
    from services.ai_service import generate_business_rules
    generated_rules = await generate_business_rules(dataset, columns)
    
    # Save the generated rules
    saved_rules = []
    for rule in generated_rules:
        rule_data = rule.dict()
        rule_data["dataset_id"] = dataset_id
        created_rule = await dataset_repo.create_business_rule(rule_data)
        saved_rules.append(created_rule)
    
    return saved_rules
