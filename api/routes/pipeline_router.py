
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, File, UploadFile, Form, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import tempfile
import os
import shutil

from api.models.dataset import PipelineRun, PipelineStep, PipelineRunStatus, PipelineStepType
from api.repositories.pipeline_repository import get_pipeline_repository
from api.repositories.dataset_repository import get_dataset_repository
from api.services.pipeline_service import run_pipeline_step
from api.routes.auth_router import get_current_user_or_api_key
from api.services.file_service import process_uploaded_file

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

@router.post("/upload", response_model=Dict[str, Any])
async def upload_data_to_pipeline(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    file_type: str = Form(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Upload a file to process through the pipeline."""
    # Create upload directory if it doesn't exist
    upload_dir = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{timestamp}_{current_user.id}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create dataset name if not provided
    if not name:
        name = f"{file.filename} - {timestamp}"
    
    # Create dataset record
    dataset = await dataset_repo.create_dataset(
        dataset={
            "name": name,
            "description": description or f"Uploaded {file_type} file: {file.filename}",
            "file_type": file_type
        },
        user_id=current_user.id,
        file_path=file_path
    )
    
    # Process the file in background
    background_tasks.add_task(
        process_uploaded_file,
        dataset.id,
        file_path,
        file_type
    )
    
    return {
        "dataset_id": str(dataset.id),
        "filename": file.filename,
        "file_type": file_type,
        "size": os.path.getsize(file_path),
        "upload_time": datetime.utcnow().isoformat()
    }

@router.post("/fetch-from-api", response_model=Dict[str, Any])
async def fetch_data_from_api(
    background_tasks: BackgroundTasks,
    api_endpoint: str = Body(...),
    output_format: str = Body(...),
    auth_config: Optional[Dict[str, Any]] = Body({}),
    name: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Fetch data from an external API for pipeline processing."""
    from api.services.external_data_service import fetch_from_api
    
    # Create dataset name if not provided
    if not name:
        name = f"API Data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Create temporary dataset record
    dataset = await dataset_repo.create_dataset(
        dataset={
            "name": name,
            "description": description or f"Data fetched from API: {api_endpoint}",
            "file_type": output_format,
            "source_type": "api"
        },
        user_id=current_user.id,
        file_path=None  # Will be updated once data is fetched
    )
    
    # Fetch the data in background
    background_tasks.add_task(
        fetch_from_api,
        dataset.id,
        api_endpoint,
        output_format,
        auth_config,
        dataset_repo
    )
    
    return {
        "dataset_id": str(dataset.id),
        "source": api_endpoint,
        "file_type": output_format,
        "status": "fetching",
        "fetch_time": datetime.utcnow().isoformat()
    }

@router.post("/fetch-from-db", response_model=Dict[str, Any])
async def fetch_data_from_database(
    background_tasks: BackgroundTasks,
    connection_id: str = Body(...),
    query: Optional[str] = Body(None),
    table_name: Optional[str] = Body(None),
    output_format: str = Body(...),
    name: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Fetch data from a database for pipeline processing."""
    from api.services.external_data_service import fetch_from_database
    
    if not query and not table_name:
        raise HTTPException(
            status_code=400,
            detail="Either query or table_name must be provided"
        )
    
    # Create dataset name if not provided
    if not name:
        name = f"DB Data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Create temporary dataset record
    dataset = await dataset_repo.create_dataset(
        dataset={
            "name": name,
            "description": description or f"Data fetched from database: {connection_id}",
            "file_type": output_format,
            "source_type": "database"
        },
        user_id=current_user.id,
        file_path=None  # Will be updated once data is fetched
    )
    
    # Fetch the data in background
    background_tasks.add_task(
        fetch_from_database,
        dataset.id,
        connection_id,
        query,
        table_name,
        output_format,
        dataset_repo
    )
    
    return {
        "dataset_id": str(dataset.id),
        "connection": connection_id,
        "query": query,
        "table": table_name,
        "file_type": output_format,
        "status": "fetching",
        "fetch_time": datetime.utcnow().isoformat()
    }

@router.post("/{dataset_id}/validate", response_model=Dict[str, Any])
async def validate_data_in_pipeline(
    dataset_id: int,
    config: Optional[Dict[str, Any]] = Body({}),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Validate data in the pipeline."""
    from api.services.validation_service import validate_dataset
    
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Run validation
    validation_results = await validate_dataset(dataset_id, config)
    
    return {
        "dataset_id": str(dataset_id),
        "validation_results": validation_results
    }

@router.post("/{dataset_id}/transform", response_model=Dict[str, Any])
async def transform_data_in_pipeline(
    dataset_id: int,
    config: Optional[Dict[str, Any]] = Body({}),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Transform data in the pipeline."""
    from api.services.transformation_service import transform_dataset
    
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Run transformation
    transformation_results = await transform_dataset(dataset_id, config)
    
    return {
        "dataset_id": str(dataset_id),
        "transformation_results": transformation_results
    }

@router.post("/{dataset_id}/enrich", response_model=Dict[str, Any])
async def enrich_data_in_pipeline(
    dataset_id: int,
    config: Optional[Dict[str, Any]] = Body({}),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Enrich data in the pipeline."""
    from api.services.enrichment_service import enrich_dataset
    
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Run enrichment
    enrichment_results = await enrich_dataset(dataset_id, config)
    
    return {
        "dataset_id": str(dataset_id),
        "enrichment_results": enrichment_results
    }

@router.post("/{dataset_id}/load", response_model=Dict[str, Any])
async def load_data_in_pipeline(
    dataset_id: int,
    destination: str = Body(...),
    config: Optional[Dict[str, Any]] = Body({}),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Load processed data to destination."""
    from api.services.loading_service import load_dataset
    
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Run data loading
    loading_results = await load_dataset(dataset_id, destination, config)
    
    return {
        "dataset_id": str(dataset_id),
        "destination": destination,
        "loading_results": loading_results
    }
