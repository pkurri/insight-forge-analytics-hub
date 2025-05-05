"""
Business Rules Suggestions Module

This module provides functionality for suggesting business rules based on data analysis:
- Pattern detection
- Statistical analysis
- Machine learning-based suggestions
- Feedback-based improvement
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import re
import json
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)

async def suggest_rules_from_data(
    dataset_id: str,
    sample_data: List[Dict[str, Any]],
    min_confidence: float = 0.7,
    max_suggestions: int = 10
) -> Dict[str, Any]:
    """
    Generate rule suggestions based on sample data patterns.
    
    Args:
        dataset_id: ID of the dataset
        sample_data: Sample data to analyze for rule suggestions
        min_confidence: Minimum confidence threshold for suggestions
        max_suggestions: Maximum number of suggestions to return
        
    Returns:
        Dictionary with rule suggestions and metadata
    """
    try:
        # Convert to DataFrame for analysis
        df = pd.DataFrame(sample_data)
        if df.empty:
            return {
                "success": False,
                "error": "Empty sample data",
                "suggestions": []
            }
            
        # Analyze data and generate suggestions
        suggestions = []
        
        # Add column-based rule suggestions
        column_suggestions = generate_column_rules(df, min_confidence)
        suggestions.extend(column_suggestions)
        
        # Add relationship-based rule suggestions
        relationship_suggestions = generate_relationship_rules(df, min_confidence)
        suggestions.extend(relationship_suggestions)
        
        # Add pattern-based rule suggestions
        pattern_suggestions = generate_pattern_rules(df, min_confidence)
        suggestions.extend(pattern_suggestions)
        
        # Sort by confidence and limit
        suggestions.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        top_suggestions = suggestions[:max_suggestions]
        
        # Add dataset_id and rule IDs
        for suggestion in top_suggestions:
            suggestion["dataset_id"] = dataset_id
            suggestion["id"] = str(uuid.uuid4())
            suggestion["model_generated"] = True
            suggestion["created_at"] = datetime.utcnow().isoformat()
            suggestion["updated_at"] = datetime.utcnow().isoformat()
            
        return {
            "success": True,
            "suggestions_count": len(top_suggestions),
            "suggestions": top_suggestions,
            "analysis_summary": {
                "columns_analyzed": len(df.columns),
                "rows_analyzed": len(df),
                "total_suggestions_generated": len(suggestions),
                "confidence_threshold": min_confidence
            }
        }
    except Exception as e:
        logger.error(f"Error suggesting rules from data: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "suggestions": []
        }

def generate_column_rules(df: pd.DataFrame, min_confidence: float) -> List[Dict[str, Any]]:
    """
    Generate rule suggestions based on individual column analysis.
    
    Args:
        df: DataFrame to analyze
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of rule suggestions
    """
    suggestions = []
    
    # Analyze each column
    for column in df.columns:
        # Skip if column is empty
        if df[column].isna().all():
            continue
            
        # Get column data type
        dtype = infer_column_type(df[column])
        
        # Generate type-specific rules
        if dtype == "numeric":
            suggestions.extend(generate_numeric_rules(df, column, min_confidence))
        elif dtype == "string":
            suggestions.extend(generate_string_rules(df, column, min_confidence))
        elif dtype == "datetime":
            suggestions.extend(generate_datetime_rules(df, column, min_confidence))
        elif dtype == "boolean":
            suggestions.extend(generate_boolean_rules(df, column, min_confidence))
            
        # Add not-null rule if appropriate
        null_rate = df[column].isna().mean()
        if null_rate < 0.1:  # Less than 10% nulls
            confidence = 1.0 - null_rate
            if confidence >= min_confidence:
                suggestions.append({
                    "name": f"{column} not null",
                    "description": f"Ensures {column} is not null",
                    "rule_type": "validation",
                    "severity": "medium",
                    "source": "ai",
                    "condition": f"df['{column}'].notna().all()",
                    "confidence": round(confidence, 2),
                    "tags": ["not_null", dtype]
                })
    
    return suggestions

def generate_numeric_rules(df: pd.DataFrame, column: str, min_confidence: float) -> List[Dict[str, Any]]:
    """
    Generate rule suggestions for numeric columns.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of rule suggestions
    """
    suggestions = []
    
    # Skip if column has too many nulls
    if df[column].isna().mean() > 0.5:
        return suggestions
        
    # Get numeric values
    values = df[column].dropna()
    if len(values) == 0:
        return suggestions
        
    # Calculate statistics
    min_val = values.min()
    max_val = values.max()
    mean_val = values.mean()
    std_val = values.std()
    
    # Range rule
    range_margin = 0.1  # 10% margin
    range_min = min_val - (max_val - min_val) * range_margin
    range_max = max_val + (max_val - min_val) * range_margin
    
    # Round values for readability
    range_min = round(range_min, 2)
    range_max = round(range_max, 2)
    
    suggestions.append({
        "name": f"{column} in range",
        "description": f"Ensures {column} is between {range_min} and {range_max}",
        "rule_type": "validation",
        "severity": "medium",
        "source": "ai",
        "condition": f"df['{column}'].between({range_min}, {range_max}).all()",
        "confidence": 0.85,
        "tags": ["range", "numeric"]
    })
    
    # Check for integers
    if all(values.apply(lambda x: x == int(x))):
        suggestions.append({
            "name": f"{column} is integer",
            "description": f"Ensures {column} contains only integer values",
            "rule_type": "validation",
            "severity": "medium",
            "source": "ai",
            "condition": f"df['{column}'].apply(lambda x: x == int(x) if pd.notna(x) else True).all()",
            "confidence": 0.9,
            "tags": ["integer", "numeric"]
        })
    
    # Check for positive values
    if min_val >= 0:
        suggestions.append({
            "name": f"{column} is positive",
            "description": f"Ensures {column} contains only positive values",
            "rule_type": "validation",
            "severity": "medium",
            "source": "ai",
            "condition": f"df['{column}'] >= 0",
            "confidence": 0.85,
            "tags": ["positive", "numeric"]
        })
    
    return suggestions

def generate_string_rules(df: pd.DataFrame, column: str, min_confidence: float) -> List[Dict[str, Any]]:
    """
    Generate rule suggestions for string columns.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of rule suggestions
    """
    suggestions = []
    
    # Skip if column has too many nulls
    if df[column].isna().mean() > 0.5:
        return suggestions
        
    # Get string values
    values = df[column].dropna().astype(str)
    if len(values) == 0:
        return suggestions
    
    # Check for non-empty strings
    empty_rate = (values == "").mean()
    if empty_rate < 0.1:  # Less than 10% empty strings
        confidence = 1.0 - empty_rate
        if confidence >= min_confidence:
            suggestions.append({
                "name": f"{column} not empty",
                "description": f"Ensures {column} is not an empty string",
                "rule_type": "validation",
                "severity": "medium",
                "source": "ai",
                "condition": f"df['{column}'].astype(str).str.strip() != ''",
                "confidence": round(confidence, 2),
                "tags": ["not_empty", "string"]
            })
    
    # Check for max length
    max_length = values.str.len().max()
    if max_length > 0:
        max_length_with_margin = int(max_length * 1.2)  # 20% margin
        suggestions.append({
            "name": f"{column} max length",
            "description": f"Ensures {column} is not longer than {max_length_with_margin} characters",
            "rule_type": "validation",
            "severity": "medium",
            "source": "ai",
            "condition": f"df['{column}'].astype(str).str.len() <= {max_length_with_margin}",
            "confidence": 0.8,
            "tags": ["max_length", "string"]
        })
    
    # Check for email pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if values.str.match(email_pattern).mean() > 0.8:
        suggestions.append({
            "name": f"{column} is email",
            "description": f"Ensures {column} contains valid email addresses",
            "rule_type": "validation",
            "severity": "high",
            "source": "ai",
            "condition": f"df['{column}'].astype(str).str.match(r'{email_pattern}')",
            "confidence": 0.9,
            "tags": ["email", "string", "format"]
        })
    
    # Check for URL pattern
    url_pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    if values.str.match(url_pattern).mean() > 0.8:
        suggestions.append({
            "name": f"{column} is URL",
            "description": f"Ensures {column} contains valid URLs",
            "rule_type": "validation",
            "severity": "medium",
            "source": "ai",
            "condition": f"df['{column}'].astype(str).str.match(r'{url_pattern}')",
            "confidence": 0.85,
            "tags": ["url", "string", "format"]
        })
    
    # Check for enumeration
    unique_values = values.unique()
    if len(unique_values) <= 10 and len(unique_values) > 0 and len(values) >= 5:
        # This might be an enumeration
        unique_values_str = ", ".join([f"'{v}'" for v in unique_values])
        suggestions.append({
            "name": f"{column} valid values",
            "description": f"Ensures {column} contains only allowed values: {unique_values_str}",
            "rule_type": "validation",
            "severity": "high",
            "source": "ai",
            "condition": f"df['{column}'].isin([{unique_values_str}])",
            "confidence": 0.85,
            "tags": ["enumeration", "string"]
        })
    
    return suggestions

def generate_datetime_rules(df: pd.DataFrame, column: str, min_confidence: float) -> List[Dict[str, Any]]:
    """
    Generate rule suggestions for datetime columns.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of rule suggestions
    """
    suggestions = []
    
    # Skip if column has too many nulls
    if df[column].isna().mean() > 0.5:
        return suggestions
        
    # Get datetime values
    try:
        values = pd.to_datetime(df[column].dropna())
    except:
        return suggestions
        
    if len(values) == 0:
        return suggestions
    
    # Check for future dates
    now = pd.Timestamp.now()
    future_rate = (values > now).mean()
    if future_rate < 0.1:  # Less than 10% future dates
        confidence = 1.0 - future_rate
        if confidence >= min_confidence:
            suggestions.append({
                "name": f"{column} not in future",
                "description": f"Ensures {column} does not contain future dates",
                "rule_type": "validation",
                "severity": "medium",
                "source": "ai",
                "condition": f"pd.to_datetime(df['{column}']) <= pd.Timestamp.now()",
                "confidence": round(confidence, 2),
                "tags": ["not_future", "datetime"]
            })
    
    # Check for reasonable date range
    min_date = values.min()
    max_date = values.max()
    
    # For dates not too far in the past (last 100 years)
    hundred_years_ago = now - pd.Timedelta(days=365.25 * 100)
    if min_date > hundred_years_ago:
        suggestions.append({
            "name": f"{column} reasonable date range",
            "description": f"Ensures {column} is within a reasonable date range",
            "rule_type": "validation",
            "severity": "medium",
            "source": "ai",
            "condition": f"pd.to_datetime(df['{column}']) >= pd.Timestamp('{hundred_years_ago}')",
            "confidence": 0.8,
            "tags": ["date_range", "datetime"]
        })
    
    return suggestions

def generate_boolean_rules(df: pd.DataFrame, column: str, min_confidence: float) -> List[Dict[str, Any]]:
    """
    Generate rule suggestions for boolean columns.
    
    Args:
        df: DataFrame to analyze
        column: Column name
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of rule suggestions
    """
    # Boolean columns typically don't need specific validation rules
    # beyond not-null checks, which are already covered
    return []

def generate_relationship_rules(df: pd.DataFrame, min_confidence: float) -> List[Dict[str, Any]]:
    """
    Generate rule suggestions based on relationships between columns.
    
    Args:
        df: DataFrame to analyze
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of rule suggestions
    """
    suggestions = []
    
    # Need at least 2 columns for relationships
    if len(df.columns) < 2:
        return suggestions
    
    # Check for correlations between numeric columns
    numeric_columns = df.select_dtypes(include=['number']).columns
    if len(numeric_columns) >= 2:
        corr_matrix = df[numeric_columns].corr()
        
        # Find highly correlated pairs
        for i in range(len(numeric_columns)):
            for j in range(i+1, len(numeric_columns)):
                col1 = numeric_columns[i]
                col2 = numeric_columns[j]
                correlation = corr_matrix.iloc[i, j]
                
                # Check for strong positive correlation
                if correlation > 0.9:
                    suggestions.append({
                        "name": f"{col1} and {col2} correlation",
                        "description": f"Ensures {col1} and {col2} maintain their positive correlation",
                        "rule_type": "validation",
                        "severity": "low",
                        "source": "ai",
                        "condition": f"df['{col1}'].corr(df['{col2}']) > 0.7",
                        "confidence": round(min(correlation, 0.95), 2),
                        "tags": ["correlation", "relationship"]
                    })
    
    # Check for potential foreign key relationships
    for col1 in df.columns:
        # Skip if column has too many nulls
        if df[col1].isna().mean() > 0.3:
            continue
            
        # Check if column values are unique
        if df[col1].dropna().is_unique:
            # This could be a primary key
            for col2 in df.columns:
                if col1 != col2 and col2.endswith('_id'):
                    # This could be a foreign key referencing col1
                    if df[col2].dropna().isin(df[col1]).all():
                        suggestions.append({
                            "name": f"{col2} references {col1}",
                            "description": f"Ensures {col2} values exist in {col1}",
                            "rule_type": "validation",
                            "severity": "high",
                            "source": "ai",
                            "condition": f"df['{col2}'].dropna().isin(df['{col1}']).all()",
                            "confidence": 0.9,
                            "tags": ["foreign_key", "relationship"]
                        })
    
    return suggestions

def generate_pattern_rules(df: pd.DataFrame, min_confidence: float) -> List[Dict[str, Any]]:
    """
    Generate rule suggestions based on patterns in the data.
    
    Args:
        df: DataFrame to analyze
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of rule suggestions
    """
    suggestions = []
    
    # Check for columns with consistent patterns
    for column in df.columns:
        # Skip if column has too many nulls
        if df[column].isna().mean() > 0.3:
            continue
            
        # Get string values
        values = df[column].dropna().astype(str)
        if len(values) < 5:
            continue
            
        # Check for common patterns
        patterns = detect_string_patterns(values)
        for pattern_name, pattern_info in patterns.items():
            if pattern_info["confidence"] >= min_confidence:
                suggestions.append({
                    "name": f"{column} {pattern_name} pattern",
                    "description": f"Ensures {column} follows the pattern: {pattern_info['description']}",
                    "rule_type": "validation",
                    "severity": "medium",
                    "source": "ai",
                    "condition": f"df['{column}'].astype(str).str.match(r'{pattern_info['regex']}')",
                    "confidence": pattern_info["confidence"],
                    "tags": ["pattern", pattern_name]
                })
    
    return suggestions

def detect_string_patterns(values: pd.Series) -> Dict[str, Dict[str, Any]]:
    """
    Detect common string patterns in a series of values.
    
    Args:
        values: Series of string values
        
    Returns:
        Dictionary of pattern names and their details
    """
    patterns = {}
    
    # Check for ZIP code pattern
    zip_pattern = r'^\d{5}(-\d{4})?$'
    zip_match_rate = values.str.match(zip_pattern).mean()
    if zip_match_rate > 0.8:
        patterns["zip_code"] = {
            "regex": zip_pattern,
            "description": "US ZIP code (5 digits with optional 4-digit extension)",
            "confidence": round(zip_match_rate, 2)
        }
    
    # Check for phone number pattern
    phone_pattern = r'^\+?1?\s*\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$'
    phone_match_rate = values.str.match(phone_pattern).mean()
    if phone_match_rate > 0.8:
        patterns["phone_number"] = {
            "regex": phone_pattern,
            "description": "Phone number format",
            "confidence": round(phone_match_rate, 2)
        }
    
    # Check for UUID pattern
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    uuid_match_rate = values.str.match(uuid_pattern, case=False).mean()
    if uuid_match_rate > 0.8:
        patterns["uuid"] = {
            "regex": uuid_pattern,
            "description": "UUID format",
            "confidence": round(uuid_match_rate, 2)
        }
    
    # Check for ISO date pattern
    iso_date_pattern = r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$'
    iso_date_match_rate = values.str.match(iso_date_pattern).mean()
    if iso_date_match_rate > 0.8:
        patterns["iso_date"] = {
            "regex": iso_date_pattern,
            "description": "ISO date format (YYYY-MM-DD with optional time)",
            "confidence": round(iso_date_match_rate, 2)
        }
    
    return patterns

def infer_column_type(column: pd.Series) -> str:
    """
    Infer the data type of a column.
    
    Args:
        column: Series to analyze
        
    Returns:
        Inferred data type as string
    """
    # Check for numeric
    if pd.api.types.is_numeric_dtype(column):
        return "numeric"
    
    # Check for boolean
    if pd.api.types.is_bool_dtype(column) or (
        column.dropna().isin([True, False, 0, 1, "True", "False", "true", "false"]).all()
    ):
        return "boolean"
    
    # Check for datetime
    try:
        pd.to_datetime(column)
        return "datetime"
    except:
        pass
    
    # Default to string
    return "string"
