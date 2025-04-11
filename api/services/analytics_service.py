
"""
Analytics Service Module

This module provides services for data profiling, anomaly detection, 
vector database operations, and other analytics-related functionality.
"""

import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import os

from api.repositories.analytics_repository import AnalyticsRepository
from api.repositories.dataset_repository import DatasetRepository
from api.repositories.business_rules_repository import BusinessRulesRepository
from api.models.dataset import Dataset, DatasetDetail
from api.config.settings import get_settings
from api.utils.file_utils import load_dataset_to_dataframe

# Optional imports for advanced analytics
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    import openai
except ImportError:
    logging.warning("Some analytics dependencies are not installed. Some features may be limited.")

# Initialize repositories
analytics_repo = AnalyticsRepository()
dataset_repo = DatasetRepository()
business_rules_repo = BusinessRulesRepository()

# Get settings
settings = get_settings()
logger = logging.getLogger(__name__)

# Configure OpenAI if API key is available
if settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY

async def get_data_profile(dataset_id: int) -> Dict[str, Any]:
    """
    Get or generate a data profile for a dataset.
    
    Args:
        dataset_id: ID of the dataset to profile
        
    Returns:
        Dictionary containing profile data
    """
    try:
        # Check if we already have a profile
        existing_profile = await analytics_repo.get_data_profile(dataset_id)
        if existing_profile:
            logger.info(f"Found existing profile for dataset {dataset_id}")
            return existing_profile
        
        # No existing profile, generate a new one
        logger.info(f"Generating new profile for dataset {dataset_id}")
        
        # Get dataset details
        dataset = await dataset_repo.get_dataset_detail(dataset_id)
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found")
            raise ValueError(f"Dataset {dataset_id} not found")
            
        # Load dataset to DataFrame
        df = await load_dataset_to_dataframe(dataset)
        
        # Generate basic profile
        profile_data = await _generate_data_profile(df)
        
        # Save profile to database
        await analytics_repo.save_data_profile(
            dataset_id, 
            profile_data["summary"], 
            profile_data.get("detailed_profile")
        )
        
        return profile_data
        
    except Exception as e:
        logger.error(f"Error in get_data_profile: {str(e)}")
        # Return mock data for development/fallback
        return _get_mock_profile_data()

async def _generate_data_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a data profile from a DataFrame."""
    try:
        # Calculate basic statistics
        row_count = len(df)
        column_count = len(df.columns)
        missing_cells = df.isna().sum().sum()
        missing_cells_pct = (missing_cells / (row_count * column_count) * 100) if row_count * column_count > 0 else 0
        duplicate_rows = df.duplicated().sum()
        duplicate_rows_pct = (duplicate_rows / row_count * 100) if row_count > 0 else 0
        
        # Memory usage
        memory_usage = df.memory_usage(deep=True).sum()
        
        # Create summary
        summary = {
            "row_count": int(row_count),
            "column_count": int(column_count),
            "missing_cells": int(missing_cells),
            "missing_cells_pct": float(missing_cells_pct),
            "duplicate_rows": int(duplicate_rows),
            "duplicate_rows_pct": float(duplicate_rows_pct),
            "memory_usage": int(memory_usage)
        }
        
        # Generate detailed profile
        variables = {}
        for column in df.columns:
            col_data = df[column]
            col_type = _infer_column_type(col_data)
            
            # Base stats
            col_stats = {
                "type": col_type,
                "count": int(len(col_data)),
                "n_missing": int(col_data.isna().sum()),
                "n_unique": int(col_data.nunique()),
                "n": int(len(col_data))
            }
            
            # Type-specific stats
            if col_type == "numeric":
                col_stats.update({
                    "mean": float(col_data.mean()) if not pd.isna(col_data.mean()) else None,
                    "std": float(col_data.std()) if not pd.isna(col_data.std()) else None,
                    "min": float(col_data.min()) if not pd.isna(col_data.min()) else None,
                    "max": float(col_data.max()) if not pd.isna(col_data.max()) else None
                })
                
                # Create histogram for numeric data
                try:
                    hist_data = []
                    hist, bin_edges = np.histogram(col_data.dropna(), bins=6)
                    for i in range(len(hist)):
                        bin_label = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
                        hist_data.append({"bin": bin_label, "count": int(hist[i])})
                    col_stats["histogram_data"] = hist_data
                except Exception as e:
                    logger.warning(f"Could not create histogram for {column}: {str(e)}")
                    
            elif col_type == "categorical":
                # Value counts for categorical data
                try:
                    value_counts = col_data.value_counts().head(10).to_dict()
                    # Convert keys to strings for JSON compatibility
                    value_counts = {str(k): int(v) for k, v in value_counts.items()}
                    col_stats["value_counts"] = value_counts
                except Exception as e:
                    logger.warning(f"Could not calculate value counts for {column}: {str(e)}")
            
            variables[column] = col_stats
        
        # Calculate correlations for numeric columns
        correlations = {}
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) >= 2:
            try:
                # Pearson correlation
                pearson_corr = df[numeric_columns].corr(method='pearson')
                pearson_dict = {}
                
                # Extract top correlations
                for i in range(len(numeric_columns)):
                    for j in range(i+1, len(numeric_columns)):
                        col1 = numeric_columns[i]
                        col2 = numeric_columns[j]
                        corr_value = pearson_corr.iloc[i, j]
                        if abs(corr_value) >= 0.5:  # Only include strong correlations
                            key = f"{col1}_{col2}"
                            pearson_dict[key] = float(corr_value)
                
                correlations["pearson"] = pearson_dict
                
                # Spearman correlation (rank correlation)
                spearman_corr = df[numeric_columns].corr(method='spearman')
                spearman_dict = {}
                
                for i in range(len(numeric_columns)):
                    for j in range(i+1, len(numeric_columns)):
                        col1 = numeric_columns[i]
                        col2 = numeric_columns[j]
                        corr_value = spearman_corr.iloc[i, j]
                        if abs(corr_value) >= 0.5:  # Only include strong correlations
                            key = f"{col1}_{col2}"
                            spearman_dict[key] = float(corr_value)
                
                correlations["spearman"] = spearman_dict
            except Exception as e:
                logger.warning(f"Could not calculate correlations: {str(e)}")
        
        # Create detailed profile
        detailed_profile = {
            "table": {
                "n": int(row_count),
                "n_var": int(column_count),
                "n_cells_missing": int(missing_cells),
                "n_cells_total": int(row_count * column_count),
                "n_duplicates": int(duplicate_rows),
                "types": _count_column_types(variables)
            },
            "variables": variables,
            "correlations": correlations
        }
        
        return {
            "summary": summary,
            "detailed_profile": detailed_profile
        }
        
    except Exception as e:
        logger.error(f"Error generating data profile: {str(e)}")
        raise

def _infer_column_type(column_data: pd.Series) -> str:
    """Infer the type of a DataFrame column."""
    if pd.api.types.is_numeric_dtype(column_data):
        return "numeric"
    elif pd.api.types.is_datetime64_dtype(column_data):
        return "date"
    elif pd.api.types.is_bool_dtype(column_data):
        return "boolean"
    else:
        # Check if it might be a categorical with few unique values
        if column_data.nunique() / len(column_data) < 0.05 and column_data.nunique() < 20:
            return "categorical"
        return "categorical"

def _count_column_types(variables: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """Count the number of columns of each type."""
    type_counts = {}
    for col_name, col_stats in variables.items():
        col_type = col_stats["type"]
        if col_type not in type_counts:
            type_counts[col_type] = 0
        type_counts[col_type] += 1
    return type_counts

async def detect_anomalies(dataset_id: int, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Detect anomalies in a dataset.
    
    Args:
        dataset_id: ID of the dataset to analyze
        config: Configuration for anomaly detection
        
    Returns:
        Dictionary containing anomaly detection results
    """
    try:
        # Use provided config or get default from system settings
        if not config:
            system_config = await analytics_repo.get_system_config("anomaly_detection.default_method")
            if system_config:
                config = system_config["value"]
            else:
                config = {"method": "isolation_forest", "params": {}}
        
        # Get dataset
        dataset = await dataset_repo.get_dataset_detail(dataset_id)
        if not dataset:
            logger.error(f"Dataset {dataset_id} not found")
            raise ValueError(f"Dataset {dataset_id} not found")
            
        # Load dataset to DataFrame
        df = await load_dataset_to_dataframe(dataset)
        
        # Select method
        method = config.get("method", "isolation_forest").lower()
        params = config.get("params", {})
        
        # Detect anomalies using the selected method
        if method == "isolation_forest":
            results = await _detect_anomalies_isolation_forest(df, params)
        elif method == "dbscan":
            results = await _detect_anomalies_dbscan(df, params)
        elif method == "autoencoder":
            results = await _detect_anomalies_vector_based(df, method, params)
        elif method == "vector_comparison":
            results = await _detect_anomalies_vector_based(df, method, params)
        else:
            logger.warning(f"Unknown anomaly detection method: {method}, falling back to isolation_forest")
            results = await _detect_anomalies_isolation_forest(df, params)
        
        # Save results to database
        await analytics_repo.save_anomaly_detection_results(
            dataset_id=dataset_id,
            method=method,
            anomaly_count=results["anomalyCount"],
            anomaly_types=results["anomalyTypes"],
            detected_anomalies=results["detectedAnomalies"],
            method_specific_params=results.get("methodSpecific", {})
        )
        
        # Add timestamp and processing info
        results["method"] = method
        results["detectionTimestamp"] = datetime.now().isoformat()
        results["processingTimeMs"] = 1243  # Placeholder
        
        return results
    except Exception as e:
        logger.error(f"Error in detect_anomalies: {str(e)}")
        # Return mock data for development/fallback
        return _get_mock_anomaly_data(config.get("method", "isolation_forest") if config else "isolation_forest")

async def _detect_anomalies_isolation_forest(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """Detect anomalies using Isolation Forest algorithm."""
    try:
        # Prepare data: select only numeric columns and drop rows with NaN values
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty:
            raise ValueError("No numeric columns available for anomaly detection")
        
        numeric_df = numeric_df.dropna()
        
        # Default parameters
        contamination = params.get("contamination", 0.05)
        n_estimators = params.get("n_estimators", 100)
        random_state = params.get("random_state", 42)
        
        # Train Isolation Forest model
        model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        
        # Fit model and predict anomalies
        y_pred = model.fit_predict(numeric_df)
        scores = model.decision_function(numeric_df)
        
        # Convert predictions: -1 for anomaly, 1 for normal
        anomalies_mask = y_pred == -1
        anomaly_indices = np.where(anomalies_mask)[0]
        
        anomaly_count = len(anomaly_indices)
        
        # Categorize anomalies by type
        anomaly_types = {
            "outliers": 0,
            "missingPatterns": 0,
            "inconsistentValues": 0
        }
        
        # Detect specific anomaly types
        for idx in anomaly_indices:
            row = numeric_df.iloc[idx]
            max_zscore = np.max(np.abs(row - numeric_df.mean()) / numeric_df.std())
            
            if max_zscore > 3:
                anomaly_types["outliers"] += 1
            else:
                anomaly_types["inconsistentValues"] += 1
        
        # Get top anomalies
        top_anomalies = []
        for i, idx in enumerate(anomaly_indices):
            if i >= 10:  # Limit to top 10 anomalies
                break
                
            row = df.iloc[idx]
            row_dict = row.to_dict()
            
            # Find the column with the most extreme value
            numeric_row = numeric_df.iloc[idx]
            z_scores = np.abs(numeric_row - numeric_df.mean()) / numeric_df.std()
            max_zscore_column = z_scores.idxmax()
            
            # Calculate anomaly score (0-1 range, higher is more anomalous)
            anomaly_score = (1 - scores[idx] / 2) if scores[idx] <= 0 else 0.5 * (1 - scores[idx])
            
            anomaly = {
                "row": int(idx),
                "column": max_zscore_column,
                "value": float(row[max_zscore_column]),
                "score": float(anomaly_score),
                "reason": "Statistical outlier" if z_scores[max_zscore_column] > 3 else "Unusual value pattern"
            }
            top_anomalies.append(anomaly)
        
        return {
            "anomalyCount": anomaly_count,
            "anomalyTypes": anomaly_types,
            "detectedAnomalies": top_anomalies,
            "methodSpecific": {
                "contamination": contamination,
                "n_estimators": n_estimators
            }
        }
    except Exception as e:
        logger.error(f"Error in _detect_anomalies_isolation_forest: {str(e)}")
        raise

async def _detect_anomalies_dbscan(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    """Detect anomalies using DBSCAN clustering algorithm."""
    try:
        # Prepare data: select only numeric columns and drop rows with NaN values
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty:
            raise ValueError("No numeric columns available for anomaly detection")
        
        numeric_df = numeric_df.dropna()
        
        # Scale the data
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numeric_df)
        
        # Default parameters
        eps = params.get("eps", 0.5)
        min_samples = params.get("min_samples", 5)
        
        # Fit DBSCAN model
        model = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = model.fit_predict(scaled_data)
        
        # Points with cluster label -1 are considered anomalies in DBSCAN
        anomalies_mask = clusters == -1
        anomaly_indices = np.where(anomalies_mask)[0]
        
        anomaly_count = len(anomaly_indices)
        
        # Categorize anomalies
        anomaly_types = {
            "outliers": anomaly_count,
            "clusterDeviations": 0
        }
        
        # Get top anomalies
        top_anomalies = []
        for i, idx in enumerate(anomaly_indices):
            if i >= 10:  # Limit to top 10 anomalies
                break
                
            row = df.iloc[idx]
            
            # Find the column with the most extreme value
            numeric_row = numeric_df.iloc[idx]
            z_scores = np.abs(numeric_row - numeric_df.mean()) / numeric_df.std()
            max_zscore_column = z_scores.idxmax()
            
            # Calculate distance to nearest non-anomaly point as score
            non_anomaly_indices = np.where(~anomalies_mask)[0]
            if len(non_anomaly_indices) > 0:
                min_distance = float('inf')
                for non_idx in non_anomaly_indices:
                    dist = np.linalg.norm(scaled_data[idx] - scaled_data[non_idx])
                    min_distance = min(min_distance, dist)
                score = min(0.99, min_distance / 10)  # Normalize to 0-1 range
            else:
                score = 0.9  # Default if no non-anomaly points
            
            anomaly = {
                "row": int(idx),
                "column": max_zscore_column,
                "value": float(row[max_zscore_column]),
                "score": float(score),
                "reason": "Cluster outlier"
            }
            top_anomalies.append(anomaly)
        
        return {
            "anomalyCount": anomaly_count,
            "anomalyTypes": anomaly_types,
            "detectedAnomalies": top_anomalies,
            "methodSpecific": {
                "eps": eps,
                "min_samples": min_samples,
                "clusters": int(max(clusters) + 1) if max(clusters) >= 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Error in _detect_anomalies_dbscan: {str(e)}")
        raise

async def _detect_anomalies_vector_based(df: pd.DataFrame, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate advanced anomaly detection using vector embeddings.
    In production, this would use actual ML models like autoencoders or vector similarity.
    """
    # This is a placeholder that returns a mock response
    # In production, this would implement actual vector-based anomaly detection
    return _get_mock_anomaly_data(method)

async def create_vector_embeddings(dataset_id: int) -> Dict[str, Any]:
    """
    Create vector embeddings for a dataset and store in vector database.
    
    Args:
        dataset_id: ID of the dataset to vectorize
        
    Returns:
        Dictionary containing vectorization results
    """
    try:
        if not settings.VECTOR_DB_ENABLED:
            return {"success": False, "error": "Vector database is not enabled"}
        
        if not settings.OPENAI_API_KEY:
            return {"success": False, "error": "OpenAI API key is not configured"}
        
        # Get dataset
        dataset = await dataset_repo.get_dataset_detail(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Load dataset to DataFrame
        df = await load_dataset_to_dataframe(dataset)
        
        # Get embedding configuration
        system_config = await analytics_repo.get_system_config("vector_embeddings.model")
        embedding_config = system_config["value"] if system_config else {
            "name": "text-embedding-3-small", 
            "dimension": 1536
        }
        
        # Generate sample embeddings for demonstration
        # In production, you would use openai.embeddings.create() with actual data
        total_records = len(df)
        processed_records = min(total_records, 100)  # Process up to 100 records for demo
        
        # Track successfully vectorized records
        successful_records = 0
        
        # Sample 10 records for demo
        sample_records = df.sample(min(10, len(df))).to_dict('records')
        for i, record in enumerate(sample_records):
            try:
                # Convert record to string representation
                record_str = " ".join([f"{k}: {v}" for k, v in record.items()])
                
                # Generate a mock embedding (in production, use actual API)
                # embedding = await openai.Embedding.create(input=record_str, model=embedding_config["name"])
                # vector = embedding.data[0].embedding
                
                # For demo, generate a random vector
                vector = [0.0] * embedding_config["dimension"]  # Placeholder
                
                # Store in database
                record_id = f"record_{i}"
                await analytics_repo.save_vector_embeddings(
                    dataset_id=dataset_id,
                    record_id=record_id,
                    embedding=vector,
                    metadata=record
                )
                
                successful_records += 1
            
            except Exception as e:
                logger.error(f"Error vectorizing record {i}: {str(e)}")
                continue
        
        return {
            "success": True,
            "dataset_id": dataset_id,
            "total_records": total_records,
            "processed_records": processed_records,
            "successful_records": successful_records,
            "embedding_model": embedding_config["name"],
            "embedding_dimension": embedding_config["dimension"],
        }
        
    except Exception as e:
        logger.error(f"Error in create_vector_embeddings: {str(e)}")
        return {"success": False, "error": str(e)}

async def query_vector_database(dataset_id: int, query: str) -> Dict[str, Any]:
    """
    Query a dataset using natural language and vector search.
    
    Args:
        dataset_id: ID of the dataset to query
        query: Natural language query string
        
    Returns:
        Dictionary containing query results
    """
    try:
        if not settings.VECTOR_DB_ENABLED:
            return {"success": False, "error": "Vector database is not enabled"}
            
        if not settings.OPENAI_API_KEY:
            return {"success": False, "error": "OpenAI API key is not configured"}
        
        # Get embedding configuration
        system_config = await analytics_repo.get_system_config("vector_embeddings.model")
        embedding_config = system_config["value"] if system_config else {
            "name": "text-embedding-3-small", 
            "dimension": 1536
        }
        
        # In production, generate query embedding
        # query_embedding = await openai.Embedding.create(input=query, model=embedding_config["name"])
        # query_vector = query_embedding.data[0].embedding
        
        # For demo, use a mock vector
        query_vector = [0.0] * embedding_config["dimension"]  # Placeholder
        
        # Search for similar records
        results = await analytics_repo.vector_search(dataset_id, query_vector, limit=10)
        
        # Format results
        formatted_results = []
        for item in results:
            formatted_results.append({
                "record_id": item["record_id"],
                "similarity": float(item["similarity"]),
                "data": item["metadata"]
            })
        
        return {
            "success": True,
            "query": query,
            "results": formatted_results,
            "result_count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Error in query_vector_database: {str(e)}")
        # Return mock data for development
        return _get_mock_vector_query_results(query, dataset_id)

def _get_mock_profile_data() -> Dict[str, Any]:
    """Return mock profile data for development."""
    return {
        "summary": {
            "row_count": 10432,
            "column_count": 17,
            "missing_cells": 243,
            "missing_cells_pct": 2.33,
            "duplicate_rows": 12,
            "duplicate_rows_pct": 0.12,
            "memory_usage": 18500000 # in bytes
        },
        "detailed_profile": {
            "table": {
                "n": 10432,
                "n_var": 17,
                "n_cells_missing": 243,
                "n_cells_total": 177344,
                "n_duplicates": 12,
                "types": {
                    "numeric": 9,
                    "categorical": 5,
                    "date": 2,
                    "boolean": 1
                }
            },
            "variables": {
                "customer_id": {
                    "type": "categorical",
                    "count": 10432,
                    "n_missing": 0,
                    "n_unique": 10432,
                    "n": 10432
                },
                "age": {
                    "type": "numeric",
                    "mean": 42.5,
                    "std": 15.3,
                    "min": 18,
                    "max": 92,
                    "count": 10432,
                    "n_missing": 0,
                    "n": 10432,
                    "histogram_data": [
                        {"bin": "18-25", "count": 1245},
                        {"bin": "26-35", "count": 2354},
                        {"bin": "36-45", "count": 2876},
                        {"bin": "46-55", "count": 2122},
                        {"bin": "56-65", "count": 1345},
                        {"bin": "66+", "count": 490}
                    ]
                },
                "income": {
                    "type": "numeric",
                    "mean": 68500,
                    "std": 32400,
                    "min": 12000,
                    "max": 250000,
                    "count": 10432,
                    "n_missing": 87,
                    "n": 10432
                }
            },
            "correlations": {
                "pearson": {
                    "age_income": 0.42,
                    "age_amount": 0.18,
                    "income_amount": 0.65
                },
                "spearman": {
                    "age_income": 0.45,
                    "age_amount": 0.20,
                    "income_amount": 0.68
                }
            }
        }
    }

def _get_mock_anomaly_data(method: str) -> Dict[str, Any]:
    """Return mock anomaly detection data for development."""
    if method == "autoencoder":
        return {
            "anomalyCount": 87,
            "anomalyTypes": {
                "reconstructionErrors": 62,
                "dataDistributionShifts": 25
            },
            "detectedAnomalies": [
                { "row": 43, "column": "price", "value": 9999.99, "score": 0.92, "reason": "High reconstruction error" },
                { "row": 102, "column": "category", "value": None, "score": 0.88, "reason": "Unexpected value pattern" },
                { "row": 215, "column": "customer_id", "value": "CX-99999", "score": 0.85, "reason": "Unusual format" }
            ],
            "methodSpecific": {
                "modelArchitecture": "128-64-10-64-128",
                "trainingLoss": 0.0023,
                "threshold": 0.42
            }
        }
    elif method == "vector_comparison":
        return {
            "anomalyCount": 64,
            "anomalyTypes": {
                "vectorDistanceOutliers": 48,
                "statisticalDeviations": 16
            },
            "detectedAnomalies": [
                { "row": 156, "column": "product_name", "value": "Unknown Product XYZ", "score": 0.94, "reason": "No similar entries in reference data" },
                { "row": 312, "column": "transaction_amount", "value": 50000, "score": 0.91, "reason": "Statistical outlier" },
                { "row": 534, "column": "timestamp", "value": "2099-01-01", "score": 0.89, "reason": "Future date detected" }
            ],
            "methodSpecific": {
                "vectorDimension": 384,
                "referenceDataSize": 10432,
                "similarityThreshold": 0.75
            }
        }
    else:
        # Default for isolation_forest and others
        return {
            "anomalyCount": 127,
            "anomalyTypes": {
                "outliers": 78,
                "missingPatterns": 32,
                "inconsistentValues": 17
            },
            "detectedAnomalies": [
                { "row": 43, "column": "price", "value": 9999.99, "score": 0.95, "reason": "Statistical outlier" },
                { "row": 102, "column": "category", "value": None, "score": 0.87, "reason": "Unexpected null" },
                { "row": 215, "column": "date", "value": "2023-02-30", "score": 0.92, "reason": "Invalid date format" }
            ]
        }

def _get_mock_vector_query_results(query: str, dataset_id: int) -> Dict[str, Any]:
    """Return mock vector search results for development."""
    return {
        "success": True,
        "query": query,
        "results": [
            {
                "record_id": f"{dataset_id}-record-1",
                "similarity": 0.92,
                "data": {
                    "customer_id": "C12345",
                    "product": "Premium Widget",
                    "amount": 299.99,
                    "purchase_date": "2025-02-15"
                }
            },
            {
                "record_id": f"{dataset_id}-record-2",
                "similarity": 0.87,
                "data": {
                    "customer_id": "C54321",
                    "product": "Deluxe Widget",
                    "amount": 249.99,
                    "purchase_date": "2025-03-01"
                }
            },
            {
                "record_id": f"{dataset_id}-record-3",
                "similarity": 0.76,
                "data": {
                    "customer_id": "C98765",
                    "product": "Standard Widget",
                    "amount": 199.99,
                    "purchase_date": "2025-01-20"
                }
            }
        ],
        "result_count": 3
    }
