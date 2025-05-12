import logging
import asyncio
import json
import os
from typing import Dict, Any, Optional, List
import pandas as pd
import asyncpg
from datetime import datetime

from api.config import get_db_config
from api.utils.validation import validate_dataset_schema
from api.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class DataLoaderService:
    """Service for loading data into the system"""
    
    def __init__(self):
        self.pool = None
        
    async def initialize(self):
        """Initialize the database connection pool"""
        if self.pool is None:
            try:
                db_config = get_db_config()
                self.pool = await asyncpg.create_pool(**db_config)
                logger.info("Data loader service initialized with asyncpg connection pool")
            except Exception as e:
                logger.error(f"Failed to initialize data loader service: {str(e)}")
                raise
    
    async def load_dataset(self, file_path: str, dataset_name: str, file_format: str = "csv") -> Dict[str, Any]:
        """
        Load a dataset from a file into the system
        
        Args:
            file_path: Path to the dataset file
            dataset_name: Name for the dataset
            file_format: Format of the file (csv, json, etc.)
            
        Returns:
            Dictionary with dataset information
        """
        await self.initialize()
        
        try:
            # Load the dataset based on format
            if file_format.lower() == "csv":
                df = pd.read_csv(file_path)
            elif file_format.lower() == "json":
                df = pd.read_json(file_path)
            elif file_format.lower() == "excel" or file_format.lower() == "xlsx":
                df = pd.read_excel(file_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {file_format}"
                }
            
            # Basic validation
            if df.empty:
                return {
                    "success": False,
                    "error": "Dataset is empty"
                }
            
            # Get basic dataset info
            row_count = len(df)
            column_count = len(df.columns)
            columns = df.columns.tolist()
            
            # Determine column types
            column_types = {}
            for col in columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    column_types[col] = "numeric"
                elif pd.api.types.is_datetime64_dtype(df[col]):
                    column_types[col] = "datetime"
                else:
                    column_types[col] = "text"
            
            # Create dataset record in database
            async with self.pool.acquire() as conn:
                dataset_id = await conn.fetchval(
                    """
                    INSERT INTO datasets (name, row_count, column_count, file_path, file_format, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                    RETURNING id
                    """,
                    dataset_name,
                    row_count,
                    column_count,
                    file_path,
                    file_format
                )
                
                # Store dataset metadata
                await conn.execute(
                    """
                    INSERT INTO dataset_metadata (dataset_id, metadata)
                    VALUES ($1, $2)
                    """,
                    dataset_id,
                    json.dumps({
                        "columns": columns,
                        "column_types": column_types,
                        "row_count": row_count,
                        "file_format": file_format
                    })
                )
            
            # Validate dataset schema
            validation_result = validate_dataset_schema(df)
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "name": dataset_name,
                "row_count": row_count,
                "column_count": column_count,
                "columns": columns,
                "column_types": column_types,
                "validation": validation_result
            }
            
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to load dataset: {str(e)}"
            }
    
    async def get_dataset_preview(self, dataset_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Get a preview of a dataset
        
        Args:
            dataset_id: ID of the dataset
            limit: Maximum number of rows to return
            
        Returns:
            Dictionary with dataset preview data
        """
        await self.initialize()
        
        try:
            async with self.pool.acquire() as conn:
                # Get dataset info
                dataset = await conn.fetchrow(
                    """
                    SELECT id, name, row_count, column_count, file_path, file_format
                    FROM datasets
                    WHERE id = $1
                    """,
                    dataset_id
                )
                
                if not dataset:
                    return {
                        "success": False,
                        "error": f"Dataset with ID {dataset_id} not found"
                    }
                
                # Get dataset metadata
                metadata_row = await conn.fetchrow(
                    """
                    SELECT metadata
                    FROM dataset_metadata
                    WHERE dataset_id = $1
                    """,
                    dataset_id
                )
                
                metadata = json.loads(metadata_row["metadata"]) if metadata_row else {}
                
                # Load the dataset file for preview
                file_path = dataset["file_path"]
                file_format = dataset["file_format"]
                
                if file_format.lower() == "csv":
                    df = pd.read_csv(file_path, nrows=limit)
                elif file_format.lower() == "json":
                    df = pd.read_json(file_path)
                    df = df.head(limit)
                elif file_format.lower() == "excel" or file_format.lower() == "xlsx":
                    df = pd.read_excel(file_path, nrows=limit)
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported file format: {file_format}"
                    }
                
                # Convert preview data to list of dictionaries
                preview_data = df.to_dict(orient="records")
                
                return {
                    "success": True,
                    "dataset_id": dataset_id,
                    "name": dataset["name"],
                    "row_count": dataset["row_count"],
                    "column_count": dataset["column_count"],
                    "columns": metadata.get("columns", []),
                    "column_types": metadata.get("column_types", {}),
                    "preview_data": preview_data
                }
                
        except Exception as e:
            logger.error(f"Error getting dataset preview: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get dataset preview: {str(e)}"
            }
