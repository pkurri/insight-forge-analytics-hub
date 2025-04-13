
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

from api.services.pipeline_data_loader import (
    load_data_file, 
    validate_dataset, 
    prepare_for_vectors,
    store_in_pgvector, 
    test_pipeline
)

router = APIRouter()

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
    # Create upload directory if it doesn't exist
    upload_dir = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Determine file type if not provided
    if not file_type:
        file_type = os.path.splitext(file.filename)[1].lower().lstrip('.')
    
    # Run pipeline test
    result = await test_pipeline(file_path, file_type)
    
    # Clean up file if requested
    # In production, you might want to keep the file for debugging
    
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
    # Create upload directory if it doesn't exist
    upload_dir = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Determine file type if not provided
    if not file_type:
        file_type = os.path.splitext(file.filename)[1].lower().lstrip('.')
    
    # Load data
    result = await load_data_file(file_path, file_type, options)
    
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
