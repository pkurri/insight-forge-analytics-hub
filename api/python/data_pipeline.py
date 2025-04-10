
"""
Data Pipeline Module

This module provides functionality for managing the data pipeline flow,
including data extraction, transformation, loading, and monitoring.

In a production environment, this would be deployed as an API endpoint or microservice.
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Any, Union, Optional
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipeline:
    """Class for managing data pipeline operations"""
    
    def __init__(self):
        """Initialize the data pipeline"""
        self.stages = {
            "extraction": {"status": "idle", "metadata": {}},
            "validation": {"status": "idle", "metadata": {}},
            "transformation": {"status": "idle", "metadata": {}},
            "enrichment": {"status": "idle", "metadata": {}},
            "loading": {"status": "idle", "metadata": {}},
        }
        self.datasets = {}
        self.pipeline_runs = []
        logger.info("DataPipeline initialized")
    
    def upload_data(self, file_data: bytes, filename: str, file_format: str) -> Dict[str, Any]:
        """
        Process uploaded file data
        
        Args:
            file_data: Raw file data bytes
            filename: Original filename
            file_format: Format of the file (csv, json, etc.)
            
        Returns:
            Dict with processing results
        """
        try:
            # Update extraction stage status
            self.stages["extraction"] = {
                "status": "processing", 
                "metadata": {
                    "filename": filename,
                    "format": file_format,
                    "size_bytes": len(file_data),
                    "started_at": datetime.now().isoformat()
                }
            }
            
            # Process the file based on format
            if file_format.lower() == 'csv':
                # In a real implementation, we would save the file to disk or cloud storage
                # and then process it
                df = pd.read_csv(pd.io.common.BytesIO(file_data))
                
            elif file_format.lower() == 'json':
                df = pd.read_json(pd.io.common.BytesIO(file_data))
                
            elif file_format.lower() in ['xlsx', 'excel']:
                df = pd.read_excel(pd.io.common.BytesIO(file_data))
                
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            # Generate a unique dataset ID
            dataset_id = f"ds-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Store basic metadata about the dataset
            self.datasets[dataset_id] = {
                "id": dataset_id,
                "name": os.path.splitext(filename)[0],
                "original_filename": filename,
                "format": file_format,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "created_at": datetime.now().isoformat(),
                "status": "extracted"
            }
            
            # Update extraction stage status to complete
            self.stages["extraction"] = {
                "status": "complete",
                "metadata": {
                    **self.stages["extraction"]["metadata"],
                    "completed_at": datetime.now().isoformat(),
                    "row_count": len(df),
                    "column_count": len(df.columns)
                }
            }
            
            # Update validation stage status to next
            self.stages["validation"] = {
                "status": "next",
                "metadata": {}
            }
            
            # Add run to pipeline history
            self.pipeline_runs.append({
                "id": f"run-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "dataset_id": dataset_id,
                "started_at": datetime.now().isoformat(),
                "status": "extraction_complete",
                "stages_completed": ["extraction"],
                "stages_remaining": ["validation", "transformation", "enrichment", "loading"]
            })
            
            return {
                "success": True,
                "message": f"File '{filename}' processed successfully",
                "dataset_id": dataset_id,
                "dataset_info": self.datasets[dataset_id]
            }
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            
            # Update extraction stage status to error
            self.stages["extraction"] = {
                "status": "error",
                "metadata": {
                    **self.stages["extraction"]["metadata"],
                    "error": str(e),
                    "error_at": datetime.now().isoformat()
                }
            }
            
            return {
                "success": False,
                "error": f"Failed to process file: {str(e)}"
            }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the current status of the pipeline
        
        Returns:
            Dict with pipeline status information
        """
        return {
            "success": True,
            "pipeline_status": {
                "stages": self.stages,
                "active_datasets": len(self.datasets),
                "latest_run": self.pipeline_runs[-1] if self.pipeline_runs else None,
                "total_runs": len(self.pipeline_runs)
            }
        }
    
    def validate_data(self, dataset_id: str, validation_rules: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Validate a dataset against rules
        
        Args:
            dataset_id: ID of the dataset to validate
            validation_rules: Optional list of validation rules
            
        Returns:
            Dict with validation results
        """
        try:
            if dataset_id not in self.datasets:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Update validation stage status
            self.stages["validation"] = {
                "status": "processing",
                "metadata": {
                    "dataset_id": dataset_id,
                    "started_at": datetime.now().isoformat()
                }
            }
            
            # In a real implementation, we would load the dataset and apply validation rules
            # For this demo, we'll simulate validation results
            validation_results = {
                "dataset_id": dataset_id,
                "total_rules": len(validation_rules) if validation_rules else 3,
                "passed_rules": 2,
                "failed_rules": 1,
                "validation_errors": [
                    {
                        "rule_id": "R001",
                        "rule_name": "Valid Date Format",
                        "column": "transaction_date",
                        "error_count": 5,
                        "error_percentage": 0.5,
                        "sample_errors": ["2023/13/45", "invalid date"]
                    }
                ]
            }
            
            # Update dataset status
            self.datasets[dataset_id]["status"] = "validated"
            self.datasets[dataset_id]["validated_at"] = datetime.now().isoformat()
            self.datasets[dataset_id]["validation_results"] = validation_results
            
            # Update validation stage status to complete
            self.stages["validation"] = {
                "status": "complete",
                "metadata": {
                    **self.stages["validation"]["metadata"],
                    "completed_at": datetime.now().isoformat(),
                    "rules_count": validation_results["total_rules"],
                    "passed_rules": validation_results["passed_rules"],
                    "failed_rules": validation_results["failed_rules"]
                }
            }
            
            # Update transformation stage status to next
            self.stages["transformation"] = {
                "status": "next",
                "metadata": {}
            }
            
            # Update pipeline run
            for run in self.pipeline_runs:
                if run["dataset_id"] == dataset_id:
                    run["status"] = "validation_complete"
                    run["stages_completed"].append("validation")
                    run["stages_remaining"].remove("validation")
                    break
            
            return {
                "success": True,
                "validation_results": validation_results
            }
            
        except Exception as e:
            logger.error(f"Error validating dataset: {str(e)}")
            
            # Update validation stage status to error
            self.stages["validation"] = {
                "status": "error",
                "metadata": {
                    **self.stages["validation"]["metadata"],
                    "error": str(e),
                    "error_at": datetime.now().isoformat()
                }
            }
            
            return {
                "success": False,
                "error": f"Failed to validate dataset: {str(e)}"
            }
    
    def transform_data(self, dataset_id: str, transformation_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Transform a dataset
        
        Args:
            dataset_id: ID of the dataset to transform
            transformation_config: Optional transformation configuration
            
        Returns:
            Dict with transformation results
        """
        try:
            if dataset_id not in self.datasets:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Update transformation stage status
            self.stages["transformation"] = {
                "status": "processing",
                "metadata": {
                    "dataset_id": dataset_id,
                    "started_at": datetime.now().isoformat()
                }
            }
            
            # In a real implementation, we would load the dataset and apply transformations
            # For this demo, we'll simulate transformation results
            transformation_results = {
                "dataset_id": dataset_id,
                "transformations_applied": [
                    {
                        "name": "Convert to datetime",
                        "columns": ["order_date", "shipping_date"],
                        "output_format": "YYYY-MM-DD"
                    },
                    {
                        "name": "Standardize case",
                        "columns": ["customer_name", "product_name"],
                        "case": "title"
                    }
                ],
                "rows_transformed": self.datasets[dataset_id]["row_count"],
                "new_columns_added": ["order_year", "order_month", "days_to_ship"]
            }
            
            # Update dataset status
            self.datasets[dataset_id]["status"] = "transformed"
            self.datasets[dataset_id]["transformed_at"] = datetime.now().isoformat()
            self.datasets[dataset_id]["transformation_results"] = transformation_results
            
            # Add new columns to dataset metadata
            self.datasets[dataset_id]["columns"].extend(["order_year", "order_month", "days_to_ship"])
            self.datasets[dataset_id]["column_count"] += 3
            
            # Update transformation stage status to complete
            self.stages["transformation"] = {
                "status": "complete",
                "metadata": {
                    **self.stages["transformation"]["metadata"],
                    "completed_at": datetime.now().isoformat(),
                    "transformations_applied": len(transformation_results["transformations_applied"]),
                    "new_columns_added": len(transformation_results["new_columns_added"])
                }
            }
            
            # Update enrichment stage status to next
            self.stages["enrichment"] = {
                "status": "next",
                "metadata": {}
            }
            
            # Update pipeline run
            for run in self.pipeline_runs:
                if run["dataset_id"] == dataset_id:
                    run["status"] = "transformation_complete"
                    run["stages_completed"].append("transformation")
                    run["stages_remaining"].remove("transformation")
                    break
            
            return {
                "success": True,
                "transformation_results": transformation_results
            }
            
        except Exception as e:
            logger.error(f"Error transforming dataset: {str(e)}")
            
            # Update transformation stage status to error
            self.stages["transformation"] = {
                "status": "error",
                "metadata": {
                    **self.stages["transformation"]["metadata"],
                    "error": str(e),
                    "error_at": datetime.now().isoformat()
                }
            }
            
            return {
                "success": False,
                "error": f"Failed to transform dataset: {str(e)}"
            }
    
    def enrich_data(self, dataset_id: str, enrichment_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Enrich a dataset with additional data
        
        Args:
            dataset_id: ID of the dataset to enrich
            enrichment_config: Optional enrichment configuration
            
        Returns:
            Dict with enrichment results
        """
        try:
            if dataset_id not in self.datasets:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Update enrichment stage status
            self.stages["enrichment"] = {
                "status": "processing",
                "metadata": {
                    "dataset_id": dataset_id,
                    "started_at": datetime.now().isoformat()
                }
            }
            
            # In a real implementation, we would load the dataset and apply enrichments
            # For this demo, we'll simulate enrichment results
            enrichment_results = {
                "dataset_id": dataset_id,
                "enrichments_applied": [
                    {
                        "name": "Geocoding",
                        "columns": ["customer_address"],
                        "output_columns": ["latitude", "longitude", "country_code"]
                    },
                    {
                        "name": "Sentiment Analysis",
                        "columns": ["customer_feedback"],
                        "output_columns": ["sentiment_score", "sentiment_label"]
                    }
                ],
                "rows_enriched": self.datasets[dataset_id]["row_count"],
                "new_columns_added": ["latitude", "longitude", "country_code", "sentiment_score", "sentiment_label"]
            }
            
            # Update dataset status
            self.datasets[dataset_id]["status"] = "enriched"
            self.datasets[dataset_id]["enriched_at"] = datetime.now().isoformat()
            self.datasets[dataset_id]["enrichment_results"] = enrichment_results
            
            # Add new columns to dataset metadata
            self.datasets[dataset_id]["columns"].extend(enrichment_results["new_columns_added"])
            self.datasets[dataset_id]["column_count"] += len(enrichment_results["new_columns_added"])
            
            # Update enrichment stage status to complete
            self.stages["enrichment"] = {
                "status": "complete",
                "metadata": {
                    **self.stages["enrichment"]["metadata"],
                    "completed_at": datetime.now().isoformat(),
                    "enrichments_applied": len(enrichment_results["enrichments_applied"]),
                    "new_columns_added": len(enrichment_results["new_columns_added"])
                }
            }
            
            # Update loading stage status to next
            self.stages["loading"] = {
                "status": "next",
                "metadata": {}
            }
            
            # Update pipeline run
            for run in self.pipeline_runs:
                if run["dataset_id"] == dataset_id:
                    run["status"] = "enrichment_complete"
                    run["stages_completed"].append("enrichment")
                    run["stages_remaining"].remove("enrichment")
                    break
            
            return {
                "success": True,
                "enrichment_results": enrichment_results
            }
            
        except Exception as e:
            logger.error(f"Error enriching dataset: {str(e)}")
            
            # Update enrichment stage status to error
            self.stages["enrichment"] = {
                "status": "error",
                "metadata": {
                    **self.stages["enrichment"]["metadata"],
                    "error": str(e),
                    "error_at": datetime.now().isoformat()
                }
            }
            
            return {
                "success": False,
                "error": f"Failed to enrich dataset: {str(e)}"
            }
    
    def load_data(self, dataset_id: str, destination: str, load_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Load a dataset to a destination
        
        Args:
            dataset_id: ID of the dataset to load
            destination: Destination to load the data to
            load_config: Optional loading configuration
            
        Returns:
            Dict with loading results
        """
        try:
            if dataset_id not in self.datasets:
                return {
                    "success": False,
                    "error": f"Dataset with ID {dataset_id} not found"
                }
            
            # Update loading stage status
            self.stages["loading"] = {
                "status": "processing",
                "metadata": {
                    "dataset_id": dataset_id,
                    "destination": destination,
                    "started_at": datetime.now().isoformat()
                }
            }
            
            # In a real implementation, we would load the dataset to the destination
            # For this demo, we'll simulate loading results
            loading_results = {
                "dataset_id": dataset_id,
                "destination": destination,
                "rows_loaded": self.datasets[dataset_id]["row_count"],
                "columns_loaded": self.datasets[dataset_id]["column_count"],
                "loading_mode": load_config.get("mode", "append") if load_config else "append"
            }
            
            # Update dataset status
            self.datasets[dataset_id]["status"] = "loaded"
            self.datasets[dataset_id]["loaded_at"] = datetime.now().isoformat()
            self.datasets[dataset_id]["loading_results"] = loading_results
            
            # Update loading stage status to complete
            self.stages["loading"] = {
                "status": "complete",
                "metadata": {
                    **self.stages["loading"]["metadata"],
                    "completed_at": datetime.now().isoformat(),
                    "rows_loaded": loading_results["rows_loaded"],
                    "columns_loaded": loading_results["columns_loaded"]
                }
            }
            
            # Update pipeline run
            for run in self.pipeline_runs:
                if run["dataset_id"] == dataset_id:
                    run["status"] = "complete"
                    run["stages_completed"].append("loading")
                    run["stages_remaining"].remove("loading")
                    run["completed_at"] = datetime.now().isoformat()
                    break
            
            # Reset all stages to idle
            for stage in self.stages:
                self.stages[stage] = {"status": "idle", "metadata": {}}
            
            return {
                "success": True,
                "loading_results": loading_results,
                "pipeline_complete": True
            }
            
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            
            # Update loading stage status to error
            self.stages["loading"] = {
                "status": "error",
                "metadata": {
                    **self.stages["loading"]["metadata"],
                    "error": str(e),
                    "error_at": datetime.now().isoformat()
                }
            }
            
            return {
                "success": False,
                "error": f"Failed to load dataset: {str(e)}"
            }
    
    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get information about a dataset
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dict with dataset information
        """
        if dataset_id not in self.datasets:
            return {
                "success": False,
                "error": f"Dataset with ID {dataset_id} not found"
            }
        
        return {
            "success": True,
            "dataset_info": self.datasets[dataset_id]
        }
    
    def get_all_datasets(self) -> Dict[str, Any]:
        """
        Get information about all datasets
        
        Returns:
            Dict with information about all datasets
        """
        return {
            "success": True,
            "datasets": list(self.datasets.values())
        }

# Create a singleton instance for use in API
pipeline = DataPipeline()

# Example usage (for testing)
if __name__ == "__main__":
    # Create sample CSV data
    import io
    
    csv_data = """
    id,name,age,email,purchase_amount
    1,John Smith,32,john@example.com,124.99
    2,Jane Doe,28,jane@example.com,89.75
    3,Bob Johnson,45,bob@example.com,245.50
    4,Alice Brown,39,alice@example.com,32.25
    5,Charlie Wilson,51,charlie@example.com,178.60
    """
    
    # Create data pipeline
    pipeline = DataPipeline()
    
    # Upload data
    upload_result = pipeline.upload_data(
        file_data=csv_data.encode('utf-8'),
        filename="sample_customer_data.csv",
        file_format="csv"
    )
    
    print("Upload result:", json.dumps(upload_result, indent=2))
    
    if upload_result["success"]:
        dataset_id = upload_result["dataset_id"]
        
        # Get pipeline status
        status_result = pipeline.get_pipeline_status()
        print("\nPipeline status:", json.dumps(status_result, indent=2))
        
        # Validate data
        validate_result = pipeline.validate_data(dataset_id)
        print("\nValidation result:", json.dumps(validate_result, indent=2))
        
        # Transform data
        transform_result = pipeline.transform_data(dataset_id)
        print("\nTransformation result:", json.dumps(transform_result, indent=2))
        
        # Enrich data
        enrich_result = pipeline.enrich_data(dataset_id)
        print("\nEnrichment result:", json.dumps(enrich_result, indent=2))
        
        # Load data
        load_result = pipeline.load_data(dataset_id, "database", {"mode": "append"})
        print("\nLoading result:", json.dumps(load_result, indent=2))
        
        # Get final pipeline status
        final_status = pipeline.get_pipeline_status()
        print("\nFinal pipeline status:", json.dumps(final_status, indent=2))
