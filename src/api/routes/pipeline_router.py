from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Body, HTTPException
from src.services.user_service import get_current_user_or_api_key
from src.services.dataset_service import get_dataset_repository
from src.services.pipeline_service import get_pipeline_repository
from src.models.pipeline_model import PipelineStepType, PipelineRunStatus

router = APIRouter()

@router.post("/{dataset_id}/business-rules", response_model=Dict[str, Any])
async def apply_business_rules_in_pipeline(
    dataset_id: int,
    rules: List[Dict[str, Any]] = Body(...),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository),
    pipeline_repo = Depends(get_pipeline_repository)
):
    """Initialize business rules step for a dataset. Requires explicit user initiation."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Create or get pipeline run
    pipeline_run = await pipeline_repo.get_or_create_pipeline_run(dataset_id)
    
    # Create business rules step if it doesn't exist
    business_rules_step = await pipeline_repo.get_or_create_pipeline_step(
        pipeline_run_id=pipeline_run.id,
        step_name=PipelineStepType.BUSINESS_RULES,
        status=PipelineRunStatus.PENDING
    )
    
    return {
        "message": "Business rules step initialized. Use /steps/{step_id}/run to start applying rules.",
        "step_id": business_rules_step.id,
        "status": business_rules_step.status
    }

@router.post("/{dataset_id}/enrich", response_model=Dict[str, Any])
async def enrich_data_in_pipeline(
    dataset_id: int,
    config: Optional[Dict[str, Any]] = Body({}),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository),
    pipeline_repo = Depends(get_pipeline_repository)
):
    """Initialize enrich step for a dataset. Requires explicit user initiation."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Create or get pipeline run
    pipeline_run = await pipeline_repo.get_or_create_pipeline_run(dataset_id)
    
    # Create enrich step if it doesn't exist
    enrich_step = await pipeline_repo.get_or_create_pipeline_step(
        pipeline_run_id=pipeline_run.id,
        step_name=PipelineStepType.ENRICH,
        status=PipelineRunStatus.PENDING
    )
    
    return {
        "message": "Enrich step initialized. Use /steps/{step_id}/run to start enrichment.",
        "step_id": enrich_step.id,
        "status": enrich_step.status
    } 