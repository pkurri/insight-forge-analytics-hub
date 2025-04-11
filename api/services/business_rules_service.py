
"""
Business Rules Service Module

This module provides services for managing, validating, and generating
business rules for datasets.
"""

import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import re

from api.repositories.business_rules_repository import BusinessRulesRepository
from api.repositories.dataset_repository import DatasetRepository
from api.models.dataset import BusinessRule, BusinessRuleCreate, BusinessRuleSeverity
from api.utils.file_utils import load_dataset_to_dataframe

# Initialize repositories
business_rules_repo = BusinessRulesRepository()
dataset_repo = DatasetRepository()

logger = logging.getLogger(__name__)

class RuleEngine:
    """Class for managing and executing business rules on data."""
    
    def __init__(self, rules: List[Dict[str, Any]] = None):
        """Initialize rule engine with optional list of rules."""
        self.rules = rules or []
        logger.info(f"RuleEngine initialized with {len(self.rules)} rules")
    
    async def load_rules(self, dataset_id: int) -> Dict[str, Any]:
        """Load rules for a dataset from the database."""
        try:
            rules = await business_rules_repo.get_rules(dataset_id)
            self.rules = rules
            return {
                "success": True,
                "loaded_rules": len(rules),
                "rules": rules
            }
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _compile_condition(self, condition: str):
        """Compile a rule condition into an executable function."""
        # First, replace common operators for better readability
        condition = condition.replace('==', '==').replace('!=', '!=')
        condition = condition.replace('<=', '<=').replace('>=', '>=')
        
        # Create a function that accepts a data context and evaluates the condition
        try:
            # Create the function code
            fn_code = f"""
def evaluate_condition(data):
    try:
        return bool({condition})
    except Exception as e:
        return False
"""
            # Create a local namespace
            local_namespace = {}
            
            # Execute the function definition in the local namespace
            exec(fn_code, {'re': re, 'np': np, 'pd': pd}, local_namespace)
            
            # Return the compiled function
            return local_namespace['evaluate_condition']
            
        except Exception as e:
            logger.error(f"Error compiling condition '{condition}': {str(e)}")
            raise ValueError(f"Invalid condition syntax: {str(e)}")
    
    async def apply_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Apply loaded rules to a dataframe and get violations."""
        try:
            if not self.rules:
                return {
                    "success": True,
                    "message": "No rules to apply",
                    "rules_applied": 0,
                    "violations": []
                }
            
            violations = []
            rules_applied = 0
            
            # Apply each rule to the data
            for rule in self.rules:
                if not rule.get("is_active", True):
                    continue
                    
                rules_applied += 1
                rule_id = rule["id"]
                rule_name = rule["name"]
                condition = rule["condition"]
                severity = rule.get("severity", "medium")
                message = rule.get("message", f"Violated rule: {rule_name}")
                
                try:
                    # Compile the condition
                    evaluate_fn = self._compile_condition(condition)
                    
                    # Apply the rule to each row
                    for index, row in df.iterrows():
                        # Create data context
                        context = row.to_dict()
                        
                        # Evaluate the condition
                        result = evaluate_fn(context)
                        
                        # If condition is False, it's a violation
                        if not result:
                            violations.append({
                                "rule_id": rule_id,
                                "rule_name": rule_name,
                                "row_index": int(index),
                                "severity": severity,
                                "message": message
                            })
                            
                            # Limit to 1000 violations for performance
                            if len(violations) >= 1000:
                                break
                    
                except Exception as e:
                    logger.error(f"Error applying rule '{rule_name}': {str(e)}")
                    violations.append({
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "row_index": None,
                        "severity": "error",
                        "message": f"Error evaluating rule: {str(e)}"
                    })
            
            return {
                "success": True,
                "rules_applied": rules_applied,
                "total_rows": len(df),
                "violation_count": len(violations),
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"Error applying rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_rules(self, df: pd.DataFrame, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate business rules from data using heuristics and patterns."""
        try:
            if options is None:
                options = {}
                
            generated_rules = []
            rule_id_counter = 1
            
            # Generate rules for each column based on data patterns
            for column in df.columns:
                column_data = df[column]
                dtype = column_data.dtype
                
                # Skip columns with too many unique values
                unique_ratio = len(column_data.dropna().unique()) / len(column_data.dropna()) if len(column_data.dropna()) > 0 else 0
                if unique_ratio > 0.9 and len(column_data) > 10:
                    continue
                
                # Generate rules based on data type
                if pd.api.types.is_numeric_dtype(dtype):
                    # Numeric column rules
                    rules = self._generate_numeric_rules(column, column_data, rule_id_counter)
                    generated_rules.extend(rules)
                    rule_id_counter += len(rules)
                    
                elif pd.api.types.is_string_dtype(dtype):
                    # String column rules
                    rules = self._generate_string_rules(column, column_data, rule_id_counter)
                    generated_rules.extend(rules)
                    rule_id_counter += len(rules)
                    
                elif pd.api.types.is_datetime64_dtype(dtype):
                    # Date column rules
                    rules = self._generate_date_rules(column, column_data, rule_id_counter)
                    generated_rules.extend(rules)
                    rule_id_counter += len(rules)
            
            # Generate cross-column rules if requested
            if options.get("cross_column_rules", True):
                # Find potential correlations or relationships
                corr_rules = self._generate_correlation_rules(df, rule_id_counter)
                generated_rules.extend(corr_rules)
                rule_id_counter += len(corr_rules)
            
            return {
                "success": True,
                "rules_generated": len(generated_rules),
                "rules": generated_rules
            }
            
        except Exception as e:
            logger.error(f"Error generating rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_numeric_rules(self, column: str, data: pd.Series, start_id: int) -> List[Dict[str, Any]]:
        """Generate rules for numeric columns."""
        rules = []
        data = data.dropna()
        
        if len(data) == 0:
            return rules
        
        # Get basic statistics
        min_val = data.min()
        max_val = data.max()
        q1 = data.quantile(0.01)  # 1st percentile
        q99 = data.quantile(0.99)  # 99th percentile
        
        # Range rule
        rules.append({
            "id": f"R{start_id}",
            "name": f"{column} Range Check",
            "condition": f"data['{column}'] >= {min_val} and data['{column}'] <= {max_val}",
            "severity": "high",
            "message": f"{column} must be between {min_val} and {max_val}"
        })
        
        # Outlier rule (more lenient)
        if q1 < q99:
            rules.append({
                "id": f"R{start_id + 1}",
                "name": f"{column} Outlier Check",
                "condition": f"data['{column}'] >= {q1} and data['{column}'] <= {q99}",
                "severity": "medium",
                "message": f"{column} has potential outlier value"
            })
        
        # If integers, check for specific values
        if pd.api.types.is_integer_dtype(data.dtype):
            # Check if column might be categorical
            unique_vals = data.unique()
            if len(unique_vals) <= 10:
                vals_str = ", ".join(map(str, unique_vals))
                rules.append({
                    "id": f"R{start_id + 2}",
                    "name": f"{column} Allowed Values",
                    "condition": f"data['{column}'] in [{vals_str}]",
                    "severity": "medium",
                    "message": f"{column} must be one of: {vals_str}"
                })
        
        return rules
    
    def _generate_string_rules(self, column: str, data: pd.Series, start_id: int) -> List[Dict[str, Any]]:
        """Generate rules for string columns."""
        rules = []
        data = data.dropna().astype(str)
        
        if len(data) == 0:
            return rules
        
        # Check if column looks like an email
        if any('@' in str(x) and '.' in str(x).split('@')[-1] for x in data.sample(min(10, len(data)))):
            rules.append({
                "id": f"R{start_id}",
                "name": f"{column} Email Format",
                "condition": f"re.match(r'^[\\w.-]+@[\\w.-]+\\.[a-zA-Z]{{2,}}$', str(data['{column}']))",
                "severity": "high",
                "message": f"{column} must be a valid email address"
            })
            
        # Length rules
        min_len = min(len(str(x)) for x in data)
        max_len = max(len(str(x)) for x in data)
        
        rules.append({
            "id": f"R{start_id + 1}",
            "name": f"{column} Length Check",
            "condition": f"len(str(data['{column}'])) >= {min_len} and len(str(data['{column}'])) <= {max_len}",
            "severity": "medium",
            "message": f"{column} length must be between {min_len} and {max_len} characters"
        })
        
        # Check if column might be categorical
        if len(data.unique()) <= 20 and len(data.unique()) < len(data) / 2:
            # Create allowed values rule
            vals = list(data.unique())
            vals_str = ", ".join(f"'{x}'" for x in vals)
            
            rules.append({
                "id": f"R{start_id + 2}",
                "name": f"{column} Allowed Values",
                "condition": f"str(data['{column}']) in [{vals_str}]",
                "severity": "medium",
                "message": f"{column} must be one of the allowed values"
            })
        
        return rules
    
    def _generate_date_rules(self, column: str, data: pd.Series, start_id: int) -> List[Dict[str, Any]]:
        """Generate rules for date columns."""
        rules = []
        data = data.dropna()
        
        if len(data) == 0:
            return rules
        
        # Get min and max dates
        min_date = data.min()
        max_date = data.max()
        
        # Convert to string format for rule
        min_date_str = min_date.strftime('%Y-%m-%d')
        max_date_str = max_date.strftime('%Y-%m-%d')
        
        rules.append({
            "id": f"R{start_id}",
            "name": f"{column} Date Range",
            "condition": f"pd.to_datetime(data['{column}']) >= pd.to_datetime('{min_date_str}') and " + 
                        f"pd.to_datetime(data['{column}']) <= pd.to_datetime('{max_date_str}')",
            "severity": "medium",
            "message": f"{column} must be between {min_date_str} and {max_date_str}"
        })
        
        # Future date rule if max date is recent
        today = pd.Timestamp.now().floor('D')
        if (max_date - today).days < 30:  # If max date is within a month of today
            rules.append({
                "id": f"R{start_id + 1}",
                "name": f"{column} No Future Dates",
                "condition": f"pd.to_datetime(data['{column}']) <= pd.Timestamp.now()",
                "severity": "high", 
                "message": f"{column} cannot be in the future"
            })
            
        return rules
    
    def _generate_correlation_rules(self, data: pd.DataFrame, start_id: int) -> List[Dict[str, Any]]:
        """Generate rules based on column correlations and relationships."""
        rules = []
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        # Skip if too few numeric columns
        if len(numeric_cols) < 2:
            return rules
        
        try:
            # Calculate correlation matrix
            corr_matrix = data[numeric_cols].corr()
            
            # Find highly correlated pairs
            for i in range(len(numeric_cols)):
                for j in range(i+1, len(numeric_cols)):
                    col1 = numeric_cols[i]
                    col2 = numeric_cols[j]
                    corr = corr_matrix.iloc[i, j]
                    
                    # Strong positive correlation
                    if corr > 0.8:
                        rules.append({
                            "id": f"R{start_id}",
                            "name": f"{col1} - {col2} Correlation",
                            "condition": f"data['{col1}'] * 0.5 <= data['{col2}'] <= data['{col1}'] * 1.5",
                            "severity": "low",
                            "message": f"Expected correlation between {col1} and {col2} not maintained"
                        })
                        start_id += 1
                        
                    # Strong negative correlation
                    elif corr < -0.8:
                        rules.append({
                            "id": f"R{start_id}",
                            "name": f"{col1} - {col2} Inverse Correlation",
                            "condition": f"(data['{col1}'] > 0 and data['{col2}'] < 0) or " + 
                                      f"(data['{col1}'] < 0 and data['{col2}'] > 0) or " +
                                      f"(data['{col1}'] == 0 and data['{col2}'] == 0)",
                            "severity": "low",
                            "message": f"Expected inverse correlation between {col1} and {col2} not maintained"
                        })
                        start_id += 1
        except Exception as e:
            logger.warning(f"Error generating correlation rules: {str(e)}")
            
        return rules

async def get_rules(dataset_id: int) -> Dict[str, Any]:
    """Get all business rules for a dataset."""
    try:
        rules = await business_rules_repo.get_rules(dataset_id)
        return {
            "success": True,
            "rules": rules,
            "rule_count": len(rules)
        }
    except Exception as e:
        logger.error(f"Error getting rules: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def create_rule(rule: BusinessRuleCreate) -> Dict[str, Any]:
    """Create a new business rule."""
    try:
        new_rule = await business_rules_repo.create_rule(rule)
        return {
            "success": True,
            "rule": new_rule
        }
    except Exception as e:
        logger.error(f"Error creating rule: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def update_rule(rule_id: int, rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing rule."""
    try:
        updated_rule = await business_rules_repo.update_rule(rule_id, rule_data)
        if updated_rule:
            return {
                "success": True,
                "rule": updated_rule
            }
        else:
            return {
                "success": False,
                "error": f"Rule with ID {rule_id} not found"
            }
    except Exception as e:
        logger.error(f"Error updating rule: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def delete_rule(rule_id: int) -> Dict[str, Any]:
    """Delete a business rule."""
    try:
        success = await business_rules_repo.delete_rule(rule_id)
        if success:
            return {
                "success": True,
                "message": f"Rule with ID {rule_id} deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Rule with ID {rule_id} not found"
            }
    except Exception as e:
        logger.error(f"Error deleting rule: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def validate_rules(dataset_id: int, rule_ids: List[int] = None) -> Dict[str, Any]:
    """
    Validate business rules against a dataset.
    
    Args:
        dataset_id: ID of the dataset to validate rules against
        rule_ids: Optional list of specific rule IDs to validate
        
    Returns:
        Dictionary containing validation results
    """
    try:
        # Get dataset
        dataset = await dataset_repo.get_dataset_detail(dataset_id)
        if not dataset:
            return {
                "success": False, 
                "error": f"Dataset with ID {dataset_id} not found"
            }
        
        # Load the dataset as DataFrame
        df = await load_dataset_to_dataframe(dataset)
        
        # Get rules for the dataset (filter by rule_ids if provided)
        if rule_ids:
            rules = []
            for rule_id in rule_ids:
                rule = await business_rules_repo.get_rule(rule_id)
                if rule:
                    rules.append(rule)
        else:
            rules = await business_rules_repo.get_rules(dataset_id)
        
        if not rules:
            return {
                "success": True,
                "message": "No rules to validate",
                "rules_applied": 0,
                "violations": []
            }
        
        # Initialize rule engine with the rules
        engine = RuleEngine(rules)
        
        # Apply rules
        validation_results = await engine.apply_rules(df)
        
        if validation_results["success"]:
            # Save validation results to database
            violations = validation_results["violations"]
            for rule_id in set(v["rule_id"] for v in violations):
                rule_violations = [v for v in violations if v["rule_id"] == rule_id]
                await business_rules_repo.save_rule_validation(
                    rule_id=rule_id,
                    dataset_id=dataset_id,
                    violations_count=len(rule_violations),
                    violations=rule_violations
                )
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating rules: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_rules(dataset_id: int, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate business rules for a dataset based on its data patterns.
    
    Args:
        dataset_id: ID of the dataset to generate rules for
        options: Optional configuration for rule generation
        
    Returns:
        Dictionary containing generated rules
    """
    try:
        # Get dataset
        dataset = await dataset_repo.get_dataset_detail(dataset_id)
        if not dataset:
            return {
                "success": False, 
                "error": f"Dataset with ID {dataset_id} not found"
            }
        
        # Load the dataset as DataFrame
        df = await load_dataset_to_dataframe(dataset)
        
        # Initialize rule engine
        engine = RuleEngine()
        
        # Generate rules
        generation_results = await engine.generate_rules(df, options)
        
        if not generation_results["success"]:
            return generation_results
            
        # Convert generated rules to BusinessRuleCreate objects and save to database
        generated_rules = generation_results["rules"]
        rule_creates = []
        
        for rule in generated_rules:
            rule_create = BusinessRuleCreate(
                name=rule["name"],
                dataset_id=dataset_id,
                condition=rule["condition"],
                severity=rule["severity"],
                message=rule["message"],
                model_generated=True,
                confidence=0.9  # Default confidence for generated rules
            )
            rule_creates.append(rule_create)
        
        # Save rules to database in bulk
        created_rules = await business_rules_repo.bulk_create_rules(rule_creates)
        
        return {
            "success": True,
            "rules_generated": len(created_rules),
            "rules": created_rules
        }
        
    except Exception as e:
        logger.error(f"Error generating rules: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
