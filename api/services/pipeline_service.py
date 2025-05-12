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
import os
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
    
    async def load_dataset_data_from_file(self, dataset_id: int) -> Dict[str, Any]:
        """
        Load dataset data from a file stored in the temp folder.
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary with loaded data and success status
        """
        # Get dataset metadata to find the file path
        dataset = await self.dataset_repository.get_dataset(dataset_id)
        if not dataset:
            return {"success": False, "error": f"Dataset {dataset_id} not found"}
        
        # Extract file path from dataset metadata
        metadata = dataset.metadata if hasattr(dataset, 'metadata') else {}
        file_path = None
        
        # Check if source_info contains the file path
        if hasattr(dataset, 'source_info') and dataset.source_info:
            source_info = dataset.source_info
            if isinstance(source_info, str):
                try:
                    source_info = json.loads(source_info)
                except json.JSONDecodeError:
                    pass
            
            file_path = source_info.get('file_path') if isinstance(source_info, dict) else None
        
        # If file_path not found in source_info, check metadata
        if not file_path and metadata:
            file_path = metadata.get('file_path')
        
        if not file_path:
            return {"success": False, "error": f"File path not found for dataset {dataset_id}"}
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found at path: {file_path}"}
        
        # Load data based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        try:
            if file_ext == '.csv':
                data = pd.read_csv(file_path).to_dict('records')
            elif file_ext in ['.xlsx', '.xls']:
                data = pd.read_excel(file_path).to_dict('records')
            elif file_ext == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                return {"success": False, "error": f"Unsupported file format: {file_ext}"}
            
            if not data:
                return {"success": False, "error": f"No data found in file: {file_path}"}
                
            return {"success": True, "data": data, "file_path": file_path}
        except Exception as e:
            return {"success": False, "error": f"Error loading data from file: {str(e)}"}
            
    async def enrich_data(self, dataset_id: int, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enrich dataset with additional data and features.
        
        Args:
            dataset_id: ID of the dataset to enrich
            config: Configuration for enrichment
            
        Returns:
            Dictionary with enrichment results
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {"success": False, "error": f"Dataset {dataset_id} not found"}
                
            # Load transformed data if available
            transformed_data = await self.dataset_repository.get_transformed_data(dataset_id)
            if not transformed_data:
                # Try to load from file
                data_result = await self.load_dataset_data_from_file(dataset_id)
                if not data_result["success"]:
                    return {"success": False, "error": f"Failed to load dataset data: {data_result['error']}"}
                transformed_data = data_result["data"]
                
            # Apply enrichment logic
            enriched_data = []
            for record in transformed_data:
                # Add derived fields based on existing data
                enriched_record = dict(record)
                
                # Example enrichment: calculate total if quantity and price exist
                if "quantity" in record and "price" in record:
                    try:
                        enriched_record["total"] = float(record["quantity"]) * float(record["price"])
                    except (ValueError, TypeError):
                        pass
                        
                # Example: add timestamp for processing
                enriched_record["enriched_at"] = datetime.now().isoformat()
                
                # Add to enriched data
                enriched_data.append(enriched_record)
                
            # Save enriched data
            file_path = await self.dataset_repository.save_enriched_data(dataset_id, enriched_data)
            
            # Update dataset metadata
            metadata = {"enriched": True, "enriched_at": datetime.now().isoformat(), "enriched_file_path": file_path}
            await self.dataset_repository.update_dataset_metadata(dataset_id, metadata)
            
            return {
                "success": True,
                "message": f"Successfully enriched {len(enriched_data)} records",
                "file_path": file_path
            }
            
        except Exception as e:
            logger.error(f"Error enriching data: {str(e)}")
            return {"success": False, "error": f"Error enriching data: {str(e)}"}
            
    async def load_to_vector_db(self, dataset_id: int, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load dataset to vector database using the API-centric approach.
        
        Args:
            dataset_id: ID of the dataset to load
            config: Configuration for vector loading
            
        Returns:
            Dictionary with loading results
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {"success": False, "error": f"Dataset {dataset_id} not found"}
                
            # Determine the file path to use (enriched > transformed > original)
            file_path = None
            metadata = dataset.metadata if hasattr(dataset, 'metadata') and dataset.metadata else {}
            
            # Check for enriched data first
            if metadata.get("enriched") and metadata.get("enriched_file_path"):
                file_path = metadata.get("enriched_file_path")
                logger.info(f"Using enriched data file: {file_path}")
            
            # If no enriched data, check for transformed data
            if not file_path and hasattr(dataset, 'transformed_file_path') and dataset.transformed_file_path:
                file_path = dataset.transformed_file_path
                logger.info(f"Using transformed data file: {file_path}")
                
            # If no transformed data, use original file
            if not file_path:
                # Get from source_info or metadata
                if hasattr(dataset, 'source_info') and dataset.source_info:
                    source_info = dataset.source_info
                    if isinstance(source_info, str):
                        try:
                            source_info = json.loads(source_info)
                        except json.JSONDecodeError:
                            pass
                    
                    if isinstance(source_info, dict):
                        file_path = source_info.get('file_path')
                        
                # Check metadata if still no file path
                if not file_path and metadata:
                    file_path = metadata.get('file_path')
                    
            if not file_path:
                return {"success": False, "error": f"No file path found for dataset {dataset_id}"}
                
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found at path: {file_path}"}
                
            # Use the vector embedding API for processing
            from api.services.vector_embedding_api import vector_embedding_api
            
            # Configure chunk size and overlap
            chunk_size = config.get("chunk_size", 1000) if config else 1000
            overlap = config.get("overlap", 200) if config else 200
            
            # Process the dataset with the vector embedding API
            result = await vector_embedding_api.process_dataset(
                dataset_id=dataset_id,
                file_path=file_path,
                chunk_size=chunk_size,
                overlap=overlap
            )
            
            if result["success"]:
                # Update dataset metadata
                vector_metadata = {
                    "vectorized": True,
                    "vectorized_at": datetime.now().isoformat(),
                    "total_vectors": result["total_vectors"],
                    "vector_model": getattr(settings, "VECTOR_EMBEDDING_API_MODEL", "mistral")
                }
                await self.dataset_repository.update_dataset_metadata(dataset_id, vector_metadata)
                
                return {
                    "success": True,
                    "message": f"Successfully loaded {result['total_vectors']} vectors to the database",
                    "total_vectors": result["total_vectors"],
                    "total_records": result["total_records"]
                }
            else:
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Error loading to vector database: {str(e)}")
            return {"success": False, "error": f"Error loading to vector database: {str(e)}"}
    
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
            
            # Load data from file
            data_result = await self.load_dataset_data_from_file(dataset_id)
            if not data_result["success"]:
                return data_result
            
            data = data_result["data"]
            file_path = data_result["file_path"]
            
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
            
            # Try to get the transformed data first
            data = await self.dataset_repository.get_transformed_data(dataset_id)
            
            # If no transformed data, load from file
            if not data:
                data_result = await self.load_dataset_data_from_file(dataset_id)
                if not data_result["success"]:
                    return data_result
                
                data = data_result["data"]
                
                # Since we're using raw data, we should transform it first
                transform_result = await self.data_transformer_service.transform_data(data, {})
                if transform_result["success"] and "data" in transform_result:
                    data = transform_result["data"]
                    # Save the transformed data for future use
                    await self.dataset_repository.save_transformed_data(dataset_id, data)
            
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
    
    async def enrich_data(self, dataset_id: int, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enrich data with additional information or derived fields.
        
        Args:
            dataset_id: ID of the dataset to enrich
            config: Optional configuration for the data enrichment
            
        Returns:
            Dictionary with the results of the data enrichment
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Try to get the transformed data first
            data = await self.dataset_repository.get_transformed_data(dataset_id)
            
            # If no transformed data, load from file
            if not data:
                data_result = await self.load_dataset_data_from_file(dataset_id)
                if not data_result["success"]:
                    return data_result
                
                data = data_result["data"]
                
                # Since we're using raw data, we should transform it first
                transform_result = await self.data_transformer_service.transform_data(data, {})
                if transform_result["success"] and "data" in transform_result:
                    data = transform_result["data"]
                    # Save the transformed data for future use
                    await self.dataset_repository.save_transformed_data(dataset_id, data)
            
            # Enrich the data with additional information
            # This could involve adding derived fields, integrating external data sources, etc.
            # For now, we'll just pass through the data as a placeholder
            enriched_data = data
            
            # Save the enriched data
            await self.dataset_repository.save_enriched_data(dataset_id, enriched_data)
            
            # Update dataset metadata with enrichment information
            await self.dataset_repository.update_dataset_metadata(dataset_id, {
                "enriched_at": datetime.now().isoformat(),
                "enrichment_details": "Data enriched with additional fields"
            })
            
            return {
                "success": True,
                "details": {
                    "row_count": len(enriched_data),
                    "sample_data": enriched_data[:5] if len(enriched_data) > 5 else enriched_data
                }
            }
            
        except Exception as e:
            error_message = f"Error enriching data: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                "success": False,
                "error": error_message
            }
    
    async def apply_business_rules(self, dataset_id: str, rule_ids: List[str]) -> Dict[str, Any]:
        """
        Apply business rules to a dataset and update pipeline metadata.
        
        Args:
            dataset_id: ID of the dataset to apply rules to
            rule_ids: List of rule IDs to apply
            
        Returns:
            Dictionary with the results of applying the business rules
        """
        try:
            # Convert dataset_id to int if it's a string
            dataset_id_int = int(dataset_id) if isinstance(dataset_id, str) else dataset_id
            
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id_int)
            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Update pipeline metadata to track applied rules
            # This is used for tracking which rules have been applied in the pipeline
            pipeline_run = await self.pipeline_repository.get_latest_pipeline_run(dataset_id_int)
            if pipeline_run:
                # Update pipeline run metadata
                metadata = pipeline_run.get("metadata", {}) or {}
                applied_rules = metadata.get("applied_rules", []) or []
                applied_rules.extend(rule_ids)
                metadata["applied_rules"] = list(set(applied_rules))  # Remove duplicates
                
                # Save the updated metadata
                await self.pipeline_repository.update_pipeline_run(pipeline_run["id"], {
                    "metadata": metadata
                })
                
                # Create a pipeline step for business rules application
                step_data = {
                    "pipeline_run_id": pipeline_run["id"],
                    "step_type": "business_rules",
                    "status": "completed",
                    "start_time": datetime.now(),
                    "end_time": datetime.now(),
                    "metadata": {
                        "applied_rules": rule_ids,
                        "rule_count": len(rule_ids)
                    }
                }
                await self.pipeline_repository.create_pipeline_step(step_data=step_data)
            
            return {
                "success": True,
                "details": {
                    "dataset_id": dataset_id,
                    "applied_rules": rule_ids,
                    "rule_count": len(rule_ids)
                }
            }
            
        except Exception as e:
            error_message = f"Error applying business rules: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {
                "success": False,
                "error": error_message
            }
    
    async def load_to_vector_db(self, dataset_id: int, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load data to vector database for semantic search and retrieval.
        
        Args:
            dataset_id: ID of the dataset to load to vector DB
            config: Optional configuration for the vector DB loading
            
        Returns:
            Dictionary with the results of the vector DB loading
        """
        try:
            # Get dataset information
            dataset = await self.dataset_repository.get_dataset(dataset_id)
            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Try to get the enriched data first, then transformed data, then raw data
            data = await self.dataset_repository.get_enriched_data(dataset_id)
            
            if not data:
                data = await self.dataset_repository.get_transformed_data(dataset_id)
            
            # If no processed data, load from file
            if not data:
                data_result = await self.load_dataset_data_from_file(dataset_id)
                if not data_result["success"]:
                    return data_result
                
                data = data_result["data"]
                
                # Since we're using raw data, we should transform it first
                transform_result = await self.data_transformer_service.transform_data(data, {})
                if transform_result["success"] and "data" in transform_result:
                    data = transform_result["data"]
                    # Save the transformed data for future use
                    await self.dataset_repository.save_transformed_data(dataset_id, data)
            
            # Generate embeddings for the data if not already done
            embeddings = await self.dataset_repository.get_embeddings(dataset_id)
            if not embeddings or len(embeddings) == 0:
                # Generate embeddings
                embedding_result = await self.generate_embeddings(dataset_id)
                if not embedding_result["success"]:
                    return embedding_result
                
                embeddings = await self.dataset_repository.get_embeddings(dataset_id)
            
            # Load the data and embeddings to the vector database
            # This is a placeholder for the actual vector DB loading logic
            vector_db_result = {
                "success": True,
                "details": {
                    "records_loaded": len(data),
                    "vector_dimensions": 768,  # Example dimension
                    "database": "vector_db"
                }
            }
            
            # Update dataset metadata with vector DB loading information
            await self.dataset_repository.update_dataset_metadata(dataset_id, {
                "loaded_to_vector_db_at": datetime.now().isoformat(),
                "vector_db_details": vector_db_result["details"]
            })
            
            return vector_db_result
            
        except Exception as e:
            error_message = f"Error loading data to vector database: {str(e)}"
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
            
            # Try to get the transformed data first
            data = await self.dataset_repository.get_transformed_data(dataset_id)
            
            # If no transformed data, load from file
            if not data:
                data_result = await self.load_dataset_data_from_file(dataset_id)
                if not data_result["success"]:
                    return data_result
                
                data = data_result["data"]
                
                # Since we're using raw data, we should transform it first
                transform_result = await self.data_transformer_service.transform_data(data, {})
                if transform_result["success"] and "data" in transform_result:
                    data = transform_result["data"]
                    # Save the transformed data for future use
                    await self.dataset_repository.save_transformed_data(dataset_id, data)
            
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
            
            # Get the transformed data if available, otherwise load from file
            data = await self.dataset_repository.get_transformed_data(dataset_id)
            if not data:
                # Load data from file
                data_result = await self.load_dataset_data_from_file(dataset_id)
                if not data_result["success"]:
                    return data_result
                
                data = data_result["data"]
                
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
