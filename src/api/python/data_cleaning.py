
"""
Data Cleaning and Validation Agent Module

This module provides agents for automatic data cleaning and validation
using machine learning techniques to identify and resolve data quality issues.

In a production environment, this would be deployed as an API endpoint or microservice.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Union, Optional, Tuple
import logging
import re
from datetime import datetime, timedelta
import json
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.cluster import DBSCAN
import string

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCleaningAgent:
    """Class for automatic data cleaning using ML techniques"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data cleaning agent
        
        Args:
            config: Configuration dictionary for the cleaning agent
        """
        self.config = config or {
            "missing_values": {
                "strategy": "auto",  # auto, mean, median, mode, knn, none
                "knn_neighbors": 5
            },
            "outliers": {
                "strategy": "auto",  # auto, clip, remove, none
                "threshold": 3.0  # Z-score threshold
            },
            "inconsistent_values": {
                "strategy": "auto",  # auto, standardize, none
                "case_sensitive": False
            },
            "duplicate_rows": {
                "strategy": "remove"  # remove, keep, none
            },
            "column_types": {},  # Manual column type overrides
            "column_transforms": {}  # Manual column transformations
        }
        logger.info("DataCleaningAgent initialized with config")
    
    def clean_dataset(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Automatically clean a dataset
        
        Args:
            data: Pandas DataFrame to clean
            
        Returns:
            Dictionary with cleaning results and cleaned data
        """
        try:
            # Keep a copy of the original data for comparison
            original_data = data.copy()
            cleaned_data = data.copy()
            
            # Track cleaning operations
            operations = []
            
            # 1. Handle duplicate rows
            if self.config["duplicate_rows"]["strategy"] != "none":
                num_duplicates = cleaned_data.duplicated().sum()
                if num_duplicates > 0:
                    cleaned_data = cleaned_data.drop_duplicates()
                    operations.append({
                        "operation": "remove_duplicates",
                        "rows_affected": int(num_duplicates)
                    })
            
            # 2. Infer column types if not provided
            column_types = self._infer_column_types(cleaned_data)
            
            # Apply manual overrides
            for col, col_type in self.config["column_types"].items():
                if col in column_types:
                    column_types[col] = col_type
            
            # 3. Handle missing values
            if self.config["missing_values"]["strategy"] != "none":
                missing_ops = self._handle_missing_values(cleaned_data, column_types)
                operations.extend(missing_ops)
            
            # 4. Handle outliers
            if self.config["outliers"]["strategy"] != "none":
                outlier_ops = self._handle_outliers(cleaned_data, column_types)
                operations.extend(outlier_ops)
            
            # 5. Handle inconsistent values
            if self.config["inconsistent_values"]["strategy"] != "none":
                inconsistent_ops = self._handle_inconsistent_values(cleaned_data, column_types)
                operations.extend(inconsistent_ops)
            
            # 6. Apply manual column transformations
            for col, transform in self.config["column_transforms"].items():
                if col in cleaned_data.columns:
                    if callable(transform):
                        cleaned_data[col] = cleaned_data[col].apply(transform)
                    operations.append({
                        "operation": "custom_transform",
                        "column": col
                    })
            
            # Calculate cleaning summary
            total_cells_original = original_data.size
            total_cells_cleaned = cleaned_data.size
            rows_removed = len(original_data) - len(cleaned_data)
            
            # Calculate percentage of changed cells
            changed_cells = 0
            for col in cleaned_data.columns:
                if col in original_data.columns:
                    try:
                        # For numeric columns
                        if pd.api.types.is_numeric_dtype(cleaned_data[col]):
                            changed_mask = ~original_data[col].equals(cleaned_data[col])
                            changed_cells += changed_mask.sum()
                        else:
                            # For non-numeric columns
                            changed_mask = original_data[col] != cleaned_data[col]
                            changed_cells += changed_mask.sum()
                    except:
                        # If comparison fails, assume all cells changed
                        changed_cells += len(cleaned_data[col])
            
            cells_changed_percent = (changed_cells / total_cells_original * 100) if total_cells_original > 0 else 0
            
            return {
                "success": True,
                "cleaned_data": cleaned_data,
                "summary": {
                    "rows_before": len(original_data),
                    "rows_after": len(cleaned_data),
                    "rows_removed": rows_removed,
                    "cells_changed": int(changed_cells),
                    "cells_changed_percent": float(cells_changed_percent),
                    "operations": operations,
                    "column_types": column_types
                }
            }
            
        except Exception as e:
            logger.error(f"Error cleaning dataset: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _infer_column_types(self, data: pd.DataFrame) -> Dict[str, str]:
        """Infer column types from data"""
        column_types = {}
        
        for col in data.columns:
            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(data[col]):
                # Check if values are mostly integers
                if pd.api.types.is_integer_dtype(data[col]) or (data[col].dropna().apply(float.is_integer).mean() > 0.8):
                    column_types[col] = "integer"
                else:
                    column_types[col] = "float"
                    
            # Check if column is datetime
            elif pd.api.types.is_datetime64_dtype(data[col]):
                column_types[col] = "datetime"
                
            # Check if boolean
            elif pd.api.types.is_bool_dtype(data[col]):
                column_types[col] = "boolean"
                
            # Check if categorical
            elif len(data[col].unique()) / len(data[col]) < 0.1 and len(data[col].unique()) < 50:
                column_types[col] = "categorical"
                
            # Check if likely an email
            elif data[col].dropna().astype(str).str.contains('@.*\.').mean() > 0.5:
                column_types[col] = "email"
                
            # Check if likely a phone number
            elif data[col].dropna().astype(str).str.replace(r'[^0-9]', '').str.len().mean() > 7:
                if data[col].dropna().astype(str).str.match(r'^\+?[\d\s\-\(\)]+$').mean() > 0.8:
                    column_types[col] = "phone"
                    
            # Check if likely a URL
            elif data[col].dropna().astype(str).str.contains('http|www\..*\.').mean() > 0.5:
                column_types[col] = "url"
                
            # Default to text
            else:
                column_types[col] = "text"
                
        return column_types
    
    def _handle_missing_values(self, data: pd.DataFrame, column_types: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Handle missing values in the dataset
        
        Args:
            data: DataFrame to process (modified in place)
            column_types: Dictionary of column types
            
        Returns:
            List of operations performed
        """
        operations = []
        
        for col in data.columns:
            missing_count = data[col].isna().sum()
            if missing_count == 0:
                continue
            
            col_type = column_types.get(col, "text")
            strategy = self.config["missing_values"]["strategy"]
            
            # If strategy is auto, choose based on column type
            if strategy == "auto":
                if col_type in ["integer", "float"]:
                    if missing_count / len(data) < 0.3:
                        strategy = "median"
                    else:
                        strategy = "knn"
                elif col_type in ["categorical", "boolean"]:
                    strategy = "mode"
                else:
                    strategy = "none"
            
            # Apply the appropriate strategy
            if strategy == "mean" and col_type in ["integer", "float"]:
                data[col] = data[col].fillna(data[col].mean())
                operations.append({
                    "operation": "fill_missing",
                    "column": col,
                    "strategy": "mean",
                    "count": int(missing_count)
                })
                
            elif strategy == "median" and col_type in ["integer", "float"]:
                data[col] = data[col].fillna(data[col].median())
                operations.append({
                    "operation": "fill_missing",
                    "column": col,
                    "strategy": "median",
                    "count": int(missing_count)
                })
                
            elif strategy == "mode":
                # For any column type, use most frequent value
                mode_value = data[col].mode()[0]
                data[col] = data[col].fillna(mode_value)
                operations.append({
                    "operation": "fill_missing",
                    "column": col,
                    "strategy": "mode",
                    "count": int(missing_count)
                })
                
            elif strategy == "knn" and col_type in ["integer", "float"]:
                # Use KNN imputation for numeric columns
                try:
                    numeric_cols = [c for c in data.columns if column_types.get(c) in ["integer", "float"]]
                    if len(numeric_cols) > 1:  # Need at least one other numeric column
                        subset = data[numeric_cols].copy()
                        
                        # Create a mask of missing values to restore after imputation
                        missing_mask = subset.isna()
                        
                        # Temporarily fill other missing values with column means
                        for num_col in numeric_cols:
                            subset[num_col] = subset[num_col].fillna(subset[num_col].mean())
                        
                        # Apply KNN imputation
                        imputer = KNNImputer(n_neighbors=self.config["missing_values"]["knn_neighbors"])
                        imputed_data = imputer.fit_transform(subset)
                        imputed_df = pd.DataFrame(imputed_data, columns=numeric_cols)
                        
                        # Replace only the missing values in the original data
                        data.loc[:, col] = data[col].fillna(imputed_df[col])
                        operations.append({
                            "operation": "fill_missing",
                            "column": col,
                            "strategy": "knn",
                            "count": int(missing_count)
                        })
                    else:
                        # Fallback to median if not enough numeric columns
                        data[col] = data[col].fillna(data[col].median())
                        operations.append({
                            "operation": "fill_missing",
                            "column": col,
                            "strategy": "median (fallback)",
                            "count": int(missing_count)
                        })
                except Exception as e:
                    logger.warning(f"KNN imputation failed for {col}: {e}. Using median instead.")
                    data[col] = data[col].fillna(data[col].median())
                    operations.append({
                        "operation": "fill_missing",
                        "column": col,
                        "strategy": "median (fallback)",
                        "count": int(missing_count)
                    })
        
        return operations
    
    def _handle_outliers(self, data: pd.DataFrame, column_types: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Handle outliers in the dataset
        
        Args:
            data: DataFrame to process (modified in place)
            column_types: Dictionary of column types
            
        Returns:
            List of operations performed
        """
        operations = []
        
        # Only process numeric columns
        numeric_cols = [col for col in data.columns if column_types.get(col) in ["integer", "float"]]
        
        for col in numeric_cols:
            # Skip columns with too few values
            if len(data[col].dropna()) < 10:
                continue
            
            strategy = self.config["outliers"]["strategy"]
            
            # If strategy is auto, use Z-score clipping
            if strategy == "auto":
                strategy = "clip"
            
            # Apply the strategy
            if strategy == "clip":
                # Use Z-score method to identify outliers
                z_scores = (data[col] - data[col].mean()) / data[col].std()
                threshold = self.config["outliers"]["threshold"]
                outliers = (z_scores.abs() > threshold)
                outlier_count = outliers.sum()
                
                if outlier_count > 0:
                    # Clip to the threshold values
                    mean_val = data[col].mean()
                    std_val = data[col].std()
                    lower_bound = mean_val - threshold * std_val
                    upper_bound = mean_val + threshold * std_val
                    
                    data.loc[data[col] < lower_bound, col] = lower_bound
                    data.loc[data[col] > upper_bound, col] = upper_bound
                    
                    operations.append({
                        "operation": "clip_outliers",
                        "column": col,
                        "count": int(outlier_count),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound)
                    })
                    
            elif strategy == "remove":
                # Use Z-score method to identify outliers
                z_scores = (data[col] - data[col].mean()) / data[col].std()
                threshold = self.config["outliers"]["threshold"]
                outliers = (z_scores.abs() > threshold)
                outlier_count = outliers.sum()
                
                if outlier_count > 0:
                    # Remove rows with outliers
                    data.drop(data[outliers].index, inplace=True)
                    
                    operations.append({
                        "operation": "remove_outliers",
                        "column": col,
                        "count": int(outlier_count)
                    })
        
        return operations
    
    def _handle_inconsistent_values(self, data: pd.DataFrame, column_types: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Handle inconsistent values in the dataset
        
        Args:
            data: DataFrame to process (modified in place)
            column_types: Dictionary of column types
            
        Returns:
            List of operations performed
        """
        operations = []
        
        for col in data.columns:
            col_type = column_types.get(col, "text")
            
            # Skip numeric columns and columns with too many unique values
            if col_type in ["integer", "float"] or len(data[col].unique()) > 100:
                continue
                
            strategy = self.config["inconsistent_values"]["strategy"]
            
            # If strategy is auto, standardize text and categorical columns
            if strategy == "auto":
                strategy = "standardize"
            
            if strategy == "standardize":
                # For categorical and text columns
                if col_type in ["categorical", "text", "email"]:
                    # Convert to string first
                    data[col] = data[col].astype(str)
                    
                    # Remove extra whitespace
                    old_data = data[col].copy()
                    data[col] = data[col].str.strip()
                    
                    # Make lowercase if configured
                    if not self.config["inconsistent_values"]["case_sensitive"]:
                        data[col] = data[col].str.lower()
                    
                    # Special handling for email addresses
                    if col_type == "email":
                        # Basic email cleanup
                        data[col] = data[col].str.replace(r'\s+@\s+', '@', regex=True)
                        data[col] = data[col].str.replace(r'\s+', '', regex=True)
                    
                    # Count changes
                    changed = (old_data != data[col]).sum()
                    
                    if changed > 0:
                        operations.append({
                            "operation": "standardize_values",
                            "column": col,
                            "count": int(changed)
                        })
        
        return operations

class DataValidationAgent:
    """Class for validating data quality using configurable rules"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data validation agent
        
        Args:
            config: Configuration dictionary for validation rules
        """
        self.config = config or {
            "schema_validation": True,
            "completeness_threshold": 0.9,  # 90% completeness required
            "consistency_checks": True,
            "format_validation": True,
            "relationship_validation": False,
            "custom_rules": []
        }
        self.rules = []
        logger.info("DataValidationAgent initialized")
    
    def add_rule(self, rule: Dict[str, Any]) -> None:
        """
        Add a validation rule
        
        Args:
            rule: Rule definition dictionary
        """
        required_fields = ["name", "type", "condition"]
        if not all(field in rule for field in required_fields):
            raise ValueError(f"Rule missing required fields. Required: {required_fields}")
        
        self.rules.append(rule)
    
    def load_rules(self, rules_config: Union[str, Dict, List]) -> Dict[str, Any]:
        """
        Load rules from configuration
        
        Args:
            rules_config: Rules configuration as JSON string, dict or list
            
        Returns:
            Dict with loaded rules info
        """
        try:
            # Parse JSON if string
            if isinstance(rules_config, str):
                rules = json.loads(rules_config)
            else:
                rules = rules_config
            
            # Handle list or dict with rules key
            if isinstance(rules, dict) and "rules" in rules:
                rules = rules["rules"]
            
            # Ensure rules is a list
            if not isinstance(rules, list):
                rules = [rules]
            
            # Validate and add each rule
            valid_rules = []
            invalid_rules = []
            
            for rule in rules:
                try:
                    self.add_rule(rule)
                    valid_rules.append(rule)
                except Exception as e:
                    invalid_rules.append({
                        "rule": rule,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "loaded_rules": len(valid_rules),
                "invalid_rules": len(invalid_rules),
                "invalid_rule_details": invalid_rules
            }
            
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_dataset(self, data: pd.DataFrame, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate a dataset against rules and schema
        
        Args:
            data: Pandas DataFrame to validate
            schema: Optional schema definition
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation_results = {
                "success": True,
                "passed": True,
                "summary": {
                    "total_checks": 0,
                    "passed_checks": 0,
                    "failed_checks": 0,
                    "completeness_score": 0,
                    "consistency_score": 0,
                    "format_score": 0,
                    "overall_quality_score": 0
                },
                "checks": []
            }
            
            # 1. Schema validation
            if self.config["schema_validation"] and schema:
                schema_results = self._validate_schema(data, schema)
                validation_results["checks"].extend(schema_results["checks"])
                validation_results["summary"]["total_checks"] += schema_results["total_checks"]
                validation_results["summary"]["passed_checks"] += schema_results["passed_checks"]
                validation_results["summary"]["failed_checks"] += schema_results["failed_checks"]
                
                if schema_results["failed_checks"] > 0:
                    validation_results["passed"] = False
            
            # 2. Completeness check
            completeness_results = self._check_completeness(data)
            validation_results["checks"].append(completeness_results)
            validation_results["summary"]["total_checks"] += 1
            
            if completeness_results["passed"]:
                validation_results["summary"]["passed_checks"] += 1
            else:
                validation_results["summary"]["failed_checks"] += 1
                validation_results["passed"] = False
            
            validation_results["summary"]["completeness_score"] = completeness_results["score"]
            
            # 3. Format validation
            if self.config["format_validation"]:
                format_results = self._validate_formats(data)
                validation_results["checks"].extend(format_results["checks"])
                validation_results["summary"]["total_checks"] += format_results["total_checks"]
                validation_results["summary"]["passed_checks"] += format_results["passed_checks"]
                validation_results["summary"]["failed_checks"] += format_results["failed_checks"]
                
                validation_results["summary"]["format_score"] = format_results["score"]
                
                if format_results["failed_checks"] > 0:
                    validation_results["passed"] = False
            
            # 4. Consistency checks
            if self.config["consistency_checks"]:
                consistency_results = self._check_consistency(data)
                validation_results["checks"].extend(consistency_results["checks"])
                validation_results["summary"]["total_checks"] += consistency_results["total_checks"]
                validation_results["summary"]["passed_checks"] += consistency_results["passed_checks"]
                validation_results["summary"]["failed_checks"] += consistency_results["failed_checks"]
                
                validation_results["summary"]["consistency_score"] = consistency_results["score"]
                
                if consistency_results["failed_checks"] > 0:
                    validation_results["passed"] = False
            
            # 5. Custom rules
            if self.rules:
                rule_results = self._apply_custom_rules(data)
                validation_results["checks"].extend(rule_results["checks"])
                validation_results["summary"]["total_checks"] += rule_results["total_checks"]
                validation_results["summary"]["passed_checks"] += rule_results["passed_checks"]
                validation_results["summary"]["failed_checks"] += rule_results["failed_checks"]
                
                if rule_results["failed_checks"] > 0:
                    validation_results["passed"] = False
            
            # Calculate overall quality score
            scores = []
            
            if "completeness_score" in validation_results["summary"]:
                scores.append(validation_results["summary"]["completeness_score"])
                
            if "format_score" in validation_results["summary"]:
                scores.append(validation_results["summary"]["format_score"])
                
            if "consistency_score" in validation_results["summary"]:
                scores.append(validation_results["summary"]["consistency_score"])
            
            if scores:
                validation_results["summary"]["overall_quality_score"] = sum(scores) / len(scores)
            else:
                validation_results["summary"]["overall_quality_score"] = 0
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating dataset: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_schema(self, data: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against a schema
        
        Args:
            data: DataFrame to validate
            schema: Schema definition
            
        Returns:
            Results of schema validation
        """
        results = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "checks": []
        }
        
        # Validate columns existence
        if "fields" in schema:
            required_columns = [col for col, field in schema["fields"].items() 
                              if field.get("required", True)]
            
            for column in required_columns:
                check = {
                    "name": f"Column existence: {column}",
                    "type": "schema",
                    "passed": column in data.columns,
                }
                
                if not check["passed"]:
                    check["message"] = f"Required column '{column}' is missing"
                
                results["checks"].append(check)
                results["total_checks"] += 1
                
                if check["passed"]:
                    results["passed_checks"] += 1
                else:
                    results["failed_checks"] += 1
            
            # Validate column types and constraints
            for column, field in schema["fields"].items():
                if column not in data.columns:
                    continue
                
                field_type = field.get("type", "string")
                
                # Type validation
                type_check = {
                    "name": f"Column type: {column}",
                    "type": "schema",
                    "passed": True
                }
                
                if field_type == "integer":
                    valid_type = pd.api.types.is_integer_dtype(data[column].dtype) or \
                                (pd.api.types.is_float_dtype(data[column].dtype) and 
                                 data[column].dropna().apply(lambda x: float(x).is_integer()).all())
                    if not valid_type:
                        type_check["passed"] = False
                        type_check["message"] = f"Column '{column}' should be integer"
                
                elif field_type == "number":
                    valid_type = pd.api.types.is_numeric_dtype(data[column].dtype)
                    if not valid_type:
                        type_check["passed"] = False
                        type_check["message"] = f"Column '{column}' should be numeric"
                
                elif field_type == "boolean":
                    valid_type = pd.api.types.is_bool_dtype(data[column].dtype) or \
                                data[column].isin([0, 1, True, False, "True", "False", "true", "false"]).all()
                    if not valid_type:
                        type_check["passed"] = False
                        type_check["message"] = f"Column '{column}' should be boolean"
                
                elif field_type == "date":
                    try:
                        pd.to_datetime(data[column])
                    except:
                        type_check["passed"] = False
                        type_check["message"] = f"Column '{column}' should contain valid dates"
                
                results["checks"].append(type_check)
                results["total_checks"] += 1
                
                if type_check["passed"]:
                    results["passed_checks"] += 1
                else:
                    results["failed_checks"] += 1
                
                # Constraints validation
                if "constraints" in field:
                    for constraint_name, constraint_value in field["constraints"].items():
                        constraint_check = {
                            "name": f"Constraint {constraint_name} on {column}",
                            "type": "schema",
                            "passed": True
                        }
                        
                        # Skip if all values are null
                        if data[column].isna().all():
                            continue
                        
                        try:
                            if constraint_name == "min" and field_type in ["integer", "number"]:
                                valid = data[column].dropna().astype(float).min() >= constraint_value
                                if not valid:
                                    constraint_check["passed"] = False
                                    constraint_check["message"] = f"Column '{column}' has values below minimum {constraint_value}"
                            
                            elif constraint_name == "max" and field_type in ["integer", "number"]:
                                valid = data[column].dropna().astype(float).max() <= constraint_value
                                if not valid:
                                    constraint_check["passed"] = False
                                    constraint_check["message"] = f"Column '{column}' has values above maximum {constraint_value}"
                            
                            elif constraint_name == "min_length" and field_type in ["string", "text"]:
                                valid = data[column].dropna().astype(str).str.len().min() >= constraint_value
                                if not valid:
                                    constraint_check["passed"] = False
                                    constraint_check["message"] = f"Column '{column}' has strings below minimum length {constraint_value}"
                            
                            elif constraint_name == "max_length" and field_type in ["string", "text"]:
                                valid = data[column].dropna().astype(str).str.len().max() <= constraint_value
                                if not valid:
                                    constraint_check["passed"] = False
                                    constraint_check["message"] = f"Column '{column}' has strings above maximum length {constraint_value}"
                            
                            elif constraint_name == "regex" and field_type in ["string", "text"]:
                                pattern = re.compile(constraint_value)
                                valid = data[column].dropna().astype(str).apply(lambda x: bool(pattern.match(x))).all()
                                if not valid:
                                    constraint_check["passed"] = False
                                    constraint_check["message"] = f"Column '{column}' has values not matching pattern {constraint_value}"
                            
                            elif constraint_name == "allowed_values":
                                valid = data[column].dropna().isin(constraint_value).all()
                                if not valid:
                                    constraint_check["passed"] = False
                                    constraint_check["message"] = f"Column '{column}' has values outside allowed set"
                        except Exception as e:
                            constraint_check["passed"] = False
                            constraint_check["message"] = f"Error checking constraint {constraint_name} on {column}: {str(e)}"
                        
                        results["checks"].append(constraint_check)
                        results["total_checks"] += 1
                        
                        if constraint_check["passed"]:
                            results["passed_checks"] += 1
                        else:
                            results["failed_checks"] += 1
        
        return results
    
    def _check_completeness(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data completeness
        
        Args:
            data: DataFrame to check
            
        Returns:
            Completeness check result
        """
        total_cells = data.size
        missing_cells = data.isna().sum().sum()
        completeness_ratio = 1 - (missing_cells / total_cells if total_cells > 0 else 0)
        
        # Check if completeness ratio meets threshold
        threshold = self.config["completeness_threshold"]
        passed = completeness_ratio >= threshold
        
        return {
            "name": "Data Completeness",
            "type": "completeness",
            "passed": passed,
            "score": float(completeness_ratio),
            "threshold": threshold,
            "message": f"Data is {completeness_ratio:.2%} complete (threshold: {threshold:.2%})"
        }
    
    def _validate_formats(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data formats
        
        Args:
            data: DataFrame to validate
            
        Returns:
            Format validation results
        """
        results = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "checks": [],
            "score": 0
        }
        
        # Infer column types and validate formats
        column_formats = {}
        
        # Try to identify column types
        for col in data.columns:
            # Skip columns with too many null values
            if data[col].isna().mean() > 0.5:
                continue
                
            # Email format check
            if data[col].dtype == object:
                sample = data[col].dropna().astype(str).iloc[:100]  # Sample first 100 non-null values
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                
                email_match_ratio = sample.str.match(email_pattern).mean()
                if email_match_ratio > 0.5:  # If > 50% match, likely emails
                    column_formats[col] = "email"
                    
                    check = {
                        "name": f"Email Format: {col}",
                        "type": "format",
                        "passed": email_match_ratio > 0.9  # 90% must match to pass
                    }
                    
                    if not check["passed"]:
                        check["message"] = f"Column '{col}' contains email values with invalid format"
                    
                    check["score"] = email_match_ratio
                    results["checks"].append(check)
                    results["total_checks"] += 1
                    
                    if check["passed"]:
                        results["passed_checks"] += 1
                    else:
                        results["failed_checks"] += 1
                        
            # URL format check
            if data[col].dtype == object and col not in column_formats:
                sample = data[col].dropna().astype(str).iloc[:100]
                url_pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
                
                url_match_ratio = sample.str.match(url_pattern).mean()
                if url_match_ratio > 0.5:  # If > 50% match, likely URLs
                    column_formats[col] = "url"
                    
                    check = {
                        "name": f"URL Format: {col}",
                        "type": "format",
                        "passed": url_match_ratio > 0.9
                    }
                    
                    if not check["passed"]:
                        check["message"] = f"Column '{col}' contains URL values with invalid format"
                    
                    check["score"] = url_match_ratio
                    results["checks"].append(check)
                    results["total_checks"] += 1
                    
                    if check["passed"]:
                        results["passed_checks"] += 1
                    else:
                        results["failed_checks"] += 1
                        
            # Date format check
            if col not in column_formats:
                try:
                    if pd.api.types.is_datetime64_dtype(data[col]):
                        column_formats[col] = "datetime"
                    else:
                        # Try to convert to datetime
                        pd.to_datetime(data[col])
                        column_formats[col] = "datetime"
                        
                        # Check if conversion worked for at least 90%
                        valid_dates = pd.to_datetime(data[col], errors='coerce').notna()
                        date_ratio = valid_dates.mean()
                        
                        check = {
                            "name": f"Date Format: {col}",
                            "type": "format",
                            "passed": date_ratio > 0.9
                        }
                        
                        if not check["passed"]:
                            check["message"] = f"Column '{col}' contains date values with invalid format"
                        
                        check["score"] = date_ratio
                        results["checks"].append(check)
                        results["total_checks"] += 1
                        
                        if check["passed"]:
                            results["passed_checks"] += 1
                        else:
                            results["failed_checks"] += 1
                except:
                    pass
                    
            # Phone number format check
            if data[col].dtype == object and col not in column_formats:
                sample = data[col].dropna().astype(str).iloc[:100]
                
                # First standardize by removing common separators
                standardized = sample.str.replace(r'[\s\-\(\)\+]', '', regex=True)
                
                # Check if mostly digits of reasonable length
                digit_ratio = standardized.str.match(r'^\d{7,15}$').mean()
                
                if digit_ratio > 0.5:  # If > 50% match, likely phone numbers
                    column_formats[col] = "phone"
                    
                    check = {
                        "name": f"Phone Format: {col}",
                        "type": "format",
                        "passed": digit_ratio > 0.9
                    }
                    
                    if not check["passed"]:
                        check["message"] = f"Column '{col}' contains phone numbers with invalid format"
                    
                    check["score"] = digit_ratio
                    results["checks"].append(check)
                    results["total_checks"] += 1
                    
                    if check["passed"]:
                        results["passed_checks"] += 1
                    else:
                        results["failed_checks"] += 1
        
        # Calculate format score
        if results["total_checks"] > 0:
            format_scores = [check.get("score", 0) for check in results["checks"]]
            results["score"] = sum(format_scores) / len(format_scores)
        
        return results
    
    def _check_consistency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data consistency
        
        Args:
            data: DataFrame to check
            
        Returns:
            Consistency check results
        """
        results = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "checks": [],
            "score": 0
        }
        
        # Check 1: Duplicate rows
        dupes_check = {
            "name": "Duplicate Rows",
            "type": "consistency",
            "passed": True
        }
        
        duplicate_count = data.duplicated().sum()
        dupes_ratio = duplicate_count / len(data) if len(data) > 0 else 0
        
        if dupes_ratio > 0.01:  # Allow up to 1% duplicates
            dupes_check["passed"] = False
            dupes_check["message"] = f"Found {duplicate_count} duplicate rows ({dupes_ratio:.2%})"
        
        dupes_check["score"] = 1 - dupes_ratio
        results["checks"].append(dupes_check)
        results["total_checks"] += 1
        
        if dupes_check["passed"]:
            results["passed_checks"] += 1
        else:
            results["failed_checks"] += 1
        
        # Check 2: Value consistency for categorical columns
        for col in data.columns:
            # Skip columns with too many unique values
            if data[col].dtype == object and len(data[col].unique()) <= 50:
                # Check for inconsistent capitalization or spacing
                values = data[col].dropna().astype(str)
                standardized = values.str.strip().str.lower()
                
                # Count unique values before and after standardization
                orig_count = len(values.unique())
                std_count = len(standardized.unique())
                
                if std_count < orig_count:
                    consistency_ratio = std_count / orig_count
                    
                    check = {
                        "name": f"Value Consistency: {col}",
                        "type": "consistency",
                        "passed": consistency_ratio > 0.9  # If > 90% are consistent after normalization
                    }
                    
                    if not check["passed"]:
                        check["message"] = f"Column '{col}' has inconsistent values (capitalization/spacing)"
                    
                    check["score"] = consistency_ratio
                    results["checks"].append(check)
                    results["total_checks"] += 1
                    
                    if check["passed"]:
                        results["passed_checks"] += 1
                    else:
                        results["failed_checks"] += 1
        
        # Calculate consistency score
        if results["total_checks"] > 0:
            scores = [check.get("score", 0) for check in results["checks"]]
            results["score"] = sum(scores) / len(scores)
        
        return results
    
    def _apply_custom_rules(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Apply custom validation rules
        
        Args:
            data: DataFrame to check
            
        Returns:
            Custom rule validation results
        """
        results = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "checks": []
        }
        
        for rule in self.rules:
            rule_name = rule["name"]
            rule_type = rule["type"]
            condition = rule["condition"]
            
            check = {
                "name": rule_name,
                "type": rule_type,
                "passed": True
            }
            
            try:
                # Evaluate rule condition
                if rule_type == "row_level":
                    # Row-level rules are evaluated for each row
                    violations = 0
                    
                    for _, row in data.iterrows():
                        context = row.to_dict()
                        # Create rule evaluation code
                        code = f"result = {condition}"
                        # Create local namespace
                        local_vars = {"data": context, "re": re, "np": np}
                        
                        # Execute and get result
                        exec(code, {}, local_vars)
                        if not local_vars.get("result", True):
                            violations += 1
                    
                    violation_ratio = violations / len(data) if len(data) > 0 else 0
                    threshold = rule.get("threshold", 0.01)  # Default 1% threshold
                    
                    if violation_ratio > threshold:
                        check["passed"] = False
                        check["message"] = f"{violations} rows ({violation_ratio:.2%}) violate rule '{rule_name}'"
                
                elif rule_type == "column_level":
                    # Column-level rules are evaluated on the entire column
                    columns = rule.get("columns", [])
                    
                    for col in columns:
                        if col in data.columns:
                            context = {"values": data[col].tolist(), "column": data[col]}
                            # Create rule evaluation code
                            code = f"result = {condition}"
                            # Create local namespace
                            local_vars = {"data": context, "re": re, "np": np, "pd": pd}
                            
                            # Execute and get result
                            exec(code, {}, local_vars)
                            if not local_vars.get("result", True):
                                check["passed"] = False
                                check["message"] = f"Column '{col}' violates rule '{rule_name}'"
                                break
                
                elif rule_type == "dataset_level":
                    # Dataset-level rules are evaluated on the entire dataset
                    context = {"df": data}
                    # Create rule evaluation code
                    code = f"result = {condition}"
                    # Create local namespace
                    local_vars = {"data": context, "re": re, "np": np, "pd": pd}
                    
                    # Execute and get result
                    exec(code, {}, local_vars)
                    if not local_vars.get("result", True):
                        check["passed"] = False
                        check["message"] = f"Dataset violates rule '{rule_name}'"
                
            except Exception as e:
                check["passed"] = False
                check["message"] = f"Error evaluating rule '{rule_name}': {str(e)}"
            
            results["checks"].append(check)
            results["total_checks"] += 1
            
            if check["passed"]:
                results["passed_checks"] += 1
            else:
                results["failed_checks"] += 1
        
        return results

# Example usage
if __name__ == "__main__":
    # Create sample data with quality issues
    data = pd.DataFrame({
        'customer_id': ['C001', 'C002', 'C003', 'C004', 'C005', 'C005'],  # Duplicate
        'email': ['john@example.com', 'jane@example', 'bob@gmail.com', None, 'alice@example.com'],
        'age': [25, -5, 40, 35, 1000],  # Negative and very high values
        'signup_date': ['2020-01-01', '2021-05-15', 'invalid date', '2022-12-31', '2023-01-01'],
        'status': ['Active', 'active', ' ACTIVE ', 'inactive', 'Inactive']  # Inconsistent capitalization
    })
    
    # Test data cleaning
    cleaner = DataCleaningAgent()
    cleaning_results = cleaner.clean_dataset(data)
    
    # Test data validation with custom rules
    validator = DataValidationAgent()
    validator.add_rule({
        "name": "Valid Age",
        "type": "row_level",
        "condition": "data['age'] >= 0 and data['age'] < 120"
    })
    validator.add_rule({
        "name": "Valid Email",
        "type": "row_level",
        "condition": "data['email'] is None or re.match(r'^[\\w.-]+@[\\w.-]+\\.[a-zA-Z]{2,}$', str(data['email']))"
    })
    
    validation_results = validator.validate_dataset(cleaning_results["cleaned_data"])
    
    # Print results
    print("\nCleaning Summary:")
    print(json.dumps(cleaning_results["summary"], indent=2))
    
    print("\nValidation Results:")
    print(json.dumps(validation_results["summary"], indent=2))
