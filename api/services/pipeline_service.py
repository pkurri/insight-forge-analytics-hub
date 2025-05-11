"""
Pipeline Service Module

This module handles data pipeline processing for datasets, coordinating the different stages
of the pipeline including data loading, transformation, and vector embedding.
"""

import logging
import pandas as pd
import json
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from api.repositories.pipeline_repository import PipelineRepository
from api.repositories.dataset_repository import DatasetRepository
from api.repositories.suggestions_repository import SuggestionsRepository
from api.services.pipeline_stages.data_loader import DataLoaderService
from api.services.pipeline_stages.data_transformer import DataTransformerService
from api.services.pipeline_stages.vector_embedder import VectorEmbedderService
from api.services.ai_service import analyze_dataset_with_rag
from api.services.data_validation_service import DataValidationService
from models.pipeline import PipelineStep, PipelineStatus, PipelineStepType, PipelineRunStatus
from models.dataset import DatasetStatus, FileType
from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class PipelineService:
    def __init__(self):
        self.data_loader_service = DataLoaderService()
        self.data_transformer_service = DataTransformerService()
        self.vector_embedder_service = VectorEmbedderService()
        self.dataset_repository = DatasetRepository()
        self.pipeline_repository = PipelineRepository()
        self.suggestions_repository = SuggestionsRepository()
        
    async def process_dataset(self, dataset_id: int, pipeline_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a dataset through the complete pipeline.
        
        Args:
            dataset_id: ID of the dataset to process
            pipeline_config: Optional configuration for the pipeline
            
        Returns:
            Dictionary with the results of the pipeline execution
        """
        pipeline_config = pipeline_config or {}
        result = {
            "dataset_id": dataset_id,
            "success": False,
            "steps": [],
            "errors": []
        }
        
        try:
            # Update dataset status to processing
            await self.dataset_repository.update_dataset_status(dataset_id, DatasetStatus.PROCESSING)
            
            # Create a new pipeline run
            pipeline_run_id = await self.pipeline_repository.create_pipeline_run({
                "dataset_id": dataset_id,
                "status": PipelineStatus.RUNNING,
                "start_time": datetime.now(),
                "config": pipeline_config
            })
            
            # Step 1: Load data
            logger.info(f"Starting data loading for dataset {dataset_id}")
            load_result = await self.load_data(dataset_id, pipeline_config.get("loader", {}))
            
            if not load_result["success"]:
                result["errors"].append({
                    "step": "data_loading",
                    "error": load_result["error"]
                })
                await self._handle_pipeline_failure(dataset_id, pipeline_run_id, "data_loading", load_result["error"])
                return result
                
            result["steps"].append({
                "name": "data_loading",
                "success": True,
                "details": load_result.get("details", {})
            })
            
            # Step 2: Transform data
            logger.info(f"Starting data transformation for dataset {dataset_id}")
            transform_result = await self.transform_data(dataset_id, pipeline_config.get("transformer", {}))
            
            if not transform_result["success"]:
                result["errors"].append({
                    "step": "data_transformation",
                    "error": transform_result["error"]
                })
                await self._handle_pipeline_failure(dataset_id, pipeline_run_id, "data_transformation", transform_result["error"])
                return result
                
            result["steps"].append({
                "name": "data_transformation",
                "success": True,
                "details": transform_result.get("details", {})
            })
            
            # Step 3: Generate vector embeddings
            logger.info(f"Starting vector embedding for dataset {dataset_id}")
            embedding_result = await self.generate_embeddings(dataset_id, pipeline_config.get("embedder", {}))
            
            if not embedding_result["success"]:
                result["errors"].append({
                    "step": "vector_embedding",
                    "error": embedding_result["error"]
                })
                await self._handle_pipeline_failure(dataset_id, pipeline_run_id, "vector_embedding", embedding_result["error"])
                return result
                
            result["steps"].append({
                "name": "vector_embedding",
                "success": True,
                "details": embedding_result.get("details", {})
            })
            
            # Step 4: Generate insights and suggestions using RAG
            logger.info(f"Generating insights for dataset {dataset_id}")
            insights_result = await self.generate_insights(dataset_id)
            
            if not insights_result["success"]:
                # Non-critical error, continue but log the error
                result["errors"].append({
                    "step": "insights_generation",
                    "error": insights_result["error"]
                })
            else:
                result["steps"].append({
                    "name": "insights_generation",
                    "success": True,
                    "details": insights_result.get("details", {})
                })
            
            # Update pipeline run status to completed
            await self.pipeline_repository.update_pipeline_run(pipeline_run_id, {
                "status": PipelineStatus.COMPLETED,
                "end_time": datetime.now()
            })
            
            # Update dataset status to ready
            await self.dataset_repository.update_dataset_status(dataset_id, DatasetStatus.READY)
            
            result["success"] = True
            return result
            
        except Exception as e:
            error_message = f"Error in pipeline execution: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            # Update dataset status to error
            await self.dataset_repository.update_dataset_status(dataset_id, DatasetStatus.ERROR)
            
            # Update pipeline run status if it exists
            if "pipeline_run_id" in locals():
                await self.pipeline_repository.update_pipeline_run(pipeline_run_id, {
                    "status": PipelineStatus.FAILED,
                    "end_time": datetime.now(),
                    "error": error_message
                })
            
            result["errors"].append({
                "step": "pipeline_execution",
                "error": error_message
            })
            
            return result
    
    async def _handle_pipeline_failure(self, dataset_id: int, pipeline_run_id: int, step: str, error: str) -> None:
        """
        Handle a pipeline failure by updating the dataset and pipeline run status.
        
        Args:
            dataset_id: ID of the dataset
            pipeline_run_id: ID of the pipeline run
            step: The pipeline step that failed
            error: The error message
        """
        # Update dataset status to error
        await self.dataset_repository.update_dataset_status(dataset_id, DatasetStatus.ERROR)
        
        # Update pipeline run status
        await self.pipeline_repository.update_pipeline_run(pipeline_run_id, {
            "status": PipelineStatus.FAILED,
            "end_time": datetime.now(),
            "error": f"Failed at step '{step}': {error}"
        })
    
    async def load_data(self, dataset_id: int, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load data from a source into the system.
        
        Args:
            dataset_id: ID of the dataset to load
            config: Optional configuration for the data loader
            
        Returns:
            Dictionary with the results of the data loading
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Load the data using the data loader service
            result = await self.data_loader_service.load_data(dataset, config)
            
            if not result["success"]:
                return result
            
            # Update dataset metadata with loading information
            await self.dataset_repository.update_dataset_metadata(dataset_id, {
                "loaded_at": datetime.now().isoformat(),
                "row_count": result.get("row_count", 0),
                "column_count": result.get("column_count", 0),
                "data_types": result.get("data_types", {})
            })
            
            return {
                "success": True,
                "details": {
                    "row_count": result.get("row_count", 0),
                    "column_count": result.get("column_count", 0),
                    "sample_data": result.get("sample_data", [])
                }
            }
            
        except Exception as e:
            error_message = f"Error loading data: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                "success": False,
                "error": error_message
            }
    
    async def transform_data(self, dataset_id: int, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transform data using the data transformer service.
        
        Args:
            dataset_id: ID of the dataset to transform
            config: Optional configuration for the data transformer
            
        Returns:
            Dictionary with the results of the data transformation
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Get the loaded data
            data = await self.dataset_repository.get_dataset_data(dataset_id)
            if not data:
                return {
                    "success": False,
                    "error": f"No data found for dataset with ID {dataset_id}"
                }
            
            # Transform the data using the data transformer service
            result = await self.data_transformer_service.transform_data(data, config)
            
            if not result["success"]:
                return result
            
            # Save the transformed data
            await self.dataset_repository.save_transformed_data(dataset_id, result["data"])
            
            # Update dataset metadata with transformation information
            await self.dataset_repository.update_dataset_metadata(dataset_id, {
                "transformed_at": datetime.now().isoformat(),
                "transformations_applied": result.get("transformations_applied", []),
                "transformed_row_count": result.get("row_count", 0),
                "transformed_column_count": result.get("column_count", 0)
            })
            
            return {
                "success": True,
                "details": {
                    "transformations_applied": result.get("transformations_applied", []),
                    "row_count": result.get("row_count", 0),
                    "column_count": result.get("column_count", 0),
                    "sample_data": result.get("sample_data", [])
                }
            }
            
        except Exception as e:
            error_message = f"Error transforming data: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                "success": False,
                "error": error_message
            }
    
    async def generate_embeddings(self, dataset_id: int, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate vector embeddings for a dataset.
        
        Args:
            dataset_id: ID of the dataset to generate embeddings for
            config: Optional configuration for the vector embedder
            
        Returns:
            Dictionary with the results of the embedding generation
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Get the transformed data
            data = await self.dataset_repository.get_transformed_data(dataset_id)
            if not data:
                return {
                    "success": False,
                    "error": f"No transformed data found for dataset with ID {dataset_id}"
                }
            
            # Generate embeddings using the vector embedder service
            result = await self.vector_embedder_service.generate_embeddings(data, config)
            
            if not result["success"]:
                return result
            
            # Save the embeddings
            await self.dataset_repository.save_embeddings(dataset_id, result["embeddings"])
            
            # Update dataset metadata with embedding information
            await self.dataset_repository.update_dataset_metadata(dataset_id, {
                "embedded_at": datetime.now().isoformat(),
                "embedding_model": result.get("model", "unknown"),
                "embedding_dimensions": result.get("dimensions", 0),
                "embedding_count": result.get("count", 0)
            })
            
            return {
                "success": True,
                "details": {
                    "model": result.get("model", "unknown"),
                    "dimensions": result.get("dimensions", 0),
                    "count": result.get("count", 0)
                }
            }
            
        except Exception as e:
            error_message = f"Error generating embeddings: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                "success": False,
                "error": error_message
            }
    
    async def generate_insights(self, dataset_id: int) -> Dict[str, Any]:
        """
        Generate insights for a dataset using RAG.
        
        Args:
            dataset_id: ID of the dataset to generate insights for
            
        Returns:
            Dictionary with the results of the insights generation
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Get the embeddings
            embeddings = await self.dataset_repository.get_embeddings(dataset_id)
            if not embeddings or len(embeddings) == 0:
                return {
                    "success": False,
                    "error": f"No embeddings found for dataset with ID {dataset_id}"
                }
            
            # Get the transformed data for context
            data = await self.dataset_repository.get_transformed_data(dataset_id)
            if not data:
                return {
                    "success": False,
                    "error": f"No transformed data found for dataset with ID {dataset_id}"
                }
            
            # Generate insights using RAG
            insights = await analyze_dataset_with_rag(dataset, data, embeddings)
            
            if not insights:
                return {
                    "success": False,
                    "error": "Failed to generate insights"
                }
            
            # Save insights to the dataset
            await self.dataset_repository.save_insights(dataset_id, insights)
            
            # Generate and save suggestions based on insights
            suggestions = []
            for insight in insights:
                suggestion_type = insight.get("type", "general")
                suggestion_text = insight.get("suggestion", "")
                
                if suggestion_text:
                    suggestion_id = await self.suggestions_repository.create_suggestion({
                        "dataset_id": dataset_id,
                        "type": suggestion_type,
                        "text": suggestion_text,
                        "created_at": datetime.now().isoformat(),
                        "status": "active"
                    })
                    
                    suggestions.append({
                        "id": suggestion_id,
                        "type": suggestion_type,
                        "text": suggestion_text
                    })
            
            # Update dataset metadata with insights information
            await self.dataset_repository.update_dataset_metadata(dataset_id, {
                "insights_generated_at": datetime.now().isoformat(),
                "insight_count": len(insights),
                "suggestion_count": len(suggestions)
            })
            
            return {
                "success": True,
                "details": {
                    "insight_count": len(insights),
                    "suggestion_count": len(suggestions),
                    "insights": insights,
                    "suggestions": suggestions
                }
            }
            
        except Exception as e:
            error_message = f"Error generating insights: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                "success": False,
                "error": error_message
            }
    
    async def get_dataset_preview(self, dataset_id: int, limit: int = 100) -> Dict[str, Any]:
        """
        Get a preview of a dataset.
        
        Args:
            dataset_id: ID of the dataset to preview
            limit: Maximum number of rows to return
            
        Returns:
            Dictionary with the dataset preview
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Get the transformed data if available, otherwise get the raw data
            data = await self.dataset_repository.get_transformed_data(dataset_id)
            if not data:
                data = await self.dataset_repository.get_dataset_data(dataset_id)
                
            if not data:
                return {
                    "success": False,
                    "error": f"No data found for dataset with ID {dataset_id}"
                }
            
            # Limit the number of rows
            preview_data = data.head(limit).to_dict(orient="records")
            
            # Get column information
            columns = []
            for column in data.columns:
                data_type = str(data[column].dtype)
                sample_values = data[column].head(5).tolist()
                
                columns.append({
                    "name": column,
                    "type": data_type,
                    "sample_values": sample_values
                })
            
            return {
                "success": True,
                "data": {
                    "dataset_id": dataset_id,
                    "name": dataset.get("name", ""),
                    "description": dataset.get("description", ""),
                    "row_count": len(data),
                    "column_count": len(data.columns),
                    "columns": columns,
                    "preview": preview_data
                }
            }
            
        except Exception as e:
            error_message = f"Error getting dataset preview: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                "success": False,
                "error": error_message
            }
            
    async def run_pipeline_step(self, dataset_id: int, step_type: PipelineStepType) -> Dict[str, Any]:
        """
        Run a specific pipeline step on a dataset.
        
        Args:
            dataset_id: ID of the dataset to process
            step_type: Type of pipeline step to run
            
        Returns:
            Dictionary with the results of the step execution
        """
        try:
            # Get dataset
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {"success": False, "error": "Dataset not found"}
                
            # Create or get pipeline run
            pipeline_run = await self.pipeline_repository.get_or_create_pipeline_run(dataset_id)
            
            # Create step if it doesn't exist
            step = await self.pipeline_repository.get_or_create_pipeline_step(
                pipeline_run_id=pipeline_run.id,
                step_name=step_type,
                status=PipelineRunStatus.RUNNING
            )
            
            # Load dataset
            df = await self.data_loader_service.load_dataset(dataset)
            
            result = {"success": True, "step_id": step.id}
            
            # Execute step based on type
            if step_type == PipelineStepType.VALIDATE:
                # Use the DataValidationService for validation
                validation_service = DataValidationService()
                validation_results = await validation_service.validate_data(df)
                result.update({"validation_results": validation_results})
                
                # Update step status
                await self.pipeline_repository.update_pipeline_step(step.id, {
                    "status": PipelineRunStatus.COMPLETED,
                    "metadata": validation_results
                })
            elif step_type == PipelineStepType.TRANSFORM:
                # Handle transformation step
                transform_results = await self.data_transformer_service.transform_data(df)
                result.update({"transform_results": transform_results})
                
                # Update step status
                await self.pipeline_repository.update_pipeline_step(step.id, {
                    "status": PipelineRunStatus.COMPLETED,
                    "metadata": transform_results
                })
            elif step_type == PipelineStepType.ENRICH:
                # Handle enrichment step
                enrich_results = await self.data_transformer_service.enrich_data(df)
                result.update({"enrich_results": enrich_results})
                
                # Update step status
                await self.pipeline_repository.update_pipeline_step(step.id, {
                    "status": PipelineRunStatus.COMPLETED,
                    "metadata": enrich_results
                })
            elif step_type == PipelineStepType.LOAD:
                # Handle load step
                load_results = await self.vector_embedder_service.embed_and_store(df, dataset_id)
                result.update({"load_results": load_results})
                
                # Update step status
                await self.pipeline_repository.update_pipeline_step(step.id, {
                    "status": PipelineRunStatus.COMPLETED,
                    "metadata": load_results
                })
            else:
                # Unknown step type
                error_message = f"Unknown pipeline step type: {step_type}"
                await self.pipeline_repository.update_pipeline_step(step.id, {
                    "status": PipelineRunStatus.FAILED,
                    "error": error_message
                })
                return {"success": False, "error": error_message}
            
            return result
            
        except Exception as e:
            error_message = f"Error executing pipeline step {step_type}: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            # Update step status if it exists
            if "step" in locals():
                await self.pipeline_repository.update_pipeline_step(step.id, {
                    "status": PipelineRunStatus.FAILED,
                    "error": error_message
                })
                
            return {"success": False, "error": error_message}

# Create a singleton instance of the pipeline service
pipeline_service = PipelineService()
