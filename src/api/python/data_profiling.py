
"""
Data Profiling Module

This module provides functionality for generating comprehensive profiles of datasets
using the ydata-profiling library (formerly pandas-profiling).

In a production environment, this would be deployed as an API endpoint or microservice.
"""

import pandas as pd
from ydata_profiling import ProfileReport
import json
import os
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProfiler:
    """Class for generating data profiles from datasets"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data profiler with configuration
        
        Args:
            config: Dictionary of configuration parameters for profiling
        """
        self.config = config or {
            "minimal": False,
            "explorative": True,
            "correlations": {
                "pearson": True,
                "spearman": True,
                "kendall": True,
                "phi_k": True,
                "cramers": True,
            },
            "missing_diagrams": {
                "bar": True,
                "matrix": True,
                "heatmap": True,
            }
        }
        logger.info("DataProfiler initialized with config: %s", self.config)
    
    def profile_dataset(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a comprehensive profile of the dataset
        
        Args:
            data: Pandas DataFrame containing the dataset to profile
            
        Returns:
            Dictionary containing the profile data
        """
        logger.info(f"Profiling dataset with {len(data)} rows and {len(data.columns)} columns")
        
        try:
            # Generate the profile report
            profile = ProfileReport(data, title="DataForge Data Profile", **self.config)
            
            # Get the JSON representation
            profile_json = json.loads(profile.to_json())
            
            # Extract key metrics for quick access
            summary_stats = {
                "row_count": len(data),
                "column_count": len(data.columns),
                "missing_cells": data.isna().sum().sum(),
                "missing_cells_pct": (data.isna().sum().sum() / (len(data) * len(data.columns)) * 100),
                "duplicate_rows": sum(data.duplicated()),
                "duplicate_rows_pct": (sum(data.duplicated()) / len(data) * 100),
                "memory_usage": data.memory_usage(deep=True).sum(),
            }
            
            return {
                "success": True,
                "summary": summary_stats,
                "detailed_profile": profile_json,
            }
            
        except Exception as e:
            logger.error(f"Error generating profile: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def profile_from_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load a file and generate a profile
        
        Args:
            filepath: Path to the file (CSV, Excel, etc.)
            
        Returns:
            Dictionary containing the profile data
        """
        try:
            # Determine file type from extension
            _, ext = os.path.splitext(filepath)
            ext = ext.lower()
            
            if ext == '.csv':
                data = pd.read_csv(filepath)
            elif ext in ['.xlsx', '.xls']:
                data = pd.read_excel(filepath)
            elif ext == '.json':
                data = pd.read_json(filepath)
            elif ext == '.parquet':
                data = pd.read_parquet(filepath)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {ext}"
                }
                
            return self.profile_dataset(data)
            
        except Exception as e:
            logger.error(f"Error loading file {filepath}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage (would be called via API endpoint in production)
if __name__ == "__main__":
    # Create sample data
    import numpy as np
    
    # Create sample data
    np.random.seed(42)
    sample_data = pd.DataFrame({
        'numeric_col': np.random.normal(0, 1, 1000),
        'categorical_col': np.random.choice(['A', 'B', 'C', None], 1000),
        'date_col': pd.date_range(start='2020-01-01', periods=1000),
        'id_col': range(1000),
        'missing_col': np.random.choice([np.nan, 1, 2], 1000)
    })
    
    # Profile the data
    profiler = DataProfiler()
    profile_results = profiler.profile_dataset(sample_data)
    
    # Output summary
    print(json.dumps(profile_results["summary"], indent=2))
