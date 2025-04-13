
"""
Pipeline Test API Router

This module provides API endpoints for testing the data pipeline process
including loading, validating, processing, and storing data.
"""
from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Form, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import shutil
import logging

from api.services.pipeline_data_loader import (
    load_data_file, 
    validate_dataset, 
    prepare_for_vectors,
    store_in_pgvector, 
    test_pipeline
)
from api.services.cache_service import cache_response, get_cached_response

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Helper functions for better separation of concerns
async def _handle_file_upload(file: UploadFile) -> str:
    """Handle file upload and save it to disk"""
    upload_dir = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    logger.info(f"File saved at: {file_path}")
    return file_path

def _determine_file_type(file_name: str, provided_type: Optional[str] = None) -> str:
    """Determine file type based on extension or provided type"""
    if provided_type:
        return provided_type
    
    return os.path.splitext(file_name)[1].lower().lstrip('.')

@router.post("/test", response_model=Dict[str, Any])
async def test_pipeline_process(
    file: UploadFile = File(...),
    file_type: Optional[str] = Form(None)
):
    """
    Test the entire data pipeline process
    
    This endpoint handles:
    1. File upload
    2. Data loading
    3. Schema detection and validation
    4. Vector preparation
    5. Storage in PostgreSQL with pgvector
    
    Returns:
        Complete processing results
    """
    # Check cache for identical file to avoid redundant processing
    cache_key = f"pipeline_test:{file.filename}:{file.size}"
    cached_result = get_cached_response(cache_key)
    
    if cached_result:
        logger.info(f"Using cached result for file: {file.filename}")
        return cached_result
    
    # Handle file upload
    file_path = await _handle_file_upload(file)
    
    # Determine file type
    detected_file_type = _determine_file_type(file.filename, file_type)
    
    # Run pipeline test
    result = await test_pipeline(file_path, detected_file_type)
    
    # Cache successful results
    if result.get("success", False):
        cache_response(cache_key, result, 3600)  # Cache for 1 hour
    
    return result

@router.post("/load", response_model=Dict[str, Any])
async def load_data(
    file: UploadFile = File(...),
    file_type: Optional[str] = Form(None),
    options: Optional[Dict[str, Any]] = Body({})
):
    """
    Load data from a file with AI schema detection
    
    Returns:
        Loading results with sample data and detected schema
    """
    # Handle file upload
    file_path = await _handle_file_upload(file)
    
    # Determine file type
    detected_file_type = _determine_file_type(file.filename, file_type)
    
    # Load data
    result = await load_data_file(file_path, detected_file_type, options)
    
    return result

@router.post("/{dataset_id}/validate", response_model=Dict[str, Any])
async def validate_data(
    dataset_id: str,
    options: Optional[Dict[str, Any]] = Body({})
):
    """
    Validate data using AI-detected schema
    
    Returns:
        Validation results
    """
    result = await validate_dataset(dataset_id, options)
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to validate data")
        )
    
    return result

@router.post("/{dataset_id}/vector-prepare", response_model=Dict[str, Any])
async def prepare_vector_data(
    dataset_id: str,
    text_columns: Optional[List[str]] = Body(None),
    options: Optional[Dict[str, Any]] = Body({})
):
    """
    Prepare data for vector database storage
    
    Returns:
        Vector preparation results with sample embeddings
    """
    result = await prepare_for_vectors(dataset_id, text_columns, options)
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to prepare vector data")
        )
    
    return result

@router.post("/{dataset_id}/store", response_model=Dict[str, Any])
async def store_data(
    dataset_id: str,
    options: Optional[Dict[str, Any]] = Body({})
):
    """
    Store data in PostgreSQL with pgvector extension
    
    Returns:
        Storage results
    """
    result = await store_in_pgvector(dataset_id, options)
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to store data")
        )
    
    return result
