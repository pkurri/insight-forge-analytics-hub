import logging
import json
import pandas as pd
import numpy as np
import asyncpg
from typing import Dict, Any, List, Optional

from api.config import get_db_config

logger = logging.getLogger(__name__)

class DataTransformerService:
    """Service for transforming datasets based on defined rules"""
    
    def __init__(self):
        self.pool = None
        
    async def initialize(self):
        """Initialize the database connection pool"""
        if self.pool is None:
            try:
                db_config = get_db_config()
                self.pool = await asyncpg.create_pool(**db_config)
                logger.info("Data transformer service initialized with asyncpg connection pool")
            except Exception as e:
                logger.error(f"Failed to initialize data transformer service: {str(e)}")
                raise
    
    async def transform_data(self, dataset_id: int, transformation_rules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Transform a dataset based on defined rules
        
        Args:
            dataset_id: ID of the dataset to transform
            transformation_rules: List of transformation rules to apply
            
        Returns:
            Dictionary with transformation results
        """
        await self.initialize()
        
        try:
            # Get dataset information
            async with self.pool.acquire() as conn:
                dataset = await conn.fetchrow(
                    """
                    SELECT id, name, file_path, file_format
                    FROM datasets
                    WHERE id = $1
                    """,
                    dataset_id
                )
                
                if not dataset:
                    return {
                        "success": False,
                        "error": f"Dataset with ID {dataset_id} not found"
                    }
                
                # Get dataset metadata
                metadata_row = await conn.fetchrow(
                    """
                    SELECT metadata
                    FROM dataset_metadata
                    WHERE dataset_id = $1
                    """,
                    dataset_id
                )
                
                metadata = json.loads(metadata_row["metadata"]) if metadata_row else {}
            
            # Load the dataset
            file_path = dataset["file_path"]
            file_format = dataset["file_format"]
            
            if file_format.lower() == "csv":
                df = pd.read_csv(file_path)
            elif file_format.lower() == "json":
                df = pd.read_json(file_path)
            elif file_format.lower() == "excel" or file_format.lower() == "xlsx":
                df = pd.read_excel(file_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {file_format}"
                }
            
            # If no transformation rules provided, get from database
            if not transformation_rules:
                async with self.pool.acquire() as conn:
                    rules_row = await conn.fetchrow(
                        """
                        SELECT rules
                        FROM transformation_rules
                        WHERE dataset_id = $1
                        """,
                        dataset_id
                    )
                    
                    if rules_row:
                        transformation_rules = json.loads(rules_row["rules"])
                    else:
                        # No rules found, return original dataset
                        return {
                            "success": True,
                            "dataset_id": dataset_id,
                            "message": "No transformation rules found, dataset remains unchanged",
                            "transformations_applied": 0
                        }
            
            # Apply transformations
            transformations_applied = 0
            transformation_details = []
            
            for rule in transformation_rules:
                rule_type = rule.get("type")
                column = rule.get("column")
                
                if not column or not rule_type:
                    continue
                
                if column not in df.columns:
                    transformation_details.append({
                        "rule": rule,
                        "status": "skipped",
                        "reason": f"Column '{column}' not found in dataset"
                    })
                    continue
                
                try:
                    # Handle different transformation types
                    if rule_type == "fill_missing":
                        value = rule.get("value", 0)
                        df[column] = df[column].fillna(value)
                        transformations_applied += 1
                        transformation_details.append({
                            "rule": rule,
                            "status": "success",
                            "affected_rows": df[column].isna().sum()
                        })
                    
                    elif rule_type == "normalize":
                        if pd.api.types.is_numeric_dtype(df[column]):
                            min_val = df[column].min()
                            max_val = df[column].max()
                            if max_val > min_val:
                                df[column] = (df[column] - min_val) / (max_val - min_val)
                                transformations_applied += 1
                                transformation_details.append({
                                    "rule": rule,
                                    "status": "success",
                                    "affected_rows": len(df)
                                })
                        else:
                            transformation_details.append({
                                "rule": rule,
                                "status": "skipped",
                                "reason": f"Column '{column}' is not numeric"
                            })
                    
                    elif rule_type == "standardize":
                        if pd.api.types.is_numeric_dtype(df[column]):
                            mean = df[column].mean()
                            std = df[column].std()
                            if std > 0:
                                df[column] = (df[column] - mean) / std
                                transformations_applied += 1
                                transformation_details.append({
                                    "rule": rule,
                                    "status": "success",
                                    "affected_rows": len(df)
                                })
                        else:
                            transformation_details.append({
                                "rule": rule,
                                "status": "skipped",
                                "reason": f"Column '{column}' is not numeric"
                            })
                    
                    elif rule_type == "one_hot_encode":
                        if not pd.api.types.is_numeric_dtype(df[column]):
                            # Create one-hot encoded columns
                            one_hot = pd.get_dummies(df[column], prefix=column)
                            # Drop the original column
                            df = df.drop(column, axis=1)
                            # Join the one-hot encoded columns
                            df = pd.concat([df, one_hot], axis=1)
                            transformations_applied += 1
                            transformation_details.append({
                                "rule": rule,
                                "status": "success",
                                "affected_rows": len(df),
                                "new_columns": one_hot.columns.tolist()
                            })
                        else:
                            transformation_details.append({
                                "rule": rule,
                                "status": "skipped",
                                "reason": f"Column '{column}' is numeric, not suitable for one-hot encoding"
                            })
                    
                    elif rule_type == "remove_outliers":
                        if pd.api.types.is_numeric_dtype(df[column]):
                            # Calculate IQR
                            Q1 = df[column].quantile(0.25)
                            Q3 = df[column].quantile(0.75)
                            IQR = Q3 - Q1
                            
                            # Define bounds
                            lower_bound = Q1 - 1.5 * IQR
                            upper_bound = Q3 + 1.5 * IQR
                            
                            # Count outliers
                            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
                            outlier_count = len(outliers)
                            
                            # Filter out outliers
                            df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
                            
                            transformations_applied += 1
                            transformation_details.append({
                                "rule": rule,
                                "status": "success",
                                "affected_rows": outlier_count
                            })
                        else:
                            transformation_details.append({
                                "rule": rule,
                                "status": "skipped",
                                "reason": f"Column '{column}' is not numeric"
                            })
                    
                    elif rule_type == "date_features":
                        try:
                            # Convert to datetime if not already
                            if not pd.api.types.is_datetime64_dtype(df[column]):
                                df[column] = pd.to_datetime(df[column])
                            
                            # Extract date features
                            df[f"{column}_year"] = df[column].dt.year
                            df[f"{column}_month"] = df[column].dt.month
                            df[f"{column}_day"] = df[column].dt.day
                            df[f"{column}_dayofweek"] = df[column].dt.dayofweek
                            
                            transformations_applied += 1
                            transformation_details.append({
                                "rule": rule,
                                "status": "success",
                                "affected_rows": len(df),
                                "new_columns": [
                                    f"{column}_year", 
                                    f"{column}_month", 
                                    f"{column}_day", 
                                    f"{column}_dayofweek"
                                ]
                            })
                        except Exception as e:
                            transformation_details.append({
                                "rule": rule,
                                "status": "error",
                                "reason": f"Failed to convert column '{column}' to datetime: {str(e)}"
                            })
                    
                    elif rule_type == "text_length":
                        if not pd.api.types.is_numeric_dtype(df[column]):
                            df[f"{column}_length"] = df[column].astype(str).apply(len)
                            transformations_applied += 1
                            transformation_details.append({
                                "rule": rule,
                                "status": "success",
                                "affected_rows": len(df),
                                "new_columns": [f"{column}_length"]
                            })
                        else:
                            transformation_details.append({
                                "rule": rule,
                                "status": "skipped",
                                "reason": f"Column '{column}' is numeric, not suitable for text length calculation"
                            })
                    
                    elif rule_type == "custom_formula":
                        formula = rule.get("formula")
                        if formula:
                            # Use eval to apply custom formula (with safety checks)
                            # This is a simplified implementation and should be made more secure in production
                            formula = formula.replace("df[column]", "df['" + column + "']")
                            result = eval(formula)
                            new_column = rule.get("new_column", f"{column}_transformed")
                            df[new_column] = result
                            transformations_applied += 1
                            transformation_details.append({
                                "rule": rule,
                                "status": "success",
                                "affected_rows": len(df),
                                "new_columns": [new_column]
                            })
                        else:
                            transformation_details.append({
                                "rule": rule,
                                "status": "skipped",
                                "reason": "No formula provided for custom transformation"
                            })
                    
                    else:
                        transformation_details.append({
                            "rule": rule,
                            "status": "skipped",
                            "reason": f"Unknown transformation type: {rule_type}"
                        })
                
                except Exception as e:
                    logger.error(f"Error applying transformation rule {rule}: {str(e)}")
                    transformation_details.append({
                        "rule": rule,
                        "status": "error",
                        "reason": str(e)
                    })
            
            # Save transformed dataset
            transformed_file_path = file_path.replace(".", "_transformed.")
            
            if file_format.lower() == "csv":
                df.to_csv(transformed_file_path, index=False)
            elif file_format.lower() == "json":
                df.to_json(transformed_file_path, orient="records")
            elif file_format.lower() == "excel" or file_format.lower() == "xlsx":
                df.to_excel(transformed_file_path, index=False)
            
            # Update dataset metadata
            new_metadata = {
                "columns": df.columns.tolist(),
                "column_types": {
                    col: "numeric" if pd.api.types.is_numeric_dtype(df[col]) else
                         "datetime" if pd.api.types.is_datetime64_dtype(df[col]) else "text"
                    for col in df.columns
                },
                "row_count": len(df),
                "file_format": file_format,
                "transformed": True,
                "transformation_details": transformation_details
            }
            
            # Store transformation results in database
            async with self.pool.acquire() as conn:
                # Update dataset record
                await conn.execute(
                    """
                    UPDATE datasets
                    SET row_count = $1, column_count = $2, transformed_file_path = $3
                    WHERE id = $4
                    """,
                    len(df),
                    len(df.columns),
                    transformed_file_path,
                    dataset_id
                )
                
                # Update metadata
                await conn.execute(
                    """
                    UPDATE dataset_metadata
                    SET metadata = $1
                    WHERE dataset_id = $2
                    """,
                    json.dumps(new_metadata),
                    dataset_id
                )
                
                # Store transformation rules if they were provided
                if transformation_rules:
                    await conn.execute(
                        """
                        INSERT INTO transformation_rules (dataset_id, rules)
                        VALUES ($1, $2)
                        ON CONFLICT (dataset_id) DO UPDATE
                        SET rules = $2
                        """,
                        dataset_id,
                        json.dumps(transformation_rules)
                    )
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "transformations_applied": transformations_applied,
                "transformation_details": transformation_details,
                "new_row_count": len(df),
                "new_column_count": len(df.columns),
                "transformed_file_path": transformed_file_path
            }
            
        except Exception as e:
            logger.error(f"Error transforming dataset: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to transform dataset: {str(e)}"
            }
    
    async def get_transformation_suggestions(self, dataset_id: int) -> Dict[str, Any]:
        """
        Generate transformation suggestions for a dataset
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary with transformation suggestions
        """
        await self.initialize()
        
        try:
            # Get dataset information and profile
            async with self.pool.acquire() as conn:
                # Get dataset metadata
                metadata_row = await conn.fetchrow(
                    """
                    SELECT metadata
                    FROM dataset_metadata
                    WHERE dataset_id = $1
                    """,
                    dataset_id
                )
                
                if not metadata_row:
                    return {
                        "success": False,
                        "error": f"Metadata for dataset with ID {dataset_id} not found"
                    }
                
                metadata = json.loads(metadata_row["metadata"])
                
                # Get dataset profile
                profile_row = await conn.fetchrow(
                    """
                    SELECT profile
                    FROM dataset_profiles
                    WHERE dataset_id = $1
                    """,
                    dataset_id
                )
                
                if not profile_row:
                    return {
                        "success": False,
                        "error": f"Profile for dataset with ID {dataset_id} not found"
                    }
                
                profile = json.loads(profile_row["profile"])
            
            # Generate transformation suggestions based on profile
            suggestions = []
            
            # Missing values handling
            missing_values = profile.get("missing_values", {})
            for column, missing_count in missing_values.items():
                if missing_count > 0:
                    column_type = metadata.get("column_types", {}).get(column)
                    
                    if column_type == "numeric":
                        # For numeric columns, suggest filling with mean or median
                        suggestions.append({
                            "type": "fill_missing",
                            "column": column,
                            "value": profile.get("column_stats", {}).get(column, {}).get("mean", 0),
                            "description": f"Fill missing values in '{column}' with mean"
                        })
                    else:
                        # For non-numeric columns, suggest filling with most common value
                        suggestions.append({
                            "type": "fill_missing",
                            "column": column,
                            "value": profile.get("column_stats", {}).get(column, {}).get("most_common", ""),
                            "description": f"Fill missing values in '{column}' with most common value"
                        })
            
            # Normalization for numeric columns
            for column, column_type in metadata.get("column_types", {}).items():
                if column_type == "numeric":
                    # Suggest normalization for numeric columns
                    suggestions.append({
                        "type": "normalize",
                        "column": column,
                        "description": f"Normalize '{column}' to range [0, 1]"
                    })
            
            # One-hot encoding for categorical columns with few unique values
            for column, stats in profile.get("column_stats", {}).items():
                if metadata.get("column_types", {}).get(column) != "numeric":
                    unique_count = stats.get("unique_count", 0)
                    if 2 <= unique_count <= 10:  # Only suggest for columns with reasonable number of categories
                        suggestions.append({
                            "type": "one_hot_encode",
                            "column": column,
                            "description": f"One-hot encode '{column}' with {unique_count} unique values"
                        })
            
            # Date feature extraction for datetime columns
            for column, column_type in metadata.get("column_types", {}).items():
                if column_type == "datetime":
                    suggestions.append({
                        "type": "date_features",
                        "column": column,
                        "description": f"Extract year, month, day, and day of week from '{column}'"
                    })
            
            # Text length for text columns
            for column, column_type in metadata.get("column_types", {}).items():
                if column_type == "text":
                    suggestions.append({
                        "type": "text_length",
                        "column": column,
                        "description": f"Calculate text length for '{column}'"
                    })
            
            # Outlier removal for numeric columns with outliers
            outlier_columns = profile.get("outlier_columns", [])
            for column in outlier_columns:
                if metadata.get("column_types", {}).get(column) == "numeric":
                    suggestions.append({
                        "type": "remove_outliers",
                        "column": column,
                        "description": f"Remove outliers from '{column}' using IQR method"
                    })
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error generating transformation suggestions: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate transformation suggestions: {str(e)}"
            }
