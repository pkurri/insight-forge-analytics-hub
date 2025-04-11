
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, Optional, List

from api.models.dataset import Dataset
from api.repositories.dataset_repository import get_dataset_repository
from api.services.analytics_service import (
    get_data_profile,
    detect_anomalies,
    query_vector_database,
    create_vector_embeddings
)
from api.routes.auth_router import get_current_user_or_api_key

router = APIRouter()

@router.get("/{dataset_id}/profile")
async def profile_dataset(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Generate and return data profile for a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Get data profile
    profile_data = await get_data_profile(dataset_id)
    return profile_data

@router.post("/{dataset_id}/anomalies")
async def detect_dataset_anomalies(
    dataset_id: int,
    config: Dict[str, Any] = Body({}),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Detect and return anomalies in a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Detect anomalies
    anomalies = await detect_anomalies(dataset_id, config)
    return anomalies

@router.post("/{dataset_id}/vectorize")
async def vectorize_dataset(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Create vector embeddings for a dataset and store in vector database."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Create vector embeddings
    result = await create_vector_embeddings(dataset_id)
    return result

@router.post("/{dataset_id}/query")
async def query_dataset(
    dataset_id: int,
    query: str = Body(..., embed=True),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Query a dataset using natural language and vector search."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.user_id and dataset.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    
    # Query vector database
    results = await query_vector_database(dataset_id, query)
    return results
