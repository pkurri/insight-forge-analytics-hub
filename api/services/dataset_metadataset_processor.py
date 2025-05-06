"""
Dataset Metadataset Processor Module

This module provides functions for processing dataset metadatasets.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

async def get_dataset_metadataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Get dataset metadataset information.
    
    Args:
        dataset_id: ID of the dataset
        
    Returns:
        Dict containing dataset information or None if not found
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import dataset_repository
        
        # Get dataset info
        dataset_info = await dataset_repository.get_dataset(dataset_id)
        if not dataset_info:
            return None
            
        return dataset_info
    except Exception as e:
        logger.error(f"Error getting dataset metadataset: {str(e)}")
        return None

async def process_dataset_metadataset(dataset_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process dataset metadataset metadata.
    
    Args:
        dataset_id: ID of the dataset
        metadata: Dataset metadata to process
        
    Returns:
        Dict containing processed metadata
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import dataset_repository
        
        # Process metadata
        processed_metadata = {
            "dataset_id": dataset_id,
            "metadata": metadata,
            "processed_at": pd.Timestamp.now().isoformat()
        }
        
        # Store processed metadata
        await dataset_repository.update_dataset_metadata(dataset_id, processed_metadata)
        
        return processed_metadata
    except Exception as e:
        logger.error(f"Error processing dataset metadataset: {str(e)}")
        return {
            "dataset_id": dataset_id,
            "error": str(e)
        } 