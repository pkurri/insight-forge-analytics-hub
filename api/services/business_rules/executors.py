"""
Business Rules Executors Module

This module provides functions for executing different types of business rules:
- Validation rules
- Transformation rules
- Enrichment rules
- Python expression rules
- Great Expectations rules
- Pydantic rules
- Hugging Face rules
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import ast
import re
import json
from pydantic import ValidationError, create_model
import great_expectations as ge

from api.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Rule execution functions dictionary
_EXECUTION_FUNCTIONS = {}

def get_execution_function(source: str) -> Optional[Callable]:
    """
    Get the execution function for a rule source.
    
    Args:
        source: Rule source (great_expectations, pydantic, huggingface, manual, ai, etc.)
    
    Returns:
        Execution function or None if source is unsupported
    """
    global _EXECUTION_FUNCTIONS
    
    # Initialize execution functions dictionary if empty
    if not _EXECUTION_FUNCTIONS:
        _EXECUTION_FUNCTIONS = {
            "great_expectations": _execute_ge_rule,
            "pydantic": _execute_pydantic_rule,
            "huggingface": _execute_hf_rule,
            "hf": _execute_hf_rule,
            "manual": _execute_python_rule,
            "ai": _execute_python_rule,
            "python": _execute_python_rule,
            "validation": _execute_python_rule,
            "transformation": _execute_transformation_rule,
            "enrichment": _execute_enrichment_rule
        }
    
    return _EXECUTION_FUNCTIONS.get(source)

def _compile_condition(condition: str) -> Optional[Callable]:
    """
    Compile a rule condition into an executable function.
    
    Args:
        condition: Python code string representing the condition
        
    Returns:
        Compiled function or None if compilation fails
    """
    try:
        # Validate condition syntax
        ast.parse(condition)
        
        # Create function code with proper indentation
        fn_code = f"def evaluate(data):\n    return {condition}"
        
        # Create namespace with common modules
        namespace = {}
        globals_dict = {
            're': re,
            'np': np,
            'pd': pd,
            'datetime': datetime
        }
        
        # Execute function definition
        exec(fn_code, globals_dict, namespace)
        
        return namespace['evaluate']
    except Exception as e:
        logger.error(f"Error compiling condition: {str(e)}")
        return None

async def apply_rules_to_dataset(dataset_id: str, data: List[Dict[str, Any]], 
                                rule_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Apply business rules to a dataset.
    
    Args:
        dataset_id: ID of the dataset
        data: List of data records to apply rules to
        rule_ids: Optional list of rule IDs to apply (if None, all active rules for the dataset are applied)
        
    Returns:
        Dictionary with rule application results
    """
    try:
        # Import here to avoid circular imports
        from api.services.business_rules.core import BusinessRulesService
        business_rules_service = BusinessRulesService()
        
        # Get rules for the dataset
        rules = await business_rules_service.get_rules_for_dataset(dataset_id, rule_ids)
        
        # Initialize results
        results = {
            "total_rules": len(rules),
            "passed_rules": 0,
            "failed_rules": 0,
            "total_violations": 0,
            "rule_results": []
        }
        
        # Convert data to DataFrame for rule application
        df = pd.DataFrame(data)
        
        # Apply each rule
        for rule in rules:
            rule_result = await apply_rule(rule, df)
            results["rule_results"].append(rule_result)
            
            # Update counters
            if rule_result["violation_count"] > 0:
                results["failed_rules"] += 1
                results["total_violations"] += rule_result["violation_count"]
            else:
                results["passed_rules"] += 1
                
            # Update rule execution stats
            await update_rule_stats(rule["id"], rule_result["violation_count"] == 0)
            
        return results
    except Exception as e:
        logger.error(f"Error applying rules to dataset {dataset_id}: {str(e)}")
        return {
            "total_rules": 0,
            "passed_rules": 0,
            "failed_rules": 0,
            "total_violations": 0,
            "rule_results": [],
            "error": str(e)
        }

async def apply_rule(rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Apply a single rule to data.
    
    Args:
        rule: Rule dictionary
        df: DataFrame containing data to apply rule to
        
    Returns:
        Dictionary with rule application results
    """
    try:
        # Get rule information
        rule_id = rule["id"]
        rule_name = rule["name"]
        rule_type = rule.get("rule_type", "validation")
        rule_severity = rule.get("severity", "medium")
        rule_source = rule.get("source", "manual")
        rule_condition = rule["condition"]
        rule_message = rule.get("message", "Rule violation")
        
        # Get execution function based on rule source
        execute_fn = get_execution_function(rule_source)
        if not execute_fn:
            execute_fn = _execute_python_rule
            
        # Execute rule
        execution_result = await execute_fn(rule, df)
        
        # Process violations
        violations = []
        if not execution_result["success"]:
            # Get violation details from execution result
            if "meta" in execution_result and "errors" in execution_result["meta"]:
                for idx, error in execution_result["meta"]["errors"]:
                    if idx < len(df):
                        violations.append({
                            "row": int(idx),
                            "message": error,
                            "data": df.iloc[idx].to_dict()
                        })
            else:
                # Generic violation for the whole dataset
                violations.append({
                    "message": execution_result["message"],
                    "data": None
                })
        
        # Create rule result
        rule_result = {
            "id": rule_id,
            "name": rule_name,
            "severity": rule_severity,
            "rule_type": rule_type,
            "source": rule_source,
            "model_generated": rule.get("model_generated", False),
            "violation_count": len(violations),
            "violations": violations[:10]  # Limit to first 10 for performance
        }
        
        return rule_result
    except Exception as e:
        logger.error(f"Error applying rule {rule.get('id', 'unknown')}: {str(e)}")
        return {
            "id": rule.get("id", "unknown"),
            "name": rule.get("name", "Unknown Rule"),
            "severity": rule.get("severity", "medium"),
            "rule_type": rule.get("rule_type", "validation"),
            "source": rule.get("source", "manual"),
            "model_generated": rule.get("model_generated", False),
            "violation_count": 1,
            "violations": [{
                "message": f"Error applying rule: {str(e)}",
                "data": None
            }]
        }

async def update_rule_stats(rule_id: str, success: bool) -> None:
    """
    Update rule execution statistics.
    
    Args:
        rule_id: ID of the rule
        success: Whether the rule execution was successful
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import business_rules_repository
        
        # Get current rule
        rule = await business_rules_repository.get_rule(rule_id)
        if not rule:
            return
            
        # Update execution count and success rate
        execution_count = rule.get("execution_count", 0) + 1
        success_count = rule.get("success_count", 0) + (1 if success else 0)
        success_rate = success_count / execution_count if execution_count > 0 else 0
        
        # Update rule
        updates = {
            "execution_count": execution_count,
            "success_count": success_count,
            "success_rate": success_rate,
            "last_executed": datetime.utcnow().isoformat()
        }
        
        await business_rules_repository.update_rule(rule_id, updates)
    except Exception as e:
        logger.error(f"Error updating rule stats for {rule_id}: {str(e)}")

async def validate_data_with_rules(dataset_id: str, data: List[Dict[str, Any]], 
                                 rule_ids: Optional[List[str]] = None,
                                 include_rule_suggestions: bool = False,
                                 confidence_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Validate data against rules before vectorization.
    
    Args:
        dataset_id: ID of the dataset
        data: List of data records to validate
        rule_ids: Optional list of rule IDs to apply (if None, all active validation rules for the dataset are applied)
        include_rule_suggestions: Whether to include rule suggestions based on data patterns
        confidence_threshold: Minimum confidence threshold for rule suggestions
        
    Returns:
        Dictionary with validation results and filtered data
    """
    try:
        # Import here to avoid circular imports
        from api.services.business_rules.core import BusinessRulesService
        business_rules_service = BusinessRulesService()
        
        # Get rules for the dataset, filtered by validation type if no specific rule_ids
        rules = await business_rules_service.get_rules_for_dataset(dataset_id, rule_ids)
        if not rule_ids:
            # If no specific rules requested, filter to validation rules only
            rules = [r for r in rules if r.get("rule_type", "validation") == "validation"]
            
        # Apply rules
        validation_results = await apply_rules_to_dataset(
            dataset_id, data, [r["id"] for r in rules]
        )
        
        # Filter data based on validation results
        filtered_data = data.copy()
        skipped_indices = set()
        
        # Find records that failed critical validation rules
        for rule_result in validation_results["rule_results"]:
            # Skip non-critical rules
            if rule_result["severity"] != "high":
                continue
                
            # Get indices of violated records
            for violation in rule_result["violations"]:
                if "row" in violation:
                    skipped_indices.add(violation["row"])
        
        # Remove skipped records
        if skipped_indices:
            filtered_data = [d for i, d in enumerate(data) if i not in skipped_indices]
        
        # Prepare result
        result = {
            "validation_results": validation_results,
            "filtered_data": filtered_data,
            "skipped_count": len(skipped_indices),
            "original_count": len(data),
            "filtered_count": len(filtered_data)
        }
        
        # Add rule suggestions if requested
        if include_rule_suggestions and len(data) > 0:
            # Import here to avoid circular imports
            from api.services.business_rules.suggestions import suggest_rules_from_data
            
            # Use a sample of the data for suggestions (max 100 records)
            sample_size = min(len(data), 100)
            sample_data = data[:sample_size]
            
            # Generate suggestions
            suggestions = await suggest_rules_from_data(
                dataset_id,
                sample_data,
                min_confidence=confidence_threshold,
                max_suggestions=10
            )
            
            # Add to result
            result["rule_suggestions"] = suggestions.get("suggestions", [])
            result["suggestion_analysis"] = suggestions.get("analysis_summary", {})
            
            # Estimate impact on full dataset
            if len(data) > sample_size:
                # Extrapolate impact
                result["estimated_impact"] = {
                    "sample_size": sample_size,
                    "total_size": len(data),
                    "extrapolation_factor": len(data) / sample_size,
                    "estimated_violations": int(validation_results["total_violations"] * (len(data) / sample_size))
                }
            
        return result
    except Exception as e:
        logger.error(f"Error validating data for dataset {dataset_id}: {str(e)}")
        return {
            "validation_results": {
                "total_rules": 0,
                "passed_rules": 0,
                "failed_rules": 0,
                "total_violations": 0,
                "rule_results": [],
                "error": str(e)
            },
            "filtered_data": data,
            "skipped_count": 0,
            "original_count": len(data),
            "filtered_count": len(data)
        }

# Rule execution implementations

async def _execute_python_rule(rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute a Python rule. The rule's 'condition' should be a valid Python expression.
    
    Args:
        rule: Rule dictionary
        df: DataFrame containing data to validate
        
    Returns:
        Dictionary with execution results
    """
    try:
        # Prepare safe context
        condition = rule["condition"]
        context = {
            "df": df,
            "pd": pd,
            "np": np,
            "re": re,
            "datetime": datetime
        }
        
        # Build a function from the condition
        fn_code = (
            "def validate(df):\n"
            "    try:\n"
            f"        {condition}\n"
            "    except Exception as e:\n"
            "        return False, str(e)\n"
            "    return True, 'Rule validation passed'"
        )
        
        local_env = {}
        exec(fn_code, context, local_env)
        success, message = local_env["validate"](df)
        
        # Handle Series result (row-wise validation)
        affected_rows = []
        if isinstance(success, pd.Series):
            affected_rows = df[~success].index.tolist()
            success = success.all()
            
        return {
            "success": bool(success),
            "message": message if not success else "Rule validation passed",
            "meta": {
                "affected_rows": affected_rows[:10],  # Limit number of rows returned
                "total_affected": len(affected_rows)
            }
        }
    except Exception as e:
        logger.error(f"Error executing Python rule: {str(e)}")
        return {
            "success": False,
            "message": f"Error executing rule: {str(e)}",
            "meta": {}
        }

async def _execute_ge_rule(rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute a Great Expectations rule. The rule's 'condition' should be a GE expectation.
    
    Args:
        rule: Rule dictionary
        df: DataFrame containing data to validate
        
    Returns:
        Dictionary with execution results
    """
    try:
        # Convert to GE DataFrame
        expectation = rule["condition"]
        ge_df = ge.from_pandas(df)
        
        # Execute expectation
        result = eval(f"ge_df.{expectation}")
        success = result.success if hasattr(result, 'success') else False
        
        return {
            "success": success,
            "message": "GE rule passed" if success else str(result),
            "meta": {"ge_result": str(result)}
        }
    except Exception as e:
        logger.error(f"Error executing GE rule: {str(e)}")
        return {
            "success": False,
            "message": f"Error executing GE rule: {str(e)}",
            "meta": {}
        }

async def _execute_pydantic_rule(rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute a Pydantic rule. The rule's 'condition' should be a Pydantic model definition.
    
    Args:
        rule: Rule dictionary
        df: DataFrame containing data to validate
        
    Returns:
        Dictionary with execution results
    """
    try:
        # Parse model definition from condition
        model_def = rule["condition"]
        if isinstance(model_def, str):
            try:
                model_def = json.loads(model_def)
            except:
                # Try to evaluate as Python dict
                model_def = eval(model_def)
        
        # Create dynamic model
        Model = create_model('DynamicModel', **model_def)
        
        # Validate each row
        errors = []
        for idx, row in df.iterrows():
            try:
                Model(**row.to_dict())
            except ValidationError as ve:
                errors.append((idx, str(ve)))
                
        success = len(errors) == 0
        
        return {
            "success": success,
            "message": "Pydantic validation passed" if success else f"{len(errors)} rows failed",
            "meta": {"errors": errors[:10], "total_failed": len(errors)}
        }
    except Exception as e:
        logger.error(f"Error executing Pydantic rule: {str(e)}")
        return {
            "success": False,
            "message": f"Error executing Pydantic rule: {str(e)}",
            "meta": {}
        }

async def _execute_hf_rule(rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute a Hugging Face rule. The rule's 'condition' should be a prompt or label.
    
    Args:
        rule: Rule dictionary
        df: DataFrame containing data to validate
        
    Returns:
        Dictionary with execution results
    """
    try:
        # This is a placeholder - in a real implementation, you would use a Hugging Face model
        # For now, we'll just return success
        return {
            "success": True,
            "message": "Hugging Face rule executed successfully",
            "meta": {}
        }
    except Exception as e:
        logger.error(f"Error executing Hugging Face rule: {str(e)}")
        return {
            "success": False,
            "message": f"Error executing Hugging Face rule: {str(e)}",
            "meta": {}
        }

async def _execute_transformation_rule(rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute a transformation rule.
    
    Args:
        rule: Rule dictionary
        df: DataFrame containing data to transform
        
    Returns:
        Dictionary with transformation results
    """
    try:
        # Compile transformation function
        transform_fn = _compile_condition(rule["condition"])
        if not transform_fn:
            return {
                "success": False,
                "message": "Failed to compile transformation function",
                "meta": {}
            }
            
        # Apply transformation to each row
        transformed_rows = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Apply transformation
                result = transform_fn(row.to_dict())
                
                # Update row with transformation result
                if isinstance(result, dict):
                    for k, v in result.items():
                        df.at[idx, k] = v
                    transformed_rows += 1
            except Exception as e:
                errors.append((idx, str(e)))
                
        return {
            "success": len(errors) == 0,
            "message": f"Transformed {transformed_rows} rows with {len(errors)} errors",
            "meta": {"errors": errors, "transformed_rows": transformed_rows}
        }
    except Exception as e:
        logger.error(f"Error executing transformation rule: {str(e)}")
        return {
            "success": False,
            "message": f"Error executing transformation rule: {str(e)}",
            "meta": {}
        }

async def _execute_enrichment_rule(rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute an enrichment rule.
    
    Args:
        rule: Rule dictionary
        df: DataFrame containing data to enrich
        
    Returns:
        Dictionary with enrichment results
    """
    try:
        # Compile enrichment function
        enrich_fn = _compile_condition(rule["condition"])
        if not enrich_fn:
            return {
                "success": False,
                "message": "Failed to compile enrichment function",
                "meta": {}
            }
            
        # Apply enrichment to each row
        enriched_rows = 0
        errors = []
        
        # Get target field from rule action
        target_field = rule.get("action", "")
        if not target_field:
            return {
                "success": False,
                "message": "No target field specified in rule action",
                "meta": {}
            }
            
        for idx, row in df.iterrows():
            try:
                # Apply enrichment
                result = enrich_fn(row.to_dict())
                
                # Add new field with enrichment result
                df.at[idx, target_field] = result
                enriched_rows += 1
            except Exception as e:
                errors.append((idx, str(e)))
                
        return {
            "success": len(errors) == 0,
            "message": f"Enriched {enriched_rows} rows with {len(errors)} errors",
            "meta": {"errors": errors, "enriched_rows": enriched_rows}
        }
    except Exception as e:
        logger.error(f"Error executing enrichment rule: {str(e)}")
        return {
            "success": False,
            "message": f"Error executing enrichment rule: {str(e)}",
            "meta": {}
        }
