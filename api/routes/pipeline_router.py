from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, UploadFile, Form, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import tempfile
import os
import shutil

from models.dataset import PipelineRun, PipelineStep, PipelineRunStatus, PipelineStepType
from repositories.pipeline_repository import get_pipeline_repository
from repositories.dataset_repository import get_dataset_repository
from services.pipeline_service import run_pipeline_step
from routes.auth_router import get_current_user_or_api_key
from services.file_service import process_uploaded_file
from services.data_cleaning_service import DataCleaningService
from services.validation_service import ValidationService
from services.database_service import DatabaseService
from services.analytics_service import get_data_profile, detect_anomalies
from config.settings import get_settings
from services.ai_models import AIModelService
from services.vector_service import vector_service

settings = get_settings()

# Initialize services
data_cleaning_service = DataCleaningService()
validation_service = ValidationService()
database_service = DatabaseService({
    'user': settings.DB_USER,
    'password': settings.DB_PASSWORD,
    'database': settings.DB_NAME,
    'host': settings.DB_HOST,
    'port': settings.DB_PORT
})
ai_model_service = AIModelService()

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
    rules_path: Optional[str] = Form(None),
    clean_data: bool = Form(True),
    validate_data: bool = Form(True),
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
    
    # Process the file and get DataFrame
    df = await process_uploaded_file(file_path, file_type)
    
    # Clean data if requested
    if clean_data:
        df, cleaning_metadata = await data_cleaning_service.clean_data(df)
    
    # Validate data if requested
    validation_results = None
    if validate_data:
        validation_results = await validation_service.validate_data(
            df,
            rules_path=rules_path
        )
    
    # Generate data profile
    profile_data = await get_data_profile(df)
    
    # Detect anomalies
    anomalies = await detect_anomalies(df)
    
    # Store data in vector database
    await database_service.store_dataframe(df, f'dataset_{timestamp}')
    
    # Create dataset record
    dataset = await dataset_repo.create_dataset(
        dataset={
            "name": name,
            "description": description or f"Uploaded {file_type} file: {file.filename}",
            "file_type": file_type,
            "cleaning_metadata": cleaning_metadata if clean_data else None,
            "validation_results": validation_results,
            "profile_data": profile_data,
            "anomalies": anomalies
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
    from services.external_data_service import fetch_from_api
    
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
    from services.external_data_service import fetch_from_database
    
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
    from services.validation_service import validate_dataset
    
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
    from services.transformation_service import transform_dataset
    
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
    from services.enrichment_service import enrich_dataset
    
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
    from services.loading_service import load_dataset
    
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
