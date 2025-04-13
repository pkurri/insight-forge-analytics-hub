
"""
AI-powered Schema Detection Service

This service uses AI techniques to automatically detect and infer
schema information from data, including data types, constraints, 
and relationships between fields.
"""
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel
from datetime import datetime
import re
from functools import lru_cache

# Import the cache service for performance optimization
from api.services.cache_service import get_cached_response, cache_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AISchemaDetector:
    """
    AI-powered schema detection for dynamic data processing.
    
    This class leverages machine learning and heuristic techniques to:
    1. Automatically infer data types from sample data
    2. Detect patterns and constraints in data
    3. Identify relationships between columns
    4. Generate validation rules based on data patterns
    """
    
    def __init__(self):
        """Initialize the AI schema detector with default settings"""
        logger.info("Initializing AI Schema Detector")
        
        # Confidence thresholds for different detection algorithms
        self.confidence_thresholds = {
            "data_type": 0.85,
            "constraint": 0.75,
            "relationship": 0.80,
            "validation_rule": 0.70
        }
    
    @lru_cache(maxsize=100)
    async def detect_schema(self, dataset_id: str, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Detect schema from dataset using AI techniques
        
        Args:
            dataset_id: Identifier for the dataset
            sample_size: Maximum number of rows to sample
            
        Returns:
            Dictionary containing detected schema with confidence scores
        """
        # Check cache first for performance
        cache_key = f"schema_detection:{dataset_id}"
        cached_result = get_cached_response(cache_key)
        if cached_result:
            logger.info(f"Using cached schema detection for dataset {dataset_id}")
            return cached_result
        
        try:
            # In a real implementation, this would load data from storage
            # For now, we'll simulate loading from a file or database
            data = await self._load_dataset(dataset_id, sample_size)
            
            # Convert to pandas DataFrame for analysis
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = data
            
            # Detect schema using multiple techniques
            column_schemas = {}
            relationships = []
            
            # Process each column
            for column in df.columns:
                column_schema = await self._analyze_column(df[column])
                column_schemas[column] = column_schema
            
            # Detect relationships between columns
            relationships = await self._detect_relationships(df)
            
            # Build final schema
            schema = {
                "dataset_id": dataset_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "columns": column_schemas,
                "relationships": relationships,
                "row_count": len(df),
                "meta": {
                    "ai_confidence": self._calculate_overall_confidence(column_schemas),
                    "suggested_indices": await self._suggest_indices(df, column_schemas),
                    "data_quality_score": await self._calculate_data_quality(df, column_schemas)
                }
            }
            
            # Cache for future use (30 minutes)
            cache_response(cache_key, schema, 1800)
            
            return schema
            
        except Exception as e:
            logger.error(f"Error detecting schema for dataset {dataset_id}: {str(e)}")
            raise
    
    async def _load_dataset(self, dataset_id: str, sample_size: int = 1000) -> pd.DataFrame:
        """Load dataset from storage (mock implementation)"""
        # In production, this would connect to your actual data storage
        try:
            # This is a mock implementation
            # In production, you would retrieve data from database/file storage
            
            # Mock datasets
            if dataset_id == "ds001":
                # Employee dataset
                data = {
                    "name": ["John Smith", "Jane Doe", "Bob Johnson", None, "Alice Brown"],
                    "age": [32, 28, 45, 39, 52],
                    "salary": [75000, 82000, 95000, 62000, 110000],
                    "department": ["Engineering", "Marketing", "Engineering", "Sales", "Executive"]
                }
            elif dataset_id == "ds002":
                # Product dataset
                data = {
                    "product_id": ["P001", "P002", "P003", "P004", "P005"],
                    "price": [29.99, 49.99, 9.99, 15.50, 99.99],
                    "quantity": [100, 50, 200, 75, 25],
                    "date": ["2023-01-15", "2023-02-01", "invalid-date", "2023-01-30", "2023-02-15"]
                }
            elif dataset_id == "ds003":
                # Customer orders dataset
                data = {
                    "customer_id": ["C001", "C002", "C003", "C001", "C004"],
                    "order_date": ["2023-01-10", "2023-01-15", "2023-01-20", "2023-02-05", "2023-02-10"],
                    "total_value": [125.50, 89.99, 45.25, 210.75, 150.00],
                    "items": [3, 2, 1, 5, 4]
                }
            else:
                # Generate random data if dataset doesn't exist
                import random
                data = {
                    "id": [f"ID{i}" for i in range(sample_size)],
                    "value_a": np.random.normal(50, 15, sample_size),
                    "value_b": np.random.uniform(0, 100, sample_size),
                    "category": np.random.choice(["A", "B", "C"], sample_size),
                    "date": [datetime.now().date() - pd.Timedelta(days=i) for i in range(sample_size)]
                }
            
            df = pd.DataFrame(data)
            return df.head(sample_size)
            
        except Exception as e:
            logger.error(f"Error loading dataset {dataset_id}: {str(e)}")
            raise
    
    async def _analyze_column(self, series: pd.Series) -> Dict[str, Any]:
        """
        Analyze a single column using AI techniques to determine its schema
        
        Uses:
        - Statistical analysis for data type inference
        - Pattern recognition for format detection
        - Outlier detection for constraint suggestion
        """
        # Calculate basic statistics
        non_null_values = series.dropna()
        total_values = len(series)
        non_null_count = len(non_null_values)
        null_count = total_values - non_null_count
        null_percentage = (null_count / total_values * 100) if total_values > 0 else 0
        
        # Detect sample values
        sample_values = non_null_values.sample(min(5, non_null_count)).tolist() if non_null_count > 0 else []
        
        # Initialize schema with basic information
        column_schema = {
            "nullable": null_count > 0,
            "null_count": null_count,
            "null_percentage": null_percentage,
            "unique_count": non_null_values.nunique(),
            "sample_values": sample_values,
        }
        
        # Infer data type with confidence score
        data_type_info = await self._infer_data_type(non_null_values)
        column_schema.update(data_type_info)
        
        # Detect constraints based on data
        constraints = await self._detect_constraints(non_null_values, data_type_info["data_type"])
        column_schema["constraints"] = constraints
        
        # Generate validation rules
        rules = await self._generate_validation_rules(series, data_type_info["data_type"], constraints)
        column_schema["validation_rules"] = rules
        
        return column_schema
    
    async def _infer_data_type(self, series: pd.Series) -> Dict[str, Any]:
        """
        Use AI techniques to infer the most likely data type for a series
        
        Returns:
            Dict with data_type and confidence score
        """
        if len(series) == 0:
            return {"data_type": "string", "data_type_confidence": 1.0}
        
        # Convert series to string for consistent type checking
        series_str = series.astype(str)
        
        # Check if all values can be parsed as integers
        try:
            int_series = pd.to_numeric(series)
            if (int_series == int_series.astype(int)).all():
                return {"data_type": "integer", "data_type_confidence": 0.95}
        except:
            pass
        
        # Check if all values can be parsed as floats
        try:
            float_series = pd.to_numeric(series)
            return {"data_type": "number", "data_type_confidence": 0.9}
        except:
            pass
        
        # Check for boolean values
        bool_values = {'true', 'false', 't', 'f', 'yes', 'no', 'y', 'n', '1', '0'}
        if all(str(v).lower() in bool_values for v in series_str):
            return {"data_type": "boolean", "data_type_confidence": 0.9}
        
        # Check for date values
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
        ]
        
        date_matches = 0
        for pattern in date_patterns:
            date_matches += sum(series_str.str.match(pattern).fillna(False))
        
        date_confidence = date_matches / len(series)
        if date_confidence > 0.8:
            return {"data_type": "date", "data_type_confidence": date_confidence}
        
        # Check for structured formats like email, phone, etc.
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email_matches = sum(series_str.str.match(email_pattern).fillna(False))
        if email_matches / len(series) > 0.8:
            return {
                "data_type": "string", 
                "data_type_confidence": 0.9,
                "format": "email",
                "format_confidence": email_matches / len(series)
            }
        
        # Check for IDs or codes (alphanumeric with patterns)
        id_pattern = r'^[A-Z0-9]{3,10}$'
        id_matches = sum(series_str.str.match(id_pattern).fillna(False))
        if id_matches / len(series) > 0.8:
            return {
                "data_type": "string", 
                "data_type_confidence": 0.85,
                "format": "id",
                "format_confidence": id_matches / len(series)
            }
        
        # Check if categorical (few unique values)
        unique_ratio = series.nunique() / len(series)
        if unique_ratio < 0.1:  # Less than 10% unique values
            return {
                "data_type": "string", 
                "data_type_confidence": 0.8,
                "format": "categorical",
                "format_confidence": 1.0 - unique_ratio  # Higher confidence if fewer unique values
            }
            
        # Default to string
        return {"data_type": "string", "data_type_confidence": 0.7}
    
    async def _detect_constraints(self, series: pd.Series, data_type: str) -> Dict[str, Any]:
        """
        Detect constraints for a column based on its data
        """
        constraints = {}
        
        # Skip if empty
        if len(series) == 0:
            return constraints
            
        # Calculate unique values
        unique_values = series.nunique()
        total_values = len(series)
        
        # Check if values should be unique (like IDs)
        if unique_values == total_values and total_values > 5:
            constraints["unique"] = True
            constraints["unique_confidence"] = 0.9
        
        if data_type in ["integer", "number"]:
            # Get min/max values
            constraints["min"] = float(series.min())
            constraints["max"] = float(series.max())
            
            # Check if values are within common ranges
            if constraints["min"] >= 0 and constraints["max"] <= 100:
                constraints["range_type"] = "percentage"
            elif constraints["min"] >= 0 and constraints["max"] <= 1:
                constraints["range_type"] = "probability"
                
        elif data_type == "string":
            # Calculate string length stats
            str_lengths = series.astype(str).str.len()
            constraints["min_length"] = int(str_lengths.min())
            constraints["max_length"] = int(str_lengths.max())
            
            # Check for repeating patterns
            sample = series.sample(min(100, len(series)))
            patterns = []
            
            # Check common patterns
            pattern_checks = [
                (r'^[A-Z0-9]{8}$', 'ID_8CHAR'),
                (r'^[0-9]{5}(-[0-9]{4})?$', 'ZIP_CODE'),
                (r'^[A-Z]{2}[0-9]{2}[A-Z]?$', 'COUNTRY_CODE')
            ]
            
            for pattern, name in pattern_checks:
                matches = sample.astype(str).str.match(pattern).mean()
                if matches > 0.8:
                    patterns.append({
                        "pattern": pattern,
                        "name": name,
                        "confidence": matches
                    })
            
            if patterns:
                constraints["patterns"] = patterns
        
        return constraints
    
    async def _detect_relationships(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect potential relationships between columns
        
        Uses correlation analysis, pattern matching, and name similarity
        to identify foreign keys and relationships.
        """
        relationships = []
        
        # Skip for small dataframes
        if df.shape[1] < 2:
            return relationships
            
        # Look for potential foreign key relationships
        columns = list(df.columns)
        
        for i, col1 in enumerate(columns):
            # Skip if column doesn't look like an ID
            if not any(x in col1.lower() for x in ['id', 'key', 'code']):
                continue
                
            # Look for matching columns in names
            base_name = col1.replace('_id', '').replace('id_', '').replace('_key', '')
            
            for j, col2 in enumerate(columns):
                if i == j:
                    continue
                    
                # Check if second column contains base name
                if base_name.lower() in col2.lower():
                    relationships.append({
                        "type": "foreign_key",
                        "columns": [col1, col2],
                        "confidence": 0.8,
                        "description": f"Potential foreign key relationship between {col1} and {col2}"
                    })
        
        # Check for numerical correlations
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.shape[1] >= 2:
            try:
                corr_matrix = numeric_df.corr()
                
                # Find highly correlated columns
                for i in range(corr_matrix.shape[0]):
                    for j in range(i+1, corr_matrix.shape[1]):
                        if abs(corr_matrix.iloc[i, j]) > 0.8:
                            relationships.append({
                                "type": "correlation",
                                "columns": [corr_matrix.index[i], corr_matrix.columns[j]],
                                "correlation": float(corr_matrix.iloc[i, j]),
                                "confidence": abs(float(corr_matrix.iloc[i, j])),
                                "description": f"Strong correlation between {corr_matrix.index[i]} and {corr_matrix.columns[j]}"
                            })
            except Exception as e:
                logger.warning(f"Error calculating correlations: {str(e)}")
        
        return relationships
    
    async def _calculate_data_quality(self, df: pd.DataFrame, column_schemas: Dict[str, Any]) -> float:
        """
        Calculate overall data quality score using AI-based heuristics
        
        Factors:
        - Null values percentage
        - Outliers percentage
        - Schema conformance
        - Data consistency
        """
        # Initialize quality scores
        quality_factors = {
            "completeness": 0,
            "validity": 0,
            "consistency": 0,
            "uniqueness": 0
        }
        
        # Calculate completeness (inverse of null percentage)
        null_percentages = []
        for col, schema in column_schemas.items():
            null_percentages.append(schema.get("null_percentage", 0))
        
        avg_null_percentage = sum(null_percentages) / len(null_percentages) if null_percentages else 0
        quality_factors["completeness"] = max(0, 100 - avg_null_percentage) / 100
        
        # Calculate validity based on data type confidence
        validity_scores = []
        for col, schema in column_schemas.items():
            confidence = schema.get("data_type_confidence", 0.5)
            validity_scores.append(confidence)
        
        quality_factors["validity"] = sum(validity_scores) / len(validity_scores) if validity_scores else 0.5
        
        # Calculate consistency (based on outliers)
        consistency_scores = []
        for col in df.columns:
            if df[col].dtype.kind in 'ifc':  # integer, float, complex
                try:
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).mean()
                    consistency_scores.append(1 - outliers)
                except:
                    consistency_scores.append(0.5)  # Default if calculation fails
        
        quality_factors["consistency"] = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
        
        # Calculate uniqueness where appropriate
        uniqueness_scores = []
        for col, schema in column_schemas.items():
            if schema.get("constraints", {}).get("unique", False):
                unique_ratio = df[col].nunique() / len(df)
                uniqueness_scores.append(unique_ratio)
        
        quality_factors["uniqueness"] = sum(uniqueness_scores) / len(uniqueness_scores) if uniqueness_scores else 0.5
        
        # Weighted average of factors
        weights = {
            "completeness": 0.4,
            "validity": 0.3,
            "consistency": 0.2,
            "uniqueness": 0.1
        }
        
        weighted_score = sum(score * weights[factor] for factor, score in quality_factors.items())
        return round(weighted_score * 100) / 100  # Round to 2 decimal places
    
    async def _generate_validation_rules(self, series: pd.Series, data_type: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use AI to generate validation rules based on detected patterns
        """
        rules = []
        
        # Skip if empty
        if len(series) == 0:
            return rules
            
        # Generate rules based on data type
        if data_type == "integer":
            # Integer range checks
            min_val = constraints.get("min")
            max_val = constraints.get("max")
            
            if min_val is not None and max_val is not None:
                rules.append({
                    "type": "range",
                    "min": min_val,
                    "max": max_val,
                    "message": f"Value should be between {min_val} and {max_val}",
                    "confidence": 0.9
                })
                
            # Check if values should be positive
            if min_val is not None and min_val >= 0:
                rules.append({
                    "type": "non_negative",
                    "message": "Value should be non-negative",
                    "confidence": 0.95
                })
                
        elif data_type == "number":
            # Floating point range checks
            min_val = constraints.get("min")
            max_val = constraints.get("max")
            
            if min_val is not None and max_val is not None:
                rules.append({
                    "type": "range",
                    "min": min_val,
                    "max": max_val,
                    "message": f"Value should be between {min_val} and {max_val}",
                    "confidence": 0.9
                })
                
        elif data_type == "string":
            # String length checks
            min_length = constraints.get("min_length")
            max_length = constraints.get("max_length")
            
            if min_length is not None and max_length is not None:
                rules.append({
                    "type": "length",
                    "min": min_length,
                    "max": max_length,
                    "message": f"String length should be between {min_length} and {max_length}",
                    "confidence": 0.9
                })
                
            # Check for patterns
            patterns = constraints.get("patterns", [])
            for pattern_info in patterns:
                rules.append({
                    "type": "pattern",
                    "pattern": pattern_info["pattern"],
                    "message": f"Value should match pattern: {pattern_info['name']}",
                    "confidence": pattern_info["confidence"]
                })
                
            # Check format-specific rules
            format_type = constraints.get("format")
            if format_type == "email":
                rules.append({
                    "type": "email",
                    "message": "Value should be a valid email address",
                    "confidence": 0.95
                })
            elif format_type == "id":
                rules.append({
                    "type": "id_format",
                    "message": "Value should be a valid ID format",
                    "confidence": 0.9
                })
                
        # Add uniqueness rule if needed
        if constraints.get("unique", False):
            rules.append({
                "type": "unique",
                "message": "Value should be unique",
                "confidence": constraints.get("unique_confidence", 0.9)
            })
            
        return rules
    
    async def _suggest_indices(self, df: pd.DataFrame, column_schemas: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest database indices based on column characteristics
        """
        suggested_indices = []
        
        # Check each column for index potential
        for col, schema in column_schemas.items():
            # ID columns should be indexed
            if '_id' in col.lower() or col.lower() == 'id':
                suggested_indices.append({
                    "column": col,
                    "type": "btree",
                    "priority": "high",
                    "reason": "ID column for fast lookups"
                })
                continue
                
            # Foreign key like columns
            if schema.get("constraints", {}).get("unique", False):
                suggested_indices.append({
                    "column": col,
                    "type": "btree", 
                    "priority": "medium",
                    "reason": "Unique column for fast lookups"
                })
                
            # Date columns often used for filtering
            if schema.get("data_type") == "date":
                suggested_indices.append({
                    "column": col,
                    "type": "btree",
                    "priority": "medium", 
                    "reason": "Date column likely used for filtering and sorting"
                })
                
            # Text columns that might benefit from full-text search
            if (schema.get("data_type") == "string" and
                schema.get("constraints", {}).get("max_length", 0) > 100):
                suggested_indices.append({
                    "column": col,
                    "type": "gin",
                    "priority": "low",
                    "reason": "Text column that may benefit from full-text search"
                })
                
        return suggested_indices
    
    def _calculate_overall_confidence(self, column_schemas: Dict[str, Any]) -> float:
        """Calculate overall confidence in the schema detection"""
        confidences = []
        
        for col, schema in column_schemas.items():
            conf = schema.get("data_type_confidence", 0.5)
            confidences.append(conf)
            
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        return avg_confidence

# Initialize the AI schema detector service
ai_schema_detector = AISchemaDetector()

# API function to detect schema
async def detect_schema(dataset_id: str, sample_size: int = 1000) -> Dict[str, Any]:
    """
    Detect schema from dataset using AI techniques
    
    Args:
        dataset_id: Identifier for the dataset
        sample_size: Maximum number of rows to sample
        
    Returns:
        Dictionary containing detected schema
    """
    return await ai_schema_detector.detect_schema(dataset_id, sample_size)

# API function to validate data against detected schema
async def validate_with_ai_schema(dataset_id: str, data: Any) -> Dict[str, Any]:
    """
    Validate data against AI-detected schema
    
    Args:
        dataset_id: Identifier for the dataset
        data: Data to validate
        
    Returns:
        Dictionary containing validation results
    """
    # Get schema
    schema = await ai_schema_detector.detect_schema(dataset_id)
    
    # Convert input to DataFrame
    if isinstance(data, pd.DataFrame):
        df = data
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        raise ValueError("Input data must be a DataFrame or list of records")
    
    # Validate against schema
    results = {
        "valid": True,
        "errors": [],
        "stats": {
            "total_rows": len(df),
            "valid_rows": 0,
            "invalid_rows": 0
        }
    }
    
    # Track invalid rows
    invalid_rows = []
    
    # Validate each row
    for idx, row in df.iterrows():
        row_errors = []
        
        # Check each field
        for col, value in row.items():
            if col not in schema["columns"]:
                continue
                
            col_schema = schema["columns"][col]
            
            # Check nullability
            if pd.isna(value) and not col_schema.get("nullable", True):
                row_errors.append({
                    "column": col,
                    "error": "Value cannot be null",
                    "value": None
                })
                continue
                
            if pd.isna(value):
                continue
                
            # Check data type
            data_type = col_schema.get("data_type")
            if data_type == "integer":
                try:
                    int(value)
                except (ValueError, TypeError):
                    row_errors.append({
                        "column": col,
                        "error": "Value must be an integer",
                        "value": str(value)
                    })
            
            elif data_type == "number":
                try:
                    float(value)
                except (ValueError, TypeError):
                    row_errors.append({
                        "column": col,
                        "error": "Value must be a number",
                        "value": str(value)
                    })
            
            # Apply validation rules
            for rule in col_schema.get("validation_rules", []):
                rule_type = rule.get("type")
                
                if rule_type == "range":
                    try:
                        val = float(value)
                        min_val = rule.get("min")
                        max_val = rule.get("max")
                        
                        if (min_val is not None and val < min_val) or (max_val is not None and val > max_val):
                            row_errors.append({
                                "column": col,
                                "error": rule.get("message", "Value outside allowed range"),
                                "value": str(value)
                            })
                    except:
                        pass
                
                elif rule_type == "length":
                    try:
                        val_str = str(value)
                        min_len = rule.get("min")
                        max_len = rule.get("max")
                        
                        if (min_len is not None and len(val_str) < min_len) or (max_len is not None and len(val_str) > max_len):
                            row_errors.append({
                                "column": col,
                                "error": rule.get("message", "String length outside allowed range"),
                                "value": val_str
                            })
                    except:
                        pass
                
                elif rule_type == "pattern":
                    try:
                        val_str = str(value)
                        pattern = rule.get("pattern")
                        
                        if not re.match(pattern, val_str):
                            row_errors.append({
                                "column": col,
                                "error": rule.get("message", "Value doesn't match required pattern"),
                                "value": val_str
                            })
                    except:
                        pass
                        
                elif rule_type == "email":
                    try:
                        val_str = str(value)
                        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                        
                        if not re.match(email_pattern, val_str):
                            row_errors.append({
                                "column": col,
                                "error": rule.get("message", "Invalid email format"),
                                "value": val_str
                            })
                    except:
                        pass
        
        # Add row to results if errors found
        if row_errors:
            invalid_rows.append({
                "row_index": idx,
                "errors": row_errors
            })
    
    # Update stats
    results["stats"]["invalid_rows"] = len(invalid_rows)
    results["stats"]["valid_rows"] = results["stats"]["total_rows"] - results["stats"]["invalid_rows"]
    results["valid"] = results["stats"]["invalid_rows"] == 0
    
    # Add errors (limit to first 100 for performance)
    results["errors"] = invalid_rows[:100]
    
    return results
