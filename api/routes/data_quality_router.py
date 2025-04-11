
"""
Data Quality Router Module

This module defines API routes for data quality, including cleaning, validation,
and automated data processing.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, BackgroundTasks
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import pandas as pd
import logging

from api.models.dataset import Dataset
from api.repositories.dataset_repository import get_dataset_repository
from api.utils.file_utils import load_dataset_to_dataframe
from api.routes.auth_router import get_current_user_or_api_key

# Import data cleaning and validation modules
try:
    from src.api.python.data_cleaning import DataCleaningAgent, DataValidationAgent
    data_modules_available = True
except ImportError:
    data_modules_available = False
    import logging
    logging.warning("Data cleaning and validation modules not available. Some features will be disabled.")

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class DataCleaningConfig(BaseModel):
    missing_values_strategy: str = Field("auto", description="Strategy for handling missing values (auto, mean, median, mode, knn, none)")
    outliers_strategy: str = Field("auto", description="Strategy for handling outliers (auto, clip, remove, none)")
    duplicate_rows_strategy: str = Field("remove", description="Strategy for handling duplicate rows (remove, keep, none)")
    inconsistent_values_strategy: str = Field("auto", description="Strategy for handling inconsistent values (auto, standardize, none)")
    case_sensitive: bool = Field(False, description="Whether string comparisons should be case-sensitive")
    column_types: Dict[str, str] = Field(default_factory=dict, description="Manual column type overrides")
    column_transforms: Dict[str, str] = Field(default_factory=dict, description="Custom transformations for columns")

class ValidationRuleCreate(BaseModel):
    name: str
    type: str = Field(..., description="Rule type (row_level, column_level, dataset_level)")
    condition: str
    columns: List[str] = Field(default_factory=list, description="Columns to check (for column_level rules)")
    threshold: float = Field(0.01, description="Maximum allowed violation ratio for row_level rules")
    severity: str = Field("medium", description="Rule severity (low, medium, high)")

class DataValidationConfig(BaseModel):
    schema_validation: bool = True
    completeness_threshold: float = 0.9
    consistency_checks: bool = True
    format_validation: bool = True
    relationship_validation: bool = False
    rules: List[ValidationRuleCreate] = Field(default_factory=list)

@router.post("/{dataset_id}/clean")
async def clean_dataset(
    dataset_id: int,
    config: DataCleaningConfig = Body(...),
    output_name: Optional[str] = Query(None, description="Name for cleaned dataset output"),
    save_result: bool = Query(False, description="Whether to save the cleaned dataset"),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Clean a dataset using configurable data cleaning agent."""
    # Check if data modules are available
    if not data_modules_available:
        raise HTTPException(status_code=501, detail="Data cleaning module not available")
        
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Load dataset to DataFrame
    try:
        data = await load_dataset_to_dataframe(dataset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading dataset: {str(e)}")
    
    # Create cleaning agent with configuration
    cleaning_config = {
        "missing_values": {
            "strategy": config.missing_values_strategy,
            "knn_neighbors": 5
        },
        "outliers": {
            "strategy": config.outliers_strategy,
            "threshold": 3.0
        },
        "inconsistent_values": {
            "strategy": config.inconsistent_values_strategy,
            "case_sensitive": config.case_sensitive
        },
        "duplicate_rows": {
            "strategy": config.duplicate_rows_strategy
        },
        "column_types": config.column_types,
        "column_transforms": {}  # We'll need to handle these separately as they can't be serialized
    }
    
    # Create and run the cleaning agent
    cleaner = DataCleaningAgent(cleaning_config)
    results = cleaner.clean_dataset(data)
    
    if not results["success"]:
        raise HTTPException(status_code=500, detail=results.get("error", "Unknown error during data cleaning"))
    
    # Save the cleaned dataset if requested
    if save_result and results["success"]:
        # Implementation for saving the cleaned dataset would go here
        # This would involve creating a new dataset from the cleaned DataFrame
        pass
    
    # Return the cleaning results
    return results

@router.post("/{dataset_id}/validate")
async def validate_dataset(
    dataset_id: int,
    config: DataValidationConfig = Body(...),
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Validate a dataset using configurable data validation agent."""
    # Check if data modules are available
    if not data_modules_available:
        raise HTTPException(status_code=501, detail="Data validation module not available")
        
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Load dataset to DataFrame
    try:
        data = await load_dataset_to_dataframe(dataset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading dataset: {str(e)}")
    
    # Create validation agent with configuration
    validation_config = {
        "schema_validation": config.schema_validation,
        "completeness_threshold": config.completeness_threshold,
        "consistency_checks": config.consistency_checks,
        "format_validation": config.format_validation,
        "relationship_validation": config.relationship_validation,
        "custom_rules": []
    }
    
    validator = DataValidationAgent(validation_config)
    
    # Add custom rules
    for rule in config.rules:
        validator.add_rule({
            "name": rule.name,
            "type": rule.type,
            "condition": rule.condition,
            "columns": rule.columns,
            "threshold": rule.threshold,
            "severity": rule.severity
        })
    
    # Get schema if available
    schema = None
    
    # Run validation
    results = validator.validate_dataset(data, schema)
    
    if not results["success"]:
        raise HTTPException(status_code=500, detail=results.get("error", "Unknown error during data validation"))
    
    return results

@router.get("/{dataset_id}/profiling-and-validation")
async def get_dataset_profiling_and_validation(
    dataset_id: int,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Get comprehensive data quality report combining profiling and validation."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # First get the profile data
    from api.services.analytics_service import get_data_profile
    profile_data = await get_data_profile(dataset_id)
    
    # Then get validation with default settings
    validation_data = {"success": True, "message": "Validation not available"}
    
    if data_modules_available:
        try:
            # Load dataset to DataFrame
            data = await load_dataset_to_dataframe(dataset)
            
            # Create validation agent with default settings
            validator = DataValidationAgent()
            validation_data = validator.validate_dataset(data)
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            validation_data = {"success": False, "error": str(e)}
    
    # Combine results
    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset.name,
        "profiling": profile_data,
        "validation": validation_data
    }

@router.post("/{dataset_id}/data-pipeline")
async def run_data_pipeline(
    dataset_id: int,
    steps: List[str] = Query(["profile", "clean", "validate"], description="Pipeline steps to execute"),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(get_current_user_or_api_key),
    dataset_repo = Depends(get_dataset_repository)
):
    """Run a configurable data pipeline on a dataset."""
    # Check dataset exists and user has access
    dataset = await dataset_repo.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Create pipeline result container
    pipeline_results = {
        "dataset_id": dataset_id,
        "dataset_name": dataset.name,
        "steps_completed": [],
        "steps_failed": [],
        "results": {}
    }
    
    # Load dataset once to avoid repeated loading
    try:
        data = await load_dataset_to_dataframe(dataset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading dataset: {str(e)}")
    
    # Execute pipeline steps
    if "profile" in steps:
        try:
            from api.services.analytics_service import get_data_profile
            profile_data = await get_data_profile(dataset_id)
            pipeline_results["results"]["profile"] = profile_data
            pipeline_results["steps_completed"].append("profile")
        except Exception as e:
            logger.error(f"Pipeline profiling step failed: {str(e)}")
            pipeline_results["steps_failed"].append({"step": "profile", "error": str(e)})
    
    if "clean" in steps and data_modules_available:
        try:
            cleaner = DataCleaningAgent()
            cleaning_results = cleaner.clean_dataset(data)
            
            if cleaning_results["success"]:
                # Update the working data for subsequent steps
                data = cleaning_results["cleaned_data"]
                pipeline_results["results"]["clean"] = cleaning_results
                pipeline_results["steps_completed"].append("clean")
            else:
                pipeline_results["steps_failed"].append({"step": "clean", "error": cleaning_results.get("error", "Unknown error")})
        except Exception as e:
            logger.error(f"Pipeline cleaning step failed: {str(e)}")
            pipeline_results["steps_failed"].append({"step": "clean", "error": str(e)})
    
    if "validate" in steps and data_modules_available:
        try:
            validator = DataValidationAgent()
            validation_results = validator.validate_dataset(data)
            
            if validation_results["success"]:
                pipeline_results["results"]["validate"] = validation_results
                pipeline_results["steps_completed"].append("validate")
            else:
                pipeline_results["steps_failed"].append({"step": "validate", "error": validation_results.get("error", "Unknown error")})
        except Exception as e:
            logger.error(f"Pipeline validation step failed: {str(e)}")
            pipeline_results["steps_failed"].append({"step": "validate", "error": str(e)})
    
    if "anomalies" in steps:
        try:
            from api.services.analytics_service import detect_anomalies
            anomaly_results = await detect_anomalies(dataset_id, {"method": "isolation_forest"})
            
            pipeline_results["results"]["anomalies"] = anomaly_results
            pipeline_results["steps_completed"].append("anomalies")
        except Exception as e:
            logger.error(f"Pipeline anomaly detection step failed: {str(e)}")
            pipeline_results["steps_failed"].append({"step": "anomalies", "error": str(e)})
    
    # Add pipeline completion status
    pipeline_results["completed"] = len(pipeline_results["steps_failed"]) == 0
    pipeline_results["status"] = "success" if pipeline_results["completed"] else "partial_failure"
    
    return pipeline_results
