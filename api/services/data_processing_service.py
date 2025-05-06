import pandas as pd
from typing import Dict, Any, Optional
from models.dataset import PipelineRunStatus

class DataProcessingService:
    """Service for data processing operations."""
    
    async def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the data by handling missing values, duplicates, etc."""
        # Make a copy to avoid modifying the original
        cleaned_df = df.copy()
        
        # Handle missing values
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype in ['int64', 'float64']:
                # For numeric columns, fill with median
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
            else:
                # For categorical/text columns, fill with mode
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0])
        
        # Remove duplicates
        cleaned_df = cleaned_df.drop_duplicates()
        
        # Remove leading/trailing whitespace from string columns
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == 'object':
                cleaned_df[col] = cleaned_df[col].str.strip()
        
        return cleaned_df
    
    async def transform_data(
        self,
        df: pd.DataFrame,
        transformations: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply transformations to the data."""
        # Make a copy to avoid modifying the original
        transformed_df = df.copy()
        
        for col, transform in transformations.items():
            if col not in transformed_df.columns:
                continue
                
            if transform.get("type") == "scale":
                # Min-max scaling
                min_val = transformed_df[col].min()
                max_val = transformed_df[col].max()
                transformed_df[col] = (transformed_df[col] - min_val) / (max_val - min_val)
                
            elif transform.get("type") == "normalize":
                # Z-score normalization
                mean = transformed_df[col].mean()
                std = transformed_df[col].std()
                transformed_df[col] = (transformed_df[col] - mean) / std
                
            elif transform.get("type") == "encode":
                # One-hot encoding
                if transform.get("method") == "onehot":
                    dummies = pd.get_dummies(transformed_df[col], prefix=col)
                    transformed_df = pd.concat([transformed_df, dummies], axis=1)
                    transformed_df = transformed_df.drop(col, axis=1)
                    
            elif transform.get("type") == "bin":
                # Binning
                if transform.get("method") == "equal_width":
                    bins = transform.get("bins", 10)
                    transformed_df[col] = pd.qcut(transformed_df[col], bins, labels=False)
                    
            elif transform.get("type") == "custom":
                # Custom transformation using a function
                if "function" in transform:
                    transformed_df[col] = transform["function"](transformed_df[col])
        
        return transformed_df
    
    async def enrich_data(
        self,
        df: pd.DataFrame,
        enrichments: Dict[str, Any]
    ) -> pd.DataFrame:
        """Enrich the data with additional information."""
        # Make a copy to avoid modifying the original
        enriched_df = df.copy()
        
        for col, enrichment in enrichments.items():
            if col not in enriched_df.columns:
                continue
                
            if enrichment.get("type") == "lookup":
                # Lookup values from another dataset
                lookup_df = pd.read_csv(enrichment["file_path"])
                enriched_df = enriched_df.merge(
                    lookup_df,
                    left_on=col,
                    right_on=enrichment["lookup_column"],
                    how="left"
                )
                
            elif enrichment.get("type") == "calculate":
                # Calculate new values
                if enrichment.get("method") == "rolling":
                    window = enrichment.get("window", 3)
                    enriched_df[f"{col}_rolling_mean"] = enriched_df[col].rolling(window=window).mean()
                    enriched_df[f"{col}_rolling_std"] = enriched_df[col].rolling(window=window).std()
                    
            elif enrichment.get("type") == "custom":
                # Custom enrichment using a function
                if "function" in enrichment:
                    enriched_df[col] = enrichment["function"](enriched_df[col])
        
        return enriched_df 