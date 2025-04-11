
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from typing import Dict, Any, Optional, List
from datetime import datetime

from api.models.dataset import PipelineRun, PipelineStep, PipelineRunStatus, PipelineStepType
from api.repositories.pipeline_repository import get_pipeline_repository
from api.repositories.dataset_repository import get_dataset_repository
from api.services.pipeline_service import run_pipeline_step
from api.routes.auth_router import get_current_user_or_api_key

router = APIRouter()

@router.post("/{dataset_id}/run", response_model=PipelineRun)
async def start_pipeline_run(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_or_api_key),
    pipeline_repo = Depends(get_pipeline_repository),
    dataset_repo = Depends(get_dataset_repository)
):
    """Start a new pipeline run for a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Create pipeline run
    pipeline_run = await pipeline_repo.create_pipeline_run(dataset_id)
    
    # Add pipeline steps
    steps = []
    for step_type in [
        PipelineStepType.VALIDATE,
        PipelineStepType.TRANSFORM,
        PipelineStepType.ENRICH,
        PipelineStepType.LOAD
    ]:
        step = await pipeline_repo.create_pipeline_step(
            pipeline_run_id=pipeline_run.id,
            step_name=step_type
        )
        steps.append(step)
    
    # Run the first step in the background
    background_tasks.add_task(
        run_pipeline_step,
        pipeline_repo,
        dataset_repo,
        pipeline_run.id,
        steps[0].id
    )
    
    # Update pipeline run status to running
    await pipeline_repo.update_pipeline_run_status(
        pipeline_run.id, 
        PipelineRunStatus.RUNNING
    )
    
    # Get the updated pipeline run with steps
    return await pipeline_repo.get_pipeline_run_with_steps(pipeline_run.id)

@router.get("/runs/{run_id}", response_model=PipelineRun)
async def get_pipeline_run(
    run_id: int,
    current_user = Depends(get_current_user_or_api_key),
    pipeline_repo = Depends(get_pipeline_repository)
):
    """Get details of a pipeline run."""
    pipeline_run = await pipeline_repo.get_pipeline_run_with_steps(run_id)
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    
    # Check user has access to the dataset
    dataset = await pipeline_repo.get_dataset_from_pipeline_run(run_id)
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this pipeline run")
    
    return pipeline_run

@router.post("/steps/{step_id}/run", response_model=PipelineStep)
async def run_pipeline_step_endpoint(
    step_id: int,
    background_tasks: BackgroundTasks,
    params: Dict[str, Any] = Body({}),
    current_user = Depends(get_current_user_or_api_key),
    pipeline_repo = Depends(get_pipeline_repository),
    dataset_repo = Depends(get_dataset_repository)
):
    """Manually run a specific pipeline step."""
    # Get the step
    step = await pipeline_repo.get_pipeline_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Pipeline step not found")
    
    # Check user has access to the dataset
    pipeline_run = await pipeline_repo.get_pipeline_run(step.pipeline_run_id)
    dataset = await dataset_repo.get_dataset(pipeline_run.dataset_id)
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to run this pipeline step")
    
    # Reset step status
    await pipeline_repo.update_pipeline_step_status(
        step_id, 
        status="running",
        start_time=datetime.utcnow(),
        end_time=None,
        results={},
        error_message=None
    )
    
    # Run step in background
    background_tasks.add_task(
        run_pipeline_step,
        pipeline_repo,
        dataset_repo,
        pipeline_run.id,
        step_id,
        params
    )
    
    return await pipeline_repo.get_pipeline_step(step_id)

@router.get("/runs", response_model=List[PipelineRun])
async def list_pipeline_runs(
    dataset_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user_or_api_key),
    pipeline_repo = Depends(get_pipeline_repository)
):
    """List pipeline runs, optionally filtered by dataset."""
    # If dataset_id is provided, check user has access
    if dataset_id:
        dataset = await pipeline_repo.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Get pipeline runs
    runs = await pipeline_repo.get_pipeline_runs(
        user_id=current_user.id,
        dataset_id=dataset_id,
        skip=skip,
        limit=limit
    )
    
    # Load steps for each run
    result = []
    for run in runs:
        steps = await pipeline_repo.get_pipeline_steps(run.id)
        run_dict = run.dict()
        run_dict["steps"] = steps
        result.append(PipelineRun(**run_dict))
    
    return result
