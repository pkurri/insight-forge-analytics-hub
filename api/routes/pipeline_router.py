from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, UploadFile, Form, Query, Body
from typing import Dict, Any, Optional, List
from datetime import datetime
import tempfile
import os
import shutil
import json
import pandas as pd

from models.dataset import PipelineRun, PipelineStep, PipelineRunStatus, PipelineStepType, DatasetCreate, DatasetStatus, SourceType, FileType
from repositories.pipeline_repository import PipelineRepository
from repositories.dataset_repository import DatasetRepository
from services.pipeline_service import pipeline_service
from routes.auth_router import get_current_user_or_api_key
from services.file_service import process_uploaded_file
from config.settings import get_settings
from services.vector_service import vector_service
from services.external_data_service import fetch_from_api, fetch_from_database

settings = get_settings()

# Initialize repositories
dataset_repo = DatasetRepository()
pipeline_repo = PipelineRepository()

router = APIRouter()

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional

class OpenEvalsEvaluationModel(BaseModel):
    score: Optional[float] = None
    summary: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ErrorResponseModel(BaseModel):
    error: str

@router.get(
    "/openevals/step-evaluation/{run_id}/{step_name}",
    response_model=OpenEvalsEvaluationModel,
    responses={
        200: {"description": "OpenEvals evaluation result for the pipeline step"},
        403: {"model": ErrorResponseModel, "description": "Not authorized"},
        404: {"model": ErrorResponseModel, "description": "Pipeline run, step, or evaluation not found"}
    },
    summary="Get OpenEvals evaluation for a pipeline step",
    description="Fetch the OpenEvals evaluation result (data quality, business rules, etc.) for a specific step in a pipeline run. Results are structured for UI consumption."
)
async def get_openevals_step_evaluation(
    run_id: int,
    step_name: str,
    pipeline_repo = Depends(get_pipeline_repository),
    current_user = Depends(get_current_user_or_api_key)
):
    """
    Get OpenEvals evaluation for a specific pipeline step in a pipeline run.
    Returns evaluation results and error info if applicable.
    """
    pipeline_run = await pipeline_repo.get_pipeline_run_with_steps(run_id)
    if not pipeline_run:
        return JSONResponse(status_code=404, content={"error": "Pipeline run not found"})
    dataset = await pipeline_repo.get_dataset_from_pipeline_run(run_id)
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        return JSONResponse(status_code=403, content={"error": "Not authorized to access this pipeline run"})
    step = next((s for s in pipeline_run.steps if s.step_name == step_name), None)
    if not step:
        return JSONResponse(status_code=404, content={"error": "Step not found in pipeline run"})
    # Step status with OpenEvals evaluation is assumed to be stored in step.status_metadata or similar
    eval_result = getattr(step, "status_metadata", {}).get("openevals_evaluation") if hasattr(step, "status_metadata") else None
    if not eval_result:
        return JSONResponse(status_code=404, content={"error": "No OpenEvals evaluation found for this step"})
    return eval_result

@router.get(
    "/openevals/pipeline-evaluations/{run_id}",
    response_model=Dict[str, OpenEvalsEvaluationModel],
    responses={
        200: {"description": "All OpenEvals evaluations for the pipeline run, keyed by step name."},
        403: {"model": ErrorResponseModel, "description": "Not authorized."},
        404: {"model": ErrorResponseModel, "description": "Pipeline run or evaluations not found."}
    },
    summary="Get all OpenEvals evaluations for a pipeline run",
    description="Fetch all OpenEvals evaluation results (data quality, business rules, etc.) for every step in a pipeline run. Results are structured for UI consumption."
)
async def get_openevals_pipeline_evaluations(
    run_id: int,
    pipeline_repo = Depends(get_pipeline_repository),
    current_user = Depends(get_current_user_or_api_key)
):
    """
    Get all OpenEvals evaluations for a pipeline run (all steps).
    Returns a dict of step_name -> evaluation.
    """
    pipeline_run = await pipeline_repo.get_pipeline_run_with_steps(run_id)
    if not pipeline_run:
        return JSONResponse(status_code=404, content={"error": "Pipeline run not found"})
    dataset = await pipeline_repo.get_dataset_from_pipeline_run(run_id)
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        return JSONResponse(status_code=403, content={"error": "Not authorized to access this pipeline run"})
    evals = {}
    for step in pipeline_run.steps:
        eval_result = getattr(step, "status_metadata", {}).get("openevals_evaluation") if hasattr(step, "status_metadata") else None
        if eval_result:
            evals[step.step_name] = eval_result
    if not evals:
        return JSONResponse(status_code=404, content={"error": "No OpenEvals evaluations found for this pipeline run"})
    return evals

from fastapi import Body
from services.pipeline_service import DataPipeline, run_pipeline_step
import asyncio

@router.post("/dynamic-pipeline")
async def run_dynamic_pipeline_endpoint(
    dataset_id: int = Body(...),
    steps: list = Body(...),
    rules: dict = Body({}),
    parallelizable: list = Body([]),
    custom_transform_code: str = Body(None),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Run a dynamic pipeline with user-specified steps, rules, and parallelization."""
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    df = await process_uploaded_file(dataset["file_path"], dataset.get("file_type", "csv"))
    pipeline = DataPipeline()
    # If custom transform code is provided, dynamically build a function
    transform_func = None
    if custom_transform_code:
        exec_globals = {}
        exec(custom_transform_code, exec_globals)
        transform_func = exec_globals.get("transform_func")
    # Run pipeline
    results = await pipeline.run_dynamic_pipeline(
        df,
        steps,
        rules=rules,
        parallelizable=parallelizable,
        transform_func=transform_func
    )
    return results

@router.get("/pipeline-status/{run_id}")
async def get_pipeline_status(run_id: int, pipeline_repo = Depends(get_pipeline_repository), current_user = Depends(get_current_user_or_api_key)):
    """Get status and progress of a pipeline run."""
    pipeline_run = await pipeline_repo.get_pipeline_run_with_steps(run_id)
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    # Optionally filter/format status here
    return pipeline_run

@router.post("/pipeline-retry/{run_id}")
async def retry_failed_steps(run_id: int, pipeline_repo = Depends(get_pipeline_repository), dataset_repo = Depends(get_dataset_repository), current_user = Depends(get_current_user_or_api_key)):
    """Retry failed steps in a pipeline run."""
    pipeline_run = await pipeline_repo.get_pipeline_run_with_steps(run_id)
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    dataset = await pipeline_repo.get_dataset_from_pipeline_run(run_id)
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this pipeline run")
    df = await process_uploaded_file(dataset["file_path"], dataset.get("file_type", "csv"))
    pipeline = DataPipeline()
    failed_steps = [step for step in pipeline_run.steps if step.status == "failed"]
    results = {}
    for step in failed_steps:
        try:
            results[step.step_name] = await run_pipeline_step(pipeline, step.step_name, df)
        except Exception as e:
            results[step.step_name] = str(e)
    return {"retried": results}

@router.post("/pipeline-resume/{run_id}")
async def resume_pipeline(run_id: int, pipeline_repo = Depends(get_pipeline_repository), dataset_repo = Depends(get_dataset_repository), current_user = Depends(get_current_user_or_api_key)):
    """Resume a pipeline run from the last incomplete step."""
    pipeline_run = await pipeline_repo.get_pipeline_run_with_steps(run_id)
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    dataset = await pipeline_repo.get_dataset_from_pipeline_run(run_id)
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this pipeline run")
    df = await process_uploaded_file(dataset["file_path"], dataset.get("file_type", "csv"))
    pipeline = DataPipeline()
    steps = [step for step in pipeline_run.steps if step.status not in ("completed", "skipped")]
    results = {}
    for step in steps:
        try:
            results[step.step_name] = await run_pipeline_step(pipeline, step.step_name, df)
        except Exception as e:
            results[step.step_name] = str(e)
    return {"resumed": results}

@router.post("/{dataset_id}/run", response_model=PipelineRun)
async def start_pipeline_run(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    pipeline_repo = Depends(get_pipeline_repository),
    dataset_repo = Depends(get_dataset_repository)
):
    """Initialize a new pipeline run for a dataset. No steps are automatically started."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Create pipeline run
    pipeline_run = await pipeline_repo.create_pipeline_run(dataset_id)
    
    # Add pipeline steps (all in 'pending' state)
    steps = []
    for step_type in [
        PipelineStepType.VALIDATE,
        PipelineStepType.TRANSFORM,
        PipelineStepType.ENRICH,
        PipelineStepType.LOAD
    ]:
        step = await pipeline_repo.create_pipeline_step(
            pipeline_run_id=pipeline_run.id,
            step_name=step_type,
            status=PipelineRunStatus.PENDING
        )
        steps.append(step)
    
    return pipeline_run

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
    """Run a specific pipeline step. Requires explicit user initiation."""
    # Get the step
    step = await pipeline_repo.get_pipeline_step(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Pipeline step not found")
    
    # Get the pipeline run
    pipeline_run = await pipeline_repo.get_pipeline_run_with_steps(step.pipeline_run_id)
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    
    # Check authorization
    dataset = await pipeline_repo.get_dataset_from_pipeline_run(pipeline_run.id)
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this pipeline run")
    
    # Check if step is in a valid state to run
    if step.status not in [PipelineRunStatus.PENDING, PipelineRunStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot run step in {step.status} state. Step must be in PENDING or FAILED state."
        )
    
    # Update step status to running
    await pipeline_repo.update_pipeline_step_status(
        step_id,
        PipelineRunStatus.RUNNING,
        {"params": params}
    )
    
    # Run the step in the background
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
    
async def upload_data_to_pipeline(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    file_type: Optional[FileType] = Form(None),
    api_config: Optional[str] = Form(None),
    db_config: Optional[str] = Form(None),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    user_id: int = Form(...)
):
    """Upload data to the pipeline from various sources."""
    try:
        # Create dataset record
        dataset_create = DatasetCreate(
            name=name,
            description=description or "",
            status=DatasetStatus.PENDING
        )
        
        # Handle different source types
        if file:
            # File upload
            dataset_create.source_type = SourceType.FILE
            dataset_create.file_type = file_type or FileType.CSV
            
            # Save file
            file_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file.filename}")
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
                
            # Set source info
            dataset_create.source_info = {
                "file_path": file_path,
                "original_filename": file.filename
            }
            
        elif api_config:
            # API source
            dataset_create.source_type = SourceType.API
            dataset_create.file_type = file_type or FileType.JSON
            
            # Parse API config
            api_config_dict = json.loads(api_config)
            dataset_create.source_info = api_config_dict
            
        elif db_config:
            # Database source
            dataset_create.source_type = SourceType.DATABASE
            dataset_create.file_type = file_type or FileType.CSV
            
            # Parse DB config
            db_config_dict = json.loads(db_config)
            dataset_create.source_info = db_config_dict
            
        else:
            return {
                "success": False,
                "error": "No data source provided. Please provide a file, API config, or database config."
            }
        
        # Create dataset
        dataset = await dataset_repo.create_dataset(dataset_create, user_id)
        
        # Process file if uploaded
        if file:
            background_tasks.add_task(
                pipeline_service.process_uploaded_file,
                dataset.id,
                file_path,
                dataset_create.file_type
            )
        elif api_config:
            # Add background task to fetch data from API
            background_tasks.add_task(
                fetch_from_api,
                api_config_dict,
                dataset.id
            )
        elif db_config:
            # Add background task to fetch data from database
            background_tasks.add_task(
                fetch_from_database,
                db_config_dict,
                dataset.id
            )
        
        return {
            "success": True,
            "dataset_id": dataset.id,
            "name": dataset.name,
            "status": dataset.status
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/pipeline/business-rules/{dataset_id}", response_model=Dict[str, Any])
async def apply_business_rules(
    dataset_id: int,
    rule_ids: List[str] = Body(...)
):
    """Apply business rules to a dataset."""
    result = await pipeline_service.apply_business_rules(str(dataset_id), rule_ids)
    return result

@router.post("/pipeline/transform/{dataset_id}", response_model=Dict[str, Any])
async def transform_data(
    dataset_id: int
):
    """Transform data using defined transformations."""
    result = await pipeline_service.transform_data(dataset_id)
    return result

@router.post("/pipeline/enrich/{dataset_id}", response_model=Dict[str, Any])
async def enrich_data(
    dataset_id: int
):
    """Enrich data with external sources or derived fields."""
    result = await pipeline_service.enrich_data(dataset_id)
    return result

@router.post("/pipeline/load/{dataset_id}", response_model=Dict[str, Any])
async def load_to_vector_db(
    dataset_id: int
):
    """Load data to vector database."""
    result = await pipeline_service.load_to_vector_db(dataset_id)
    return result

@router.get("/pipeline/sample/{dataset_id}", response_model=Dict[str, Any])
async def get_sample_data(
    dataset_id: int,
    max_rows: int = 100
):
    """Get a sample of data from a dataset for preview and rule testing."""
    try:
        # Get dataset
        dataset = await dataset_repo.get_dataset(dataset_id)
        if not dataset:
            return {"success": False, "error": f"Dataset with ID {dataset_id} not found"}
        
        # Extract sample data
        file_path = dataset.source_info.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return {"success": False, "error": "Dataset file not found"}
        
        result = await pipeline_service.extract_sample_data(
            file_path,
            dataset.file_type,
            max_rows
        )
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/pipeline/step/{dataset_id}/{step_type}", response_model=Dict[str, Any])
async def run_pipeline_step(
    dataset_id: int,
    step_type: PipelineStepType
):
    """Run a specific pipeline step on a dataset."""
    result = await pipeline_service.run_pipeline_step(dataset_id, step_type)
    return result

@router.get("/pipeline/runs/{dataset_id}", response_model=Dict[str, Any])
async def get_pipeline_runs(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100
):
    """Get pipeline runs for a dataset."""
    runs = await pipeline_repo.get_pipeline_runs(dataset_id, skip, limit)
    
    return {
        "dataset_id": dataset_id,
        "runs": [
            {
                "id": run["id"],
                "status": run["status"],
                "start_time": run["start_time"],
                "end_time": run["end_time"],
                "steps": [
                    {
                        "id": step["id"],
                        "step_type": step["step_type"],
                        "status": step["status"],
                        "start_time": step["start_time"],
                        "end_time": step["end_time"],
                        "metadata": step["pipeline_metadata"]
                    }
                    for step in run["steps"]
                ]
            }
            for run in runs
        ]
    }
