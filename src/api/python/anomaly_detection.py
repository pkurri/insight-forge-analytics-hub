
"""
Anomaly Detection Module

This module provides functionality for detecting anomalies in datasets
using statistical methods and machine learning techniques.

In a production environment, this would be deployed as an API endpoint or microservice.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from typing import Dict, List, Any, Union, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Class for detecting anomalies in datasets"""
    
    def __init__(self, method: str = "isolation_forest", params: Optional[Dict[str, Any]] = None):
        """
        Initialize the anomaly detector
        
        Args:
            method: The anomaly detection method to use
                ("isolation_forest", "lof", "z_score", "iqr")
            params: Parameters specific to the detection method
        """
        self.method = method
        self.params = params or {}
        logger.info(f"AnomalyDetector initialized with method: {method}")
    
    def detect(self, data: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Detect anomalies in the dataset
        
        Args:
            data: Pandas DataFrame containing the dataset
            columns: List of column names to check for anomalies 
                     (if None, all numeric columns are used)
                     
        Returns:
            Dictionary with anomaly detection results
        """
        # Select columns for analysis
        if columns is None:
            # Select only numeric columns
            numeric_columns = data.select_dtypes(include=np.number).columns.tolist()
            analysis_data = data[numeric_columns]
            logger.info(f"Auto-selected {len(numeric_columns)} numeric columns for analysis")
        else:
            analysis_data = data[columns]
            logger.info(f"Using {len(columns)} specified columns for analysis")
        
        # Fill missing values for algorithm processing
        analysis_data = analysis_data.fillna(analysis_data.mean())
        
        # Run the appropriate detection method
        if self.method == "isolation_forest":
            return self._isolation_forest(analysis_data, data)
        elif self.method == "lof":
            return self._local_outlier_factor(analysis_data, data)
        elif self.method == "z_score":
            return self._z_score(analysis_data, data)
        elif self.method == "iqr":
            return self._iqr_method(analysis_data, data)
        else:
            error_msg = f"Unknown method: {self.method}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _isolation_forest(self, analysis_data: pd.DataFrame, 
                         original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use Isolation Forest algorithm to detect anomalies"""
        try:
            # Get parameters with defaults
            n_estimators = self.params.get('n_estimators', 100)
            contamination = self.params.get('contamination', 'auto')
            random_state = self.params.get('random_state', 42)
            
            # Create and fit model
            model = IsolationForest(n_estimators=n_estimators, 
                                   contamination=contamination,
                                   random_state=random_state)
            
            model.fit(analysis_data)
            # Predict: -1 for outliers and 1 for inliers
            predictions = model.predict(analysis_data)
            scores = model.decision_function(analysis_data)
            
            # Get anomaly indices
            anomaly_indices = np.where(predictions == -1)[0]
            
            return self._format_results(original_data, anomaly_indices, scores, 
                                      analysis_data.columns.tolist())
            
        except Exception as e:
            logger.error(f"Error in isolation forest: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _local_outlier_factor(self, analysis_data: pd.DataFrame, 
                             original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use Local Outlier Factor algorithm to detect anomalies"""
        try:
            # Get parameters with defaults
            n_neighbors = self.params.get('n_neighbors', 20)
            contamination = self.params.get('contamination', 0.1)
            
            # Create and fit model
            model = LocalOutlierFactor(n_neighbors=n_neighbors, 
                                      contamination=contamination)
            
            # Predict: -1 for outliers and 1 for inliers
            predictions = model.fit_predict(analysis_data)
            
            # Get anomaly indices
            anomaly_indices = np.where(predictions == -1)[0]
            
            # LOF doesn't have built-in decision function, so we use negative outlier factor
            scores = -model.negative_outlier_factor_
            
            return self._format_results(original_data, anomaly_indices, scores, 
                                      analysis_data.columns.tolist())
            
        except Exception as e:
            logger.error(f"Error in LOF: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _z_score(self, analysis_data: pd.DataFrame, 
                original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use Z-score method to detect anomalies"""
        try:
            # Get parameters with defaults
            threshold = self.params.get('threshold', 3.0)
            
            # Calculate Z-scores for each column
            z_scores = (analysis_data - analysis_data.mean()) / analysis_data.std()
            abs_z_scores = abs(z_scores)
            
            # Find rows with any Z-score exceeding the threshold
            outlier_rows = abs_z_scores.max(axis=1) > threshold
            anomaly_indices = np.where(outlier_rows)[0]
            
            # Use max Z-score as anomaly score
            scores = abs_z_scores.max(axis=1).values
            
            return self._format_results(original_data, anomaly_indices, scores, 
                                      analysis_data.columns.tolist())
            
        except Exception as e:
            logger.error(f"Error in Z-score method: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _iqr_method(self, analysis_data: pd.DataFrame, 
                   original_data: pd.DataFrame) -> Dict[str, Any]:
        """Use IQR (Interquartile Range) method to detect anomalies"""
        try:
            # Get parameters with defaults
            factor = self.params.get('factor', 1.5)
            
            # Calculate anomalies for each column
            outlier_indices_sets = []
            
            for column in analysis_data.columns:
                Q1 = analysis_data[column].quantile(0.25)
                Q3 = analysis_data[column].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - factor * IQR
                upper_bound = Q3 + factor * IQR
                
                # Find indices outside bounds
                column_outliers = analysis_data[
                    (analysis_data[column] < lower_bound) | 
                    (analysis_data[column] > upper_bound)
                ].index
                
                outlier_indices_sets.append(set(column_outliers))
            
            # Combine all outlier indices
            if outlier_indices_sets:
                all_outliers = set().union(*outlier_indices_sets)
                anomaly_indices = np.array(list(all_outliers))
            else:
                anomaly_indices = np.array([])
            
            # Create simple anomaly scores (1 for normal, >1 for anomalies based on violations)
            scores = np.ones(len(analysis_data))
            
            # For each outlier, count how many columns flagged it
            for idx in anomaly_indices:
                violation_count = sum(1 for s in outlier_indices_sets if idx in s)
                scores[idx] = 1 + violation_count
            
            return self._format_results(original_data, anomaly_indices, scores, 
                                      analysis_data.columns.tolist())
            
        except Exception as e:
            logger.error(f"Error in IQR method: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _format_results(self, original_data: pd.DataFrame, 
                       anomaly_indices: np.ndarray,
                       anomaly_scores: np.ndarray,
                       analyzed_columns: List[str]) -> Dict[str, Any]:
        """Format the results of anomaly detection"""
        try:
            # Extract anomaly data
            total_rows = len(original_data)
            anomaly_count = len(anomaly_indices)
            
            # Create detailed anomaly information
            anomalies = []
            for idx in anomaly_indices:
                anomaly_record = {
                    "index": int(idx),
                    "score": float(anomaly_scores[idx]),
                    "values": {}
                }
                
                # Add values for analyzed columns
                for col in analyzed_columns:
                    try:
                        val = original_data.iloc[idx][col]
                        # Convert numpy types to Python native types
                        if isinstance(val, (np.integer, np.floating)):
                            val = val.item()
                        anomaly_record["values"][col] = val
                    except:
                        anomaly_record["values"][col] = None
                
                anomalies.append(anomaly_record)
            
            # Sort anomalies by score (highest first)
            anomalies = sorted(anomalies, key=lambda x: x["score"], reverse=True)
            
            return {
                "success": True,
                "summary": {
                    "total_rows": total_rows,
                    "anomaly_count": anomaly_count,
                    "anomaly_percentage": (anomaly_count / total_rows * 100) if total_rows > 0 else 0,
                    "analyzed_columns": analyzed_columns,
                    "detection_method": self.method,
                },
                "anomalies": anomalies[:100]  # Limit to top 100 anomalies
            }
            
        except Exception as e:
            logger.error(f"Error formatting results: {str(e)}")
            return {"success": False, "error": str(e)}

# Example usage (would be called via API endpoint in production)
if __name__ == "__main__":
    import json
    
    # Create sample data with outliers
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, (1000, 4))
    
    # Add some outliers
    outliers = np.random.uniform(10, 20, (20, 4))
    combined_data = np.vstack([normal_data, outliers])
    
    # Create DataFrame
    df = pd.DataFrame(
        combined_data, 
        columns=["feature1", "feature2", "feature3", "feature4"]
    )
    
    # Detect anomalies using isolation forest
    detector = AnomalyDetector(method="isolation_forest")
    results = detector.detect(df)
    
    # Output summary
    print(json.dumps(results["summary"], indent=2))
    print(f"Found {len(results['anomalies'])} anomalies")
