"""
Pipeline Service Module

This module handles data pipeline processing for datasets.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import ydata_profiling as yp
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import IsolationForest

from config.settings import get_settings
from repositories.dataset_repository import DatasetRepository
from models.dataset import DatasetStatus, FileType, SourceType
from models.pipeline import PipelineStepType, PipelineRunStatus
from services.validation_service import validation_service
from services.cleaning_service import cleaning_service
from services.profiling_service import profiling_service
from services.business_rules import business_rules_service
from services.data_processing_service import DataProcessingService
from services.data_validation_service import DataValidationService
from services.data_profiling_service import DataProfilingService
from services.data_enrichment_service import data_enrichment_service
from repositories.pipeline_repository import PipelineRepository

settings = get_settings()
logger = logging.getLogger(__name__)

import asyncio
import time

def run_pipeline_step(pipeline: 'DataPipeline', step_type: str, df: pd.DataFrame, rules: dict = None, status: dict = None, **kwargs) -> Any:
    """
    Dispatch to the correct DataPipeline method based on step_type.
    Logs start/end/duration, supports rule-based skipping, and updates status dict.
    Integrates OpenEvals for quality and rule evaluation after each step.
    
    Args:
        pipeline: DataPipeline instance
        step_type: Type of pipeline step to run
        df: DataFrame to process
        rules: Optional business rules to apply
        status: Optional status dictionary to update
        **kwargs: Additional arguments for specific steps
        
    Returns:
        Result of the pipeline step
    """
    step_type = step_type.lower()
    rules = rules or {}
    status = status or {}
    step_status = {"step": step_type, "start": time.time(), "status": "started"}
    
    try:
        # Check business rules
        if rules.get("skip_steps") and step_type in rules["skip_steps"]:
            step_status["status"] = "skipped"
            status[step_type] = step_status
            logger.info(f"Step {step_type} skipped by rules.")
            return None
            
        logger.info(f"Step {step_type} started.")
        
        # Dispatch to appropriate method
        if step_type == 'clean':
            result = pipeline._clean_data(df)
        elif step_type == 'validate':
            result = pipeline._validate_data(df)
        elif step_type == 'profile':
            result = pipeline._generate_profile(df)
        elif step_type == 'analyze':
            result = pipeline._analyze_data(df)
        elif step_type == 'anomalies':
            result = pipeline._detect_anomalies(df)
        elif step_type == 'embed':
            result = pipeline._generate_embeddings(df)
        elif step_type == 'quality':
            result = pipeline._calculate_quality_score(df)
        elif step_type == 'enrich':
            result = pipeline.enrich_data(df)
        elif step_type == 'custom_transform':
            result = pipeline.custom_transform(df, **kwargs)
        else:
            raise ValueError(f"Unknown pipeline step type: {step_type}")
            
        step_status["status"] = "completed"
        step_status["end"] = time.time()
        step_status["duration"] = step_status["end"] - step_status["start"]
        status[step_type] = step_status
        logger.info(f"Step {step_type} completed in {step_status['duration']:.2f}s.")
        return result
        
    except Exception as e:
        step_status["status"] = "failed"
        step_status["end"] = time.time()
        step_status["duration"] = step_status["end"] - step_status["start"]
        step_status["error"] = str(e)
        status[step_type] = step_status
        logger.error(f"Step {step_type} failed: {e}")
        raise

# Forward declaration for type hints
from typing import Callable

async def run_pipeline_step(pipeline: 'DataPipeline', step_type: str, df: pd.DataFrame, rules: dict = None, status: dict = None, **kwargs) -> Any:
    """
    Dispatch to the correct DataPipeline method based on step_type.
    Logs start/end/duration, supports rule-based skipping, and updates status dict.
    Integrates OpenEvals for quality and rule evaluation after each step.
    """
    from services.openevals_service import openevals_service
    step_type = step_type.lower()
    rules = rules or {}
    status = status or {}
    logger = logging.getLogger(__name__)
    step_status = {"step": step_type, "start": time.time(), "status": "started"}
    try:
        # Check business rules
        if rules.get("skip_steps") and step_type in rules["skip_steps"]:
            step_status["status"] = "skipped"
            status[step_type] = step_status
            logger.info(f"Step {step_type} skipped by rules.")
            return None
        logger.info(f"Step {step_type} started.")
        # Dispatch
        if step_type == 'clean':
            result = await pipeline._clean_data(df)
            # OpenEvals data quality evaluation
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", result if result is not None else df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'validate':
            result = await pipeline._validate_data(df)
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'profile':
            result = await pipeline._generate_profile(df)
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'analyze':
            result = await pipeline._analyze_data(df)
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'anomalies':
            result = await pipeline._detect_anomalies(df)
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'embed':
            result = await pipeline._generate_embeddings(df)
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'quality':
            result = await pipeline._calculate_quality_score(df)
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'enrich':
            result = await pipeline.enrich_data(df)
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", result if result is not None else df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'custom_transform':
            result = await pipeline.custom_transform(df, **kwargs)
            try:
                oeval = await openevals_service.evaluate_data_quality("unknown", result if result is not None else df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
        elif step_type == 'business_rules':
            # If you add business_rules as a step, evaluate with OpenEvals
            try:
                oeval = await openevals_service.evaluate_business_rules("unknown", df)
                step_status["openevals_evaluation"] = oeval
            except Exception as oe:
                logger.error(f"OpenEvals business rule evaluation failed: {str(oe)}")
                step_status["openevals_evaluation"] = {"error": str(oe)}
            result = None
        else:
            raise ValueError(f"Unknown pipeline step type: {step_type}")
        step_status["status"] = "completed"
        step_status["end"] = time.time()
        step_status["duration"] = step_status["end"] - step_status["start"]
        status[step_type] = step_status
        logger.info(f"Step {step_type} completed in {step_status['duration']:.2f}s.")
        return result
    except Exception as e:
        step_status["status"] = "failed"
        step_status["end"] = time.time()
        step_status["duration"] = step_status["end"] - step_status["start"]
        step_status["error"] = str(e)
        # Try OpenEvals error evaluation
        from services.openevals_service import openevals_service
        try:
            if step_type == 'business_rules':
                oeval = await openevals_service.evaluate_business_rules("unknown", df)
            else:
                oeval = await openevals_service.evaluate_data_quality("unknown", df)
            step_status["openevals_evaluation"] = oeval
        except Exception as oe:
            logger.error(f"OpenEvals evaluation on error failed: {str(oe)}")
            step_status["openevals_evaluation"] = {"error": str(oe)}
        status[step_type] = step_status
        logger.error(f"Step {step_type} failed: {e}")
        raise

    """
    Dispatch to the correct DataPipeline method based on step_type.
    """
    step_type = step_type.lower()
    if step_type == 'clean':
        return pipeline._clean_data(df)
    elif step_type == 'validate':
        return pipeline._validate_data(df)
    elif step_type == 'profile':
        return pipeline._generate_profile(df)
    elif step_type == 'analyze':
        return pipeline._analyze_data(df)
    elif step_type == 'anomalies':
        return pipeline._detect_anomalies(df)
    elif step_type == 'embed':
        return pipeline._generate_embeddings(df)
    elif step_type == 'quality':
        return pipeline._calculate_quality_score(df)
    else:
        raise ValueError(f"Unknown pipeline step type: {step_type}")


class DataPipeline:
    """Data pipeline for processing datasets."""
    
    def __init__(self):
        """Initialize pipeline components."""
        self.imputer = SimpleImputer(strategy='mean')
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.anomaly_detector = IsolationForest(contamination=0.1)
    
    async def process_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Process a dataset through the complete pipeline.
        
        Args:
            dataset_id: ID of the dataset to process
            
        Returns:
            Processing results and pipeline_metadata
        """
        try:
            # Get dataset
            from repositories.dataset_repository import DatasetRepository
            dataset_repo = DatasetRepository()
            dataset = await dataset_repo.get_dataset(dataset_id)
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")

            # Update status
            await dataset_repo.update_dataset_status(
                dataset_id, 
                DatasetStatus.PROCESSING
            )

            # Load dataset
            df = pd.read_csv(dataset["file_path"])

            # 1. Clean data
            cleaned_df = await self._clean_data(df)
            cleaned_path = f"{dataset['file_path']}_cleaned.csv"
            cleaned_df.to_csv(cleaned_path, index=False)

            # 2. Validate data
            validation_results = await self._validate_data(cleaned_df)

            # 3. Generate profile
            profile = await self._generate_profile(cleaned_df)

            # 4. Perform analytics
            analytics_results = await self._analyze_data(cleaned_df)

            # 5. Detect anomalies
            anomalies = await self._detect_anomalies(cleaned_df)

            # 6. Store embeddings
            await dataset_repo.store_embeddings(dataset_id, self._generate_embeddings(cleaned_df))

            # Update dataset pipeline_metadata
            ds_pipeline_metadata = {
                "validation": validation_results,
                "analytics": analytics_results,
                "anomalies": anomalies,
                "profile": profile,
                "columns": [
                    {
                        "name": col,
                        "data_type": str(cleaned_df[col].dtype),
                        "stats": {
                            "unique": int(cleaned_df[col].nunique()),
                            "missing": int(cleaned_df[col].isnull().sum())
                        }
                    }
                    for col in cleaned_df.columns
                ]
            }

            await dataset_repo.update_dataset_status(
                dataset_id,
                DatasetStatus.COMPLETED,
                ds_pipeline_metadata
            )

            return {
                "success": True,
                "ds_pipeline_metadata": ds_pipeline_metadata,
                "cleaned_path": cleaned_path
            }

        except Exception as e:
            logger.error(f"Error processing dataset: {str(e)}")
            await dataset_repo.update_dataset_status(
                dataset_id,
                DatasetStatus.ERROR,
                {"error": str(e)}
            )
            raise
    
    async def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean dataset by handling missing values and encoding."""
        result_df = df.copy()
        
        # Handle numeric columns
        numeric_cols = result_df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            result_df[numeric_cols] = self.imputer.fit_transform(result_df[numeric_cols])
            result_df[numeric_cols] = self.scaler.fit_transform(result_df[numeric_cols])
        
        # Handle categorical columns
        cat_cols = result_df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            if result_df[col].isnull().any():
                result_df[col] = result_df[col].fillna('MISSING')
            result_df[col] = self.label_encoder.fit_transform(result_df[col])
        
        return result_df
    
    async def _validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate dataset and return quality metrics."""
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicates": int(df.duplicated().sum()),
            "quality_score": self._calculate_quality_score(df)
        }
    
    async def _generate_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate data profile using ydata-profiling."""
        profile = yp.ProfileReport(df, minimal=True)
        return profile.get_description()
    
    async def _analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform data analysis and return insights."""
        insights = {
            "correlation": df.corr().to_dict() if len(df.select_dtypes(include=['number']).columns) > 1 else {},
            "summary_stats": df.describe().to_dict(),
            "key_metrics": {}
        }
        
        # Calculate key metrics for each column
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                insights["key_metrics"][col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "skew": float(df[col].skew())
                }
        
        return insights
    
    async def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in the dataset."""
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            # Detect anomalies using Isolation Forest
            anomalies = self.anomaly_detector.fit_predict(df[numeric_cols])
            anomaly_indices = np.where(anomalies == -1)[0]
            
            return {
                "total_anomalies": len(anomaly_indices),
                "anomaly_indices": anomaly_indices.tolist(),
                "anomaly_score": self.anomaly_detector.score_samples(df[numeric_cols]).tolist()
            }
        return {"total_anomalies": 0, "anomaly_indices": [], "anomaly_score": []}
    
    def _generate_embeddings(self, df: pd.DataFrame) -> np.ndarray:
        """Generate embeddings for the dataset."""
        # Convert DataFrame to string representation
        text_data = df.to_string()
        # Use a pre-trained model to generate embeddings
        # For now, return random embeddings
        return np.random.rand(768)  # 768-dimensional embedding
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score."""
        # Calculate based on missing values, duplicates, and data types
        missing_score = 1 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]))
        duplicate_score = 1 - (df.duplicated().sum() / len(df))
        
        return (missing_score + duplicate_score) / 2

class PipelineService:
    """Service for managing data pipelines."""
    
    def __init__(self, business_rules_service=None):
        self.dataset_repo = DatasetRepository()
        self.pipeline_repo = PipelineRepository()
        self.processing_service = DataProcessingService()
        self.validation_service = DataValidationService()
        self.profiling_service = DataProfilingService()
        self.business_rules_service = business_rules_service or business_rules_service
        self.enrichment_service = data_enrichment_service
        self.vector_service = None  # Will be initialized on demand
    
    async def process_uploaded_file(
        self,
        dataset_id: int,
        file_path: str,
        file_type: FileType
    ) -> Dataset:
        """Process an uploaded file through the pipeline."""
        # Update dataset status
        dataset = await self.dataset_repo.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
            
        await self.dataset_repo.update_dataset(
            dataset_id,
            {"status": DatasetStatus.PROCESSING}
        )
        
        try:
            # Read file based on type
            if file_type == FileType.CSV:
                df = pd.read_csv(file_path)
            elif file_type == FileType.JSON:
                df = pd.read_json(file_path)
            elif file_type == FileType.EXCEL:
                df = pd.read_excel(file_path)
            elif file_type == FileType.PARQUET:
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Update dataset metadata
            metadata = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "file_path": file_path,
                "file_type": file_type
            }
            
            await self.dataset_repo.update_dataset(
                dataset_id,
                {
                    "status": DatasetStatus.COMPLETED,
                    "metadata": metadata
                }
            )
            
            # Create pipeline run
            pipeline_run = await self.pipeline_repo.create_pipeline_run(dataset_id)
            
            # Run cleaning step
            cleaning_step = await self.pipeline_repo.create_pipeline_step(
                pipeline_run.id,
                PipelineStepType.CLEAN,
                PipelineRunStatus.PROCESSING
            )
            
            cleaned_df = await self.processing_service.clean_data(df)
            await self.pipeline_repo.update_pipeline_step_status(
                cleaning_step.id,
                PipelineRunStatus.COMPLETED,
                {"rows_cleaned": len(df) - len(cleaned_df)}
            )
            
            # Run validation step
            validation_step = await self.pipeline_repo.create_pipeline_step(
                pipeline_run.id,
                PipelineStepType.VALIDATE,
                PipelineRunStatus.PROCESSING
            )
            
            validation_results = await self.validation_service.validate_data(cleaned_df)
            await self.pipeline_repo.update_pipeline_step_status(
                validation_step.id,
                PipelineRunStatus.COMPLETED,
                validation_results
            )
            
            # Run profiling step
            profiling_step = await self.pipeline_repo.create_pipeline_step(
                pipeline_run.id,
                PipelineStepType.PROFILE,
                PipelineRunStatus.PROCESSING
            )
            
            profiling_results = await self.profiling_service.profile_data(cleaned_df)
            await self.pipeline_repo.update_pipeline_step_status(
                profiling_step.id,
                PipelineRunStatus.COMPLETED,
                profiling_results
            )
            
            # Add business rules step (but don't run it yet)
            business_rules_step = await self.pipeline_repo.create_pipeline_step(
                pipeline_run.id,
                PipelineStepType.BUSINESS_RULES,
                PipelineRunStatus.PENDING
            )
            
            # Add transform step (but don't run it yet)
            transform_step = await self.pipeline_repo.create_pipeline_step(
                pipeline_run.id,
                PipelineStepType.TRANSFORM,
                PipelineRunStatus.PENDING
            )
            
            # Add enrich step (but don't run it yet)
            enrich_step = await self.pipeline_repo.create_pipeline_step(
                pipeline_run.id,
                PipelineStepType.ENRICH,
                PipelineRunStatus.PENDING
            )
            
            # Add load step (but don't run it yet)
            load_step = await self.pipeline_repo.create_pipeline_step(
                pipeline_run.id,
                PipelineStepType.LOAD,
                PipelineRunStatus.PENDING
            )
            
            return await self.dataset_repo.get_dataset(dataset_id)
            
        except Exception as e:
            await self.dataset_repo.update_dataset(
                dataset_id,
                {
                    "status": DatasetStatus.ERROR,
                    "error_message": str(e)
                }
            )
            raise
    
    async def extract_sample_data(self, file_path: str, file_type: FileType, max_rows: int = 100) -> Dict[str, Any]:
        """
        Extract a sample of data from a file for rule testing and preview.
        
        Args:
            file_path: Path to the file
            file_type: Type of file (csv, json, etc.)
            max_rows: Maximum number of rows to extract
            
        Returns:
            Dictionary with sample data and metadata
        """
        try:
            # Read data based on file type
            if file_type == FileType.CSV:
                df = pd.read_csv(file_path, nrows=max_rows)
            elif file_type == FileType.JSON:
                df = pd.read_json(file_path)
                df = df.head(max_rows)
            elif file_type == FileType.EXCEL:
                df = pd.read_excel(file_path, nrows=max_rows)
            elif file_type == FileType.PARQUET:
                df = pd.read_parquet(file_path)
                df = df.head(max_rows)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
            # Convert to list of dictionaries for API response
            sample_data = df.to_dict(orient='records')
            
            # Get basic metadata
            metadata = {
                "columns": list(df.columns),
                "dtypes": {col: str(df[col].dtype) for col in df.columns},
                "row_count": len(df),
                "sample_size": min(max_rows, len(df))
            }
            
            return {
                "success": True,
                "sample": sample_data,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to extract sample data: {str(e)}"
            }
    
    async def apply_business_rules(self, dataset_id: str, rule_ids: List[str]):
        """
        Apply business rules to a dataset.
        
        Args:
            dataset_id: ID of the dataset
            rule_ids: List of rule IDs to apply
            
        Returns:
            Dictionary with results of applying rules
        """
        try:
            # Get dataset
            dataset = await self.dataset_repo.get_dataset(int(dataset_id))
            if not dataset:
                return {"success": False, "error": f"Dataset {dataset_id} not found"}
            
            # Create a new pipeline run
            run_id = await self.pipeline_repo.create_pipeline_run(int(dataset_id))
            
            # Create a new pipeline step
            step_id = await self.pipeline_repo.create_pipeline_step(run_id, PipelineStepType.BUSINESS_RULES)
            
            # Update step status to processing
            await self.pipeline_repo.update_pipeline_step_status(step_id, "processing")
            
            # Load dataset data
            data = await self.dataset_repo.get_dataset_data(int(dataset_id))
            
            # Apply business rules
            from services.business_rules.executors import apply_rules_to_dataset
            result = await apply_rules_to_dataset(dataset_id, data, rule_ids)
            
            if result.get("success", False):
                # Update step status to completed
                await self.pipeline_repo.update_pipeline_step_status(step_id, "completed")
                
                # Update dataset metadata with applied rules
                metadata = dataset.get("metadata", {}) or {}
                applied_rules = metadata.get("applied_rules", []) or []
                applied_rules.extend(rule_ids)
                metadata["applied_rules"] = list(set(applied_rules))  # Remove duplicates
                await self.dataset_repo.update_dataset_metadata(int(dataset_id), metadata)
                
                return {"success": True, "data": result}
            else:
                # Update step status to failed
                await self.pipeline_repo.update_pipeline_step_status(step_id, "failed", result.get("error", "Unknown error"))
                return result
        except Exception as e:
            # Update step status to failed
            if 'step_id' in locals():
                await self.pipeline_repo.update_pipeline_step_status(step_id, "failed", str(e))
            
            return {"success": False, "error": str(e)}
    
    async def run_pipeline_step(
        self,
        dataset_id: int,
        step_type: PipelineStepType
    ):
        """Run a specific pipeline step on a dataset."""
        try:
            # Get dataset
            dataset = await self.dataset_repo.get_dataset(dataset_id)
            if not dataset:
                return {"success": False, "error": f"Dataset {dataset_id} not found"}
                
            # Create a new pipeline run
            run_id = await self.pipeline_repo.create_pipeline_run(dataset_id)
            
            # Create a new pipeline step
            step_id = await self.pipeline_repo.create_pipeline_step(run_id, step_type)
            
            # Update step status to processing
            await self.pipeline_repo.update_pipeline_step_status(step_id, "processing")
            
            # Load dataset data
            data = await self.dataset_repo.get_dataset_data(dataset_id)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Run the step
            result = None
            if step_type == PipelineStepType.VALIDATE:
                result = await self.validation_service.validate_data(df)
            elif step_type == PipelineStepType.CLEAN:
                result = await self.cleaning_service.clean_data(df)
            elif step_type == PipelineStepType.PROFILE:
                result = await self.profiling_service.profile_data(df)
            elif step_type == PipelineStepType.TRANSFORM:
                result = await self.transform_data(dataset_id)
                # Apply transformations to the dataset
                result = await self.processing_service.transform_data(df)
                metadata = {"transformations_applied": result.get("transformations_applied", [])}
            elif step_type == PipelineStepType.ENRICH:
                # Enrich data with external sources or derived fields
                enrichment_config = kwargs.get("enrichment_config", {})
                result = await self.enrichment_service.enrich_data(df, enrichment_config)
                metadata = {
                    "enrichments_applied": result.get("enrichments_applied", []),
                    "new_columns": result.get("new_columns", []),
                    "rows_before": result.get("rows_before", len(df)),
                    "rows_after": result.get("rows_after", len(df))
                }
                
                # Update the dataframe with the enriched version
                df = result.get("enriched_df", df)
            elif step_type == PipelineStepType.LOAD:
                # Load data to vector database
                if not self.vector_service:
                    from services.vector_service import VectorService
                    self.vector_service = VectorService()
                
                result = await self.vector_service.load_dataset(dataset_id, df)
                metadata = {
                    "vectors_created": result.get("vectors_created", 0),
                    "index_name": result.get("index_name", "")
                }
            else:
                return {"success": False, "error": f"Unsupported step type: {step_type}"}
                
            # Update step status
            await self.pipeline_repo.update_pipeline_step_status(
                step["id"],
                PipelineRunStatus.COMPLETED,
                metadata
            )
            
            return {"success": True, "step_id": step["id"], "status": "completed"}
            
        except Exception as e:
            logger.error(f"Error running pipeline step {step_type}: {str(e)}")
            if step and step.get("id"):
                await self.pipeline_repo.update_pipeline_step_status(
                    step["id"],
                    PipelineRunStatus.FAILED,
                    {"error": str(e)}
                )
            return {"success": False, "error": f"Failed to run pipeline step: {str(e)}"}
            
    async def transform_data(self, dataset_id: int) -> Dict[str, Any]:
        """Transform data using defined transformations."""
        try:
            # Get dataset
            dataset = await self.dataset_repo.get_dataset(dataset_id)
            if not dataset:
                return {"success": False, "error": f"Dataset with ID {dataset_id} not found"}
            
            # Run the transform step
            return await self.run_pipeline_step(dataset_id, PipelineStepType.TRANSFORM)
        except Exception as e:
            logger.error(f"Error transforming data: {str(e)}")
            return {"success": False, "error": f"Failed to transform data: {str(e)}"}
    
    async def enrich_data(self, dataset_id: int) -> Dict[str, Any]:
        """Enrich data with external sources or derived fields."""
        try:
            # Get dataset
            dataset = await self.dataset_repo.get_dataset(dataset_id)
            if not dataset:
                return {"success": False, "error": f"Dataset with ID {dataset_id} not found"}
            
            # Get enrichment configuration from dataset metadata if available
            metadata = await self.dataset_repo.get_dataset_metadata(dataset_id) or {}
            enrichment_config = metadata.get("enrichment_config", {})
            
            # Run the enrich step with configuration
            result = await self.run_pipeline_step(
                dataset_id, 
                PipelineStepType.ENRICH, 
                enrichment_config=enrichment_config
            )
            
            if result["success"]:
                # Update dataset metadata with enrichment information
                enrichment_info = {
                    "enrichments_applied": result.get("enrichments_applied", []),
                    "new_columns": result.get("new_columns", []),
                    "enrichment_status": "completed"
                }
                
                metadata["enrichment"] = enrichment_info
                await self.dataset_repo.update_dataset_metadata(dataset_id, metadata)
            
            return result
        except Exception as e:
            logger.error(f"Error enriching data: {str(e)}")
            return {"success": False, "error": f"Failed to enrich data: {str(e)}"}
    
    async def load_to_vector_db(self, dataset_id: int) -> Dict[str, Any]:
        """Load data to vector database."""
        try:
            # Get dataset
            dataset = await self.dataset_repo.get_dataset(dataset_id)
            if not dataset:
                return {"success": False, "error": f"Dataset with ID {dataset_id} not found"}
            
            # Initialize vector service if not already done
            if not self.vector_service:
                from services.vector_service import VectorService
                self.vector_service = VectorService()
            
            # Run the load step
            result = await self.run_pipeline_step(dataset_id, PipelineStepType.LOAD)
            
            if result["success"]:
                # Update dataset metadata with vector information
                vectors_info = {
                    "vectors_created": result.get("vectors_created", 0),
                    "index_name": result.get("index_name", ""),
                    "vector_status": "indexed"
                }
                
                metadata = await self.dataset_repo.get_dataset_metadata(dataset_id) or {}
                metadata["vector_db"] = vectors_info
                await self.dataset_repo.update_dataset_metadata(dataset_id, metadata)
                
            return result
        except Exception as e:
            logger.error(f"Error loading data to vector database: {str(e)}")
            return {"success": False, "error": f"Failed to load data to vector database: {str(e)}"}

pipeline_service = PipelineService()  # Will be initialized with dataset repo
