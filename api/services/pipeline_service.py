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

from api.config.settings import get_settings
from api.repositories.dataset_repository import DatasetRepository
from api.models.dataset import DatasetStatus

settings = get_settings()
logger = logging.getLogger(__name__)

import asyncio
import time

def run_pipeline_step(pipeline: 'DataPipeline', step_type: str, df: pd.DataFrame, rules: dict = None, status: dict = None, **kwargs) -> Any:
    """
    Dispatch to the correct DataPipeline method based on step_type.
    Logs start/end/duration, supports rule-based skipping, and updates status dict.
    """
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

# Add new async methods to DataPipeline for enrichment and custom transformation
from typing import Callable

class DataPipeline:
    def __init__(self):
        self.imputer = SimpleImputer(strategy='mean')
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.anomaly_detector = IsolationForest(contamination=0.1)

    # Existing methods: _clean_data, _validate_data, etc. (not shown here for brevity)

    async def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich data using external APIs or knowledge bases."""
        df["enriched"] = "external_info"
        logger.info("Data enriched.")
        return df

    async def custom_transform(self, df: pd.DataFrame, transform_func: Optional[Callable] = None, **kwargs) -> pd.DataFrame:
        """Apply a custom transformation function to the DataFrame."""
        if transform_func:
            df = transform_func(df, **kwargs)
            logger.info("Custom transformation applied.")
        return df

    async def run_dynamic_pipeline(self, df: pd.DataFrame, steps: list, rules: dict = None, parallelizable: list = None, **kwargs) -> dict:
        """Run a dynamic pipeline as specified by the user, supporting async/parallel steps and rule-based logic."""
        results = {}
        status = {}
        rules = rules or {}
        parallelizable = parallelizable or []
        for step in steps:
            if step in parallelizable:
                coros = [run_pipeline_step(self, s, df, rules=rules, status=status, **kwargs) for s in parallelizable]
                step_results = await asyncio.gather(*coros, return_exceptions=True)
                for s, r in zip(parallelizable, step_results):
                    results[s] = r
            else:
                results[step] = await run_pipeline_step(self, step, df, rules=rules, status=status, **kwargs)
        return {"results": results, "status": status}

async def run_pipeline_step(pipeline: 'DataPipeline', step_type: str, df: pd.DataFrame, rules: dict = None, status: dict = None, **kwargs) -> Any:
    """
    Dispatch to the correct DataPipeline method based on step_type.
    Logs start/end/duration, supports rule-based skipping, and updates status dict.
    Integrates OpenEvals for quality and rule evaluation after each step.
    """
    from api.services.openevals_service import openevals_service
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
        from api.services.openevals_service import openevals_service
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
            from api.repositories.dataset_repository import DatasetRepository
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
