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
from models.dataset import DatasetStatus

settings = get_settings()
logger = logging.getLogger(__name__)
dataset_repo = DatasetRepository()

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
            Processing results and metadata
        """
        try:
            # Get dataset
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
            
            # Update dataset metadata
            metadata = {
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
                metadata
            )
            
            return {
                "success": True,
                "metadata": metadata,
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
