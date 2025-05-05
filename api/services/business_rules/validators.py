"""
Business Rules Validators Module

This module provides functions for validating business rules and their execution results.
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_rule_condition(condition: str) -> bool:
    """Validate that a rule condition is safe and well-formed.
    
    Args:
        condition: The rule condition to validate
        
    Returns:
        bool: True if the condition is valid, False otherwise
    """
    try:
        # Basic security checks
        if any(keyword in condition.lower() for keyword in [
            "import", "exec", "eval", "os.", "sys.", "subprocess",
            "open", "file", "read", "write", "delete", "remove"
        ]):
            logger.warning(f"Rule condition contains forbidden keywords: {condition}")
            return False
            
        # Try to compile the condition
        compile(condition, "<string>", "eval")
        return True
    except Exception as e:
        logger.error(f"Error validating rule condition: {str(e)}")
        return False

def validate_rule_structure(rule: Dict[str, Any]) -> bool:
    """Validate that a rule has all required fields and they are of the correct type.
    
    Args:
        rule: The rule to validate
        
    Returns:
        bool: True if the rule is valid, False otherwise
    """
    try:
        required_fields = {
            "name": str,
            "description": str,
            "condition": str,
            "severity": str,
            "message": str,
            "source": str
        }
        
        # Check all required fields exist
        for field, field_type in required_fields.items():
            if field not in rule:
                logger.warning(f"Rule missing required field: {field}")
                return False
            if not isinstance(rule[field], field_type):
                logger.warning(f"Rule field {field} has incorrect type: {type(rule[field])}")
                return False
                
        # Validate severity is one of the allowed values
        if rule["severity"].lower() not in ["low", "medium", "high"]:
            logger.warning(f"Rule has invalid severity: {rule['severity']}")
            return False
            
        # Validate source is one of the allowed values
        if rule["source"].lower() not in ["manual", "ai_default", "huggingface", "pydantic", "great_expectations"]:
            logger.warning(f"Rule has invalid source: {rule['source']}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error validating rule structure: {str(e)}")
        return False

def validate_execution_result(result: Dict[str, Any]) -> bool:
    """Validate that a rule execution result has all required fields and they are of the correct type.
    
    Args:
        result: The execution result to validate
        
    Returns:
        bool: True if the result is valid, False otherwise
    """
    try:
        required_fields = {
            "rule_id": (int, str),
            "dataset_id": (int, str),
            "status": str,
            "execution_time": (float, int),
            "timestamp": (str, datetime),
            "details": dict
        }
        
        # Check all required fields exist
        for field, field_types in required_fields.items():
            if field not in result:
                logger.warning(f"Result missing required field: {field}")
                return False
            if not isinstance(result[field], field_types):
                logger.warning(f"Result field {field} has incorrect type: {type(result[field])}")
                return False
                
        # Validate status is one of the allowed values
        if result["status"].lower() not in ["passed", "failed", "error"]:
            logger.warning(f"Result has invalid status: {result['status']}")
            return False
            
        # Validate execution time is positive
        if result["execution_time"] <= 0:
            logger.warning(f"Result has invalid execution time: {result['execution_time']}")
            return False
            
        # Validate details contains required fields for failed rules
        if result["status"].lower() == "failed":
            if "failed_rows" not in result["details"]:
                logger.warning("Failed result missing failed_rows in details")
                return False
            if not isinstance(result["details"]["failed_rows"], (list, np.ndarray)):
                logger.warning("failed_rows must be a list or numpy array")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Error validating execution result: {str(e)}")
        return False

def validate_dataset_for_rules(dataset: pd.DataFrame, rules: List[Dict[str, Any]]) -> bool:
    """Validate that a dataset has all required columns for the given rules.
    
    Args:
        dataset: The dataset to validate
        rules: List of rules to check against
        
    Returns:
        bool: True if the dataset is valid for all rules, False otherwise
    """
    try:
        # Extract all column names used in rule conditions
        required_columns = set()
        for rule in rules:
            # Simple regex to find column references like df['column_name']
            import re
            matches = re.findall(r"df\['([^']+)'\]", rule["condition"])
            required_columns.update(matches)
            
        # Check all required columns exist in dataset
        missing_columns = required_columns - set(dataset.columns)
        if missing_columns:
            logger.warning(f"Dataset missing columns required by rules: {missing_columns}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error validating dataset for rules: {str(e)}")
        return False
