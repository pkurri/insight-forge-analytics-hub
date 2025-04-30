from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime

class DataCleaningService:
    def __init__(self):
        self.numeric_imputer = SimpleImputer(strategy='mean')
        self.categorical_imputer = SimpleImputer(strategy='most_frequent')
        self.scaler = StandardScaler()
        self.label_encoders = {}

    async def clean_data(self, df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Clean the input dataframe using scikit-learn preprocessing tools
        """
        config = config or {}
        
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Handle missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        categorical_columns = df.select_dtypes(include=['object']).columns
        
        if len(numeric_columns) > 0:
            df[numeric_columns] = self.numeric_imputer.fit_transform(df[numeric_columns])
        
        if len(categorical_columns) > 0:
            df[categorical_columns] = self.categorical_imputer.fit_transform(df[categorical_columns])
        
        # Handle categorical encoding if specified
        if config.get('encode_categorical', True):
            for col in categorical_columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col])
        
        # Handle scaling if specified
        if config.get('scale_numeric', True):
            df[numeric_columns] = self.scaler.fit_transform(df[numeric_columns])
        
        # Add dataset_metadata
        cleaning_dataset_metadata = {
            'timestamp': datetime.utcnow().isoformat(),
            'rows_processed': len(df),
            'columns_processed': list(df.columns),
            'numeric_columns': list(numeric_columns),
            'categorical_columns': list(categorical_columns)
        }
        
        return df, cleaning_dataset_metadata
