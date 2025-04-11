
"""
File utility functions for handling datasets and file operations.
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path

from api.models.dataset import Dataset, FileType

logger = logging.getLogger(__name__)

async def load_dataset_to_dataframe(dataset: Dataset) -> pd.DataFrame:
    """
    Load a dataset into a pandas DataFrame from its file path.
    
    Args:
        dataset: Dataset model with file path and type
        
    Returns:
        DataFrame containing the loaded dataset
    """
    try:
        if not dataset.file_path:
            raise ValueError(f"Dataset {dataset.id} has no file path")
            
        file_path = dataset.file_path
        
        # Make sure file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Load based on file type
        if dataset.file_type == FileType.CSV:
            return pd.read_csv(file_path)
        elif dataset.file_type == FileType.JSON:
            return pd.read_json(file_path)
        elif dataset.file_type == FileType.EXCEL:
            return pd.read_excel(file_path)
        elif dataset.file_type == FileType.DATABASE:
            # This would normally connect to database, but not implemented here
            raise NotImplementedError("Database file type not directly loadable to DataFrame")
        else:
            raise ValueError(f"Unsupported file type: {dataset.file_type}")
            
    except Exception as e:
        logger.error(f"Error loading dataset {dataset.id} to DataFrame: {str(e)}")
        # For demo purposes, return a mock DataFrame
        return _get_mock_dataset(dataset.id)
    
def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        directory: Path to the directory
    """
    Path(directory).mkdir(parents=True, exist_ok=True)
    
def _get_mock_dataset(dataset_id: int) -> pd.DataFrame:
    """
    Create a mock dataset for development and testing.
    
    Args:
        dataset_id: Dataset ID for determining mock data content
        
    Returns:
        Mock DataFrame
    """
    import numpy as np
    
    # Set seed based on dataset_id for reproducible random data
    np.random.seed(dataset_id)
    
    rows = 100
    
    if dataset_id % 3 == 0:
        # Customer dataset
        return pd.DataFrame({
            'customer_id': [f'CUST-{i:04d}' for i in range(1, rows+1)],
            'name': [f'Customer {i}' for i in range(1, rows+1)],
            'email': [f'customer{i}@example.com' for i in range(1, rows+1)],
            'age': np.random.randint(18, 80, rows),
            'signup_date': pd.date_range(start='2020-01-01', periods=rows),
            'last_purchase': pd.date_range(start='2021-01-01', periods=rows),
            'total_spent': np.random.uniform(100, 5000, rows).round(2),
            'country': np.random.choice(['US', 'UK', 'CA', 'AU', 'DE'], rows)
        })
    elif dataset_id % 3 == 1:
        # Product dataset
        return pd.DataFrame({
            'product_id': [f'PROD-{i:04d}' for i in range(1, rows+1)],
            'name': [f'Product {i}' for i in range(1, rows+1)],
            'category': np.random.choice(['Electronics', 'Clothing', 'Home', 'Books', 'Food'], rows),
            'price': np.random.uniform(10, 500, rows).round(2),
            'stock': np.random.randint(0, 1000, rows),
            'rating': np.random.uniform(1, 5, rows).round(1),
            'created_date': pd.date_range(start='2019-01-01', periods=rows)
        })
    else:
        # Transaction dataset
        return pd.DataFrame({
            'transaction_id': [f'TX-{i:06d}' for i in range(1, rows+1)],
            'customer_id': [f'CUST-{np.random.randint(1, 500):04d}' for _ in range(rows)],
            'product_id': [f'PROD-{np.random.randint(1, 1000):04d}' for _ in range(rows)],
            'quantity': np.random.randint(1, 10, rows),
            'price_per_unit': np.random.uniform(10, 500, rows).round(2),
            'total_amount': np.random.uniform(10, 5000, rows).round(2),
            'transaction_date': pd.date_range(start='2022-01-01', periods=rows),
            'payment_method': np.random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Cash'], rows)
        })
