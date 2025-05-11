"""
Business Rules Generators Module

This module provides functions for generating business rules using different engines:
- AI-based rule generation
- Great Expectations rule generation
- Pydantic model rule generation
- Hugging Face model rule generation
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union, Callable
import uuid
from datetime import datetime
import pandas as pd
import numpy as np
import re
import great_expectations as ge
from pydantic import create_model, Field, validator
from functools import partial

from api.config.settings import get_settings
from api.utils.openai_client import get_openai_client
from services.internal_ai_service import generate_text_internal

# Try to import greater_expectations if available
try:
    import greater_expectations as gx
    from greater_expectations.expectations.core import ExpectColumnValuesToBeUnique
    from greater_expectations.expectations.core import ExpectColumnValuesToNotBeNull
    from greater_expectations.expectations.core import ExpectColumnValuesToBeBetween
    from greater_expectations.expectations.core import ExpectColumnValuesToMatchRegex
    GREATER_EXPECTATIONS_AVAILABLE = True
except ImportError:
    GREATER_EXPECTATIONS_AVAILABLE = False

settings = get_settings()
logger = logging.getLogger(__name__)

# Rule generation engines
RULE_ENGINES = {
    "ai_default": "_generate_rules_with_ai",
    "great_expectations": "_generate_rules_with_ge",
    "pydantic": "_generate_rules_with_pydantic",
    "huggingface": "_generate_rules_with_hf",
    "greater_expressions": "_generate_rules_with_greater_expressions"
}

async def generate_rules_with_engine(
    dataset_id: str,
    column_meta: Dict[str, Any],
    engine: str = "ai_default",
    model_type: str = None
) -> Dict[str, Any]:
    """Generate business rules using different AI engines based on column meta.
    
    Args:
        dataset_id: ID of the dataset to generate rules for
        column_meta: Dictionary containing column information about the dataset
        engine: AI engine to use for rule generation
        model_type: Type of model to use for generation
        
    Returns:
        Dictionary containing generated rules and meta
    """
    try:
        # Validate engine parameter
        valid_engines = ["huggingface", "pydantic", "great_expectations", "ai_default", "greater_expressions"]
        if engine not in valid_engines:
            logger.warning(f"Invalid engine '{engine}', defaulting to 'ai_default'")
            engine = "ai_default"
            
        logger.info(f"Generating business rules using {engine} engine for dataset {dataset_id}")
        
        # Generate rules based on the selected engine
        if engine == "huggingface":
            return await generate_huggingface_rules(dataset_id, column_meta)
        elif engine == "pydantic":
            return await generate_pydantic_rules(dataset_id, column_meta)
        elif engine == "great_expectations":
            return await generate_great_expectations_rules(dataset_id, column_meta)
        elif engine == "greater_expressions":
            return await generate_greater_expressions_rules(dataset_id, column_meta)
        else:  # ai_default
            # Only allow internal models
            allowed_models = getattr(settings, "ALLOWED_TEXT_GEN_MODELS", ["Mistral-3.2-instruct"])
            if not model_type or model_type not in allowed_models:
                model_type = allowed_models[0]

            # Use internal text generation models
            prompt = build_prompt(column_meta)
            generated = await generate_text_internal(prompt, model=model_type)
            # Parse the generated text into rules
            return {"rules": generated, "meta": {"model": model_type, "source": "ai_default"}}
    except Exception as e:
        logger.error(f"Error generating AI rules with {engine} engine: {str(e)}")
        return {"success": False, "error": str(e)}

async def generate_huggingface_rules(dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Generate business rules using Hugging Face models."""
    try:
        prompt = f"""Generate business rules for data validation using Hugging Face models.
        Dataset columns: {json.dumps(column_meta, indent=2)}
        Generate 3-5 business rules that would be useful for validating this data.
        Each rule should include name, description, condition (as a Python expression), severity (low/medium/high), and message.
        """
        
        # Use internal text generation as a placeholder for actual Hugging Face API call
        generated = await generate_text_internal(prompt)
        
        # Process the generated rules to ensure they have the source field
        if isinstance(generated, list):
            for rule in generated:
                if isinstance(rule, dict):
                    rule["source"] = "huggingface"
        
        return {"rules": generated, "meta": {"source": "huggingface"}}
    except Exception as e:
        logger.error(f"Error generating Hugging Face rules: {str(e)}")
        return {"success": False, "error": str(e)}

async def generate_pydantic_rules(dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Generate business rules using Pydantic models."""
    try:
        rules = []
        
        # Generate rules based on column types and constraints
        for col_name, col_info in column_meta.items():
            # Skip if no type information
            if not col_info.get("type"):
                continue
                
            col_type = col_info.get("type").lower()
            
            # Generate type validation rules
            if col_type in ["int", "integer", "float", "number"]:
                # Numeric validation
                rules.append({
                    "name": f"{col_name} Type Validation",
                    "description": f"Validates that {col_name} contains only {col_type} values",
                    "condition": f"df['{col_name}'].apply(lambda x: isinstance(x, {col_type}) if pd.notna(x) else True).all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain only {col_type} values",
                    "source": "pydantic"
                })
                
                # Add range validation if min/max are provided
                if "min" in col_info and "max" in col_info:
                    rules.append({
                        "name": f"{col_name} Range Validation",
                        "description": f"Validates that {col_name} values are within the allowed range",
                        "condition": f"df[df['{col_name}'].notna()]['{col_name}'].between({col_info['min']}, {col_info['max']}).all()",
                        "severity": "medium",
                        "message": f"Column {col_name} values must be between {col_info['min']} and {col_info['max']}",
                        "source": "pydantic"
                    })
                    
            elif col_type in ["str", "string", "text"]:
                # String validation
                rules.append({
                    "name": f"{col_name} Type Validation",
                    "description": f"Validates that {col_name} contains only string values",
                    "condition": f"df['{col_name}'].apply(lambda x: isinstance(x, str) if pd.notna(x) else True).all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain only string values",
                    "source": "pydantic"
                })
                
                # Add length validation if max_length is provided
                if "max_length" in col_info:
                    rules.append({
                        "name": f"{col_name} Length Validation",
                        "description": f"Validates that {col_name} values don't exceed the maximum length",
                        "condition": f"df[df['{col_name}'].notna()]['{col_name}'].str.len().max() <= {col_info['max_length']}",
                        "severity": "medium",
                        "message": f"Column {col_name} values must not exceed {col_info['max_length']} characters",
                        "source": "pydantic"
                    })
                    
            elif col_type in ["date", "datetime"]:
                # Date validation
                rules.append({
                    "name": f"{col_name} Date Validation",
                    "description": f"Validates that {col_name} contains valid date values",
                    "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').notna().all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain valid date values",
                    "source": "pydantic"
                })
            
            # Add not-null validation if required
            if col_info.get("required", False):
                rules.append({
                    "name": f"{col_name} Required Validation",
                    "description": f"Validates that {col_name} does not contain null values",
                    "condition": f"df['{col_name}'].notna().all()",
                    "severity": "high",
                    "message": f"Column {col_name} must not contain null values",
                    "source": "pydantic"
                })
        
        return {"rules": rules, "meta": {"source": "pydantic"}}
    except Exception as e:
        logger.error(f"Error generating Pydantic rules: {str(e)}")
        return {"success": False, "error": str(e)}

async def generate_great_expectations_rules(dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Generate business rules using Great Expectations."""
    try:
        rules = []
        
        # Generate rules based on column types and common validation patterns
        for col_name, col_info in column_meta.items():
            # Skip if no type information
            if not col_info.get("type"):
                continue
                
            col_type = col_info.get("type").lower()
            
            # Column existence check
            rules.append({
                "name": f"Expect {col_name} to exist",
                "description": f"Validates that column {col_name} exists in the dataset",
                "condition": f"'{col_name}' in df.columns",
                "severity": "high",
                "message": f"Column {col_name} must exist in the dataset",
                "source": "great_expectations"
            })
            
            # Type-specific validations
            if col_type in ["int", "integer", "float", "number"]:
                # Numeric validation
                rules.append({
                    "name": f"Expect {col_name} values to be valid numbers",
                    "description": f"Validates that {col_name} contains valid numeric values",
                    "condition": f"pd.to_numeric(df['{col_name}'], errors='coerce').notna().all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain valid numeric values",
                    "source": "great_expectations"
                })
                
                # Statistical validations
                rules.append({
                    "name": f"Expect {col_name} values to be reasonable",
                    "description": f"Validates that {col_name} values are within a reasonable range (not extreme outliers)",
                    "condition": f"(df['{col_name}'] - df['{col_name}'].mean()).abs() <= 3 * df['{col_name}'].std()",
                    "severity": "medium",
                    "message": f"Column {col_name} contains outlier values that are more than 3 standard deviations from the mean",
                    "source": "great_expectations"
                })
                
            elif col_type in ["str", "string", "text"]:
                # String validation
                rules.append({
                    "name": f"Expect {col_name} values to be strings",
                    "description": f"Validates that {col_name} contains string values",
                    "condition": f"df['{col_name}'].apply(lambda x: isinstance(x, str) if pd.notna(x) else True).all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain string values",
                    "source": "great_expectations"
                })
                
                # Non-empty string validation
                rules.append({
                    "name": f"Expect {col_name} values to not be empty strings",
                    "description": f"Validates that {col_name} does not contain empty strings",
                    "condition": f"df[df['{col_name}'].notna()]['{col_name}'].str.strip().str.len().gt(0).all()",
                    "severity": "medium",
                    "message": f"Column {col_name} must not contain empty strings",
                    "source": "great_expectations"
                })
                
            elif col_type in ["date", "datetime"]:
                # Date validation
                rules.append({
                    "name": f"Expect {col_name} values to be valid dates",
                    "description": f"Validates that {col_name} contains valid date values",
                    "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').notna().all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain valid date values",
                    "source": "great_expectations"
                })
                
                # Future date validation
                rules.append({
                    "name": f"Expect {col_name} values to not be in the future",
                    "description": f"Validates that {col_name} does not contain future dates",
                    "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').dt.date.max() <= pd.Timestamp.now().date()",
                    "severity": "medium",
                    "message": f"Column {col_name} must not contain future dates",
                    "source": "great_expectations"
                })
            
            # Completeness validation (applicable to all types)
            rules.append({
                "name": f"Expect {col_name} to be at least 95% complete",
                "description": f"Validates that {col_name} has at least 95% non-null values",
                "condition": f"df['{col_name}'].notna().mean() >= 0.95",
                "severity": "medium",
                "message": f"Column {col_name} must be at least 95% complete (non-null)",
                "source": "great_expectations"
            })
        
        return {"rules": rules, "meta": {"source": "great_expectations"}}
    except Exception as e:
        logger.error(f"Error generating Great Expectations rules: {str(e)}")
        return {"success": False, "error": str(e)}

async def generate_greater_expressions_rules(dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Generate business rules using Greater Expectations."""
    try:
        rules = []
        
        # Generate rules based on column types and common validation patterns
        for col_name, col_info in column_meta.items():
            # Skip if no type information
            if not col_info.get("type"):
                continue
                
            col_type = col_info.get("type").lower()
            
            # Column existence check
            rules.append({
                "name": f"Expect {col_name} to exist",
                "description": f"Validates that column {col_name} exists in the dataset",
                "condition": f"'{col_name}' in df.columns",
                "severity": "high",
                "message": f"Column {col_name} must exist in the dataset",
                "source": "greater_expressions"
            })
            
            # Type-specific validations
            if col_type in ["int", "integer", "float", "number"]:
                # Numeric validation
                rules.append({
                    "name": f"Expect {col_name} values to be valid numbers",
                    "description": f"Validates that {col_name} contains valid numeric values",
                    "condition": f"pd.to_numeric(df['{col_name}'], errors='coerce').notna().all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain valid numeric values",
                    "source": "greater_expressions"
                })
                
                # Statistical validations
                rules.append({
                    "name": f"Expect {col_name} values to be reasonable",
                    "description": f"Validates that {col_name} values are within a reasonable range (not extreme outliers)",
                    "condition": f"(df['{col_name}'] - df['{col_name}'].mean()).abs() <= 3 * df['{col_name}'].std()",
                    "severity": "medium",
                    "message": f"Column {col_name} contains outlier values that are more than 3 standard deviations from the mean",
                    "source": "greater_expressions"
                })
                
            elif col_type in ["str", "string", "text"]:
                # String validation
                rules.append({
                    "name": f"Expect {col_name} values to be strings",
                    "description": f"Validates that {col_name} contains string values",
                    "condition": f"df['{col_name}'].apply(lambda x: isinstance(x, str) if pd.notna(x) else True).all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain string values",
                    "source": "greater_expressions"
                })
                
                # Non-empty string validation
                rules.append({
                    "name": f"Expect {col_name} values to not be empty strings",
                    "description": f"Validates that {col_name} does not contain empty strings",
                    "condition": f"df[df['{col_name}'].notna()]['{col_name}'].str.strip().str.len().gt(0).all()",
                    "severity": "medium",
                    "message": f"Column {col_name} must not contain empty strings",
                    "source": "greater_expressions"
                })
                
            elif col_type in ["date", "datetime"]:
                # Date validation
                rules.append({
                    "name": f"Expect {col_name} values to be valid dates",
                    "description": f"Validates that {col_name} contains valid date values",
                    "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').notna().all()",
                    "severity": "high",
                    "message": f"Column {col_name} must contain valid date values",
                    "source": "greater_expressions"
                })
                
                # Future date validation
                rules.append({
                    "name": f"Expect {col_name} values to not be in the future",
                    "description": f"Validates that {col_name} does not contain future dates",
                    "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').dt.date.max() <= pd.Timestamp.now().date()",
                    "severity": "medium",
                    "message": f"Column {col_name} must not contain future dates",
                    "source": "greater_expressions"
                })
            
            # Completeness validation (applicable to all types)
            rules.append({
                "name": f"Expect {col_name} to be at least 95% complete",
                "description": f"Validates that {col_name} has at least 95% non-null values",
                "condition": f"df['{col_name}'].notna().mean() >= 0.95",
                "severity": "medium",
                "message": f"Column {col_name} must be at least 95% complete (non-null)",
                "source": "greater_expressions"
            })
        
        return {"rules": rules, "meta": {"source": "greater_expressions"}}
    except Exception as e:
        logger.error(f"Error generating Greater Expectations rules: {str(e)}")
        return {"success": False, "error": str(e)}

def build_prompt(column_meta: Dict[str, Any]) -> str:
    """Build a prompt for AI rule generation based on column metadata."""
    prompt = f"""Generate business rules for data validation based on the following column information:

{json.dumps(column_meta, indent=2)}

Generate 3-5 business rules that would be useful for validating this data.
Each rule should include:
1. name: A descriptive name for the rule
2. description: A clear description of what the rule validates
3. condition: A Python expression that can be evaluated on a pandas DataFrame
4. severity: The severity level (low/medium/high)
5. message: The error message to show when the rule fails

Focus on:
- Data type validation
- Range/format validation
- Completeness checks
- Business logic validation
- Data quality rules

Return the rules as a JSON array of objects.
"""
    return prompt

async def _create_generated_rules(dataset_id: str, rules: List[Dict[str, Any]]) -> int:
    """
    Create rules from generated rule definitions.
    
    Args:
        dataset_id: ID of the dataset
        rules: List of rule definitions
        
    Returns:
        Number of rules created
    """
    try:
        # Import here to avoid circular imports
        from api.services.business_rules.core import BusinessRulesService
        business_rules_service = BusinessRulesService()
        
        # Create each rule
        created_count = 0
        for rule in rules:
            try:
                # Add dataset ID and defaults
                rule["dataset_id"] = dataset_id
                rule["model_generated"] = True
                rule["created_at"] = datetime.utcnow().isoformat()
                rule["updated_at"] = datetime.utcnow().isoformat()
                rule["id"] = str(uuid.uuid4())
                
                # Create rule
                await business_rules_service.create_rule(rule)
                created_count += 1
            except Exception as rule_error:
                logger.error(f"Error creating generated rule: {str(rule_error)}")
                
        return created_count
    except Exception as e:
        logger.error(f"Error creating generated rules: {str(e)}")
        return 0

async def _generate_rules_with_ai(
    dataset_id: str, 
    column_meta: Dict[str, Any], 
    model_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate business rules using AI.
    
    Args:
        dataset_id: ID of the dataset to generate rules for
        column_meta: Dictionary containing column information about the dataset
        model_type: Type of model to use for generation
        
    Returns:
        Dictionary containing generated rules and meta
    """
    try:
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            return {
                "success": False,
                "error": "OpenAI client not available"
            }
            
        # Prepare prompt
        columns = column_meta.get("columns", [])
        column_descriptions = []
        
        for col in columns:
            col_name = col.get("name", "")
            col_type = col.get("type", "")
            col_desc = col.get("description", "")
            col_stats = col.get("stats", {})
            
            # Format column description
            desc = f"Column: {col_name}\n"
            desc += f"Type: {col_type}\n"
            if col_desc:
                desc += f"Description: {col_desc}\n"
                
            # Add basic stats if available
            if col_stats:
                desc += "Statistics:\n"
                for stat, value in col_stats.items():
                    desc += f"- {stat}: {value}\n"
                    
            column_descriptions.append(desc)
            
        # Build prompt
        prompt = f"""
        Generate business rules for a dataset with the following columns:
        
        {'\n\n'.join(column_descriptions)}
        
        For each column, suggest validation rules that would help ensure data quality.
        Rules should be in Python syntax using pandas DataFrame operations.
        
        For each rule, provide:
        1. A descriptive name
        2. A clear description of what the rule validates
        3. The rule condition as a Python expression using 'df' as the DataFrame
        4. The severity (low, medium, high)
        5. Tags for categorization
        
        Format each rule as a JSON object.
        """
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model=model_type or "gpt-4",
            messages=[
                {"role": "system", "content": "You are a data quality expert specializing in business rules generation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse response
        content = response.choices[0].message.content
        
        # Extract JSON objects from response
        rules_json = []
        json_pattern = r'\{[\s\S]*?\}'
        matches = re.finditer(json_pattern, content)
        
        for match in matches:
            try:
                rule = json.loads(match.group(0))
                rules_json.append(rule)
            except json.JSONDecodeError:
                continue
                
        # If no rules found, try to parse the whole response
        if not rules_json:
            try:
                rules_json = json.loads(content)
                if not isinstance(rules_json, list):
                    rules_json = [rules_json]
            except json.JSONDecodeError:
                pass
                
        # Process and validate rules
        rules = []
        for rule in rules_json:
            # Add required fields
            rule["source"] = "ai"
            rule["rule_type"] = rule.get("rule_type", "validation")
            rule["severity"] = rule.get("severity", "medium")
            rule["active"] = True
            rule["model_generated"] = True
            
            # Validate rule
            if "name" in rule and "condition" in rule:
                rules.append(rule)
                
        return {
            "success": True,
            "rules": rules,
            "auto_create": True,
            "engine": "ai",
            "model": model_type or "gpt-4"
        }
    except Exception as e:
        logger.error(f"Error generating rules with AI: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def _generate_rules_with_ge(
    dataset_id: str, 
    column_meta: Dict[str, Any], 
    model_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate business rules using Great Expectations.
    
    Args:
        dataset_id: ID of the dataset to generate rules for
        column_meta: Dictionary containing column information about the dataset
        model_type: Type of model to use for generation
        
    Returns:
        Dictionary containing generated rules and meta
    """
    try:
        # Get column information
        columns = column_meta.get("columns", [])
        rules = []
        
        # Generate rules for each column
        for col in columns:
            col_name = col.get("name", "")
            col_type = col.get("type", "")
            col_stats = col.get("stats", {})
            
            # Skip if no name or type
            if not col_name or not col_type:
                continue
                
            # Generate rules based on column type
            if col_type in ["int", "integer", "float", "double", "numeric"]:
                # Numeric column rules
                
                # Not null rule
                rules.append({
                    "name": f"{col_name} not null",
                    "description": f"Ensures {col_name} is not null",
                    "condition": f"expect_column_values_to_not_be_null('{col_name}')",
                    "rule_type": "validation",
                    "severity": "high",
                    "source": "great_expectations",
                    "tags": ["not_null", col_type]
                })
                
                # Range rule if min/max available
                if "min" in col_stats and "max" in col_stats:
                    min_val = col_stats["min"]
                    max_val = col_stats["max"]
                    
                    rules.append({
                        "name": f"{col_name} in range",
                        "description": f"Ensures {col_name} is between {min_val} and {max_val}",
                        "condition": f"expect_column_values_to_be_between('{col_name}', {min_val}, {max_val})",
                        "rule_type": "validation",
                        "severity": "medium",
                        "source": "great_expectations",
                        "tags": ["range", col_type]
                    })
            
            elif col_type in ["string", "text", "varchar"]:
                # String column rules
                
                # Not null rule
                rules.append({
                    "name": f"{col_name} not null",
                    "description": f"Ensures {col_name} is not null",
                    "condition": f"expect_column_values_to_not_be_null('{col_name}')",
                    "rule_type": "validation",
                    "severity": "high",
                    "source": "great_expectations",
                    "tags": ["not_null", col_type]
                })
                
                # Not empty rule
                rules.append({
                    "name": f"{col_name} not empty",
                    "description": f"Ensures {col_name} is not an empty string",
                    "condition": f"expect_column_values_to_not_match_regex('{col_name}', '^\\s*$')",
                    "rule_type": "validation",
                    "severity": "medium",
                    "source": "great_expectations",
                    "tags": ["not_empty", col_type]
                })
                
            elif col_type in ["date", "datetime", "timestamp"]:
                # Date column rules
                
                # Not null rule
                rules.append({
                    "name": f"{col_name} not null",
                    "description": f"Ensures {col_name} is not null",
                    "condition": f"expect_column_values_to_not_be_null('{col_name}')",
                    "rule_type": "validation",
                    "severity": "high",
                    "source": "great_expectations",
                    "tags": ["not_null", col_type]
                })
                
                # Valid date rule
                rules.append({
                    "name": f"{col_name} valid date",
                    "description": f"Ensures {col_name} is a valid date",
                    "condition": f"expect_column_values_to_be_dateutil_parseable('{col_name}')",
                    "rule_type": "validation",
                    "severity": "high",
                    "source": "great_expectations",
                    "tags": ["valid_date", col_type]
                })
                
        return {
            "success": True,
            "rules": rules,
            "auto_create": True,
            "engine": "great_expectations"
        }
    except Exception as e:
        logger.error(f"Error generating rules with Great Expectations: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def _generate_rules_with_pydantic(
    dataset_id: str, 
    column_meta: Dict[str, Any], 
    model_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate business rules using Pydantic models.
    
    Args:
        dataset_id: ID of the dataset to generate rules for
        column_meta: Dictionary containing column information about the dataset
        model_type: Type of model to use for generation
        
    Returns:
        Dictionary containing generated rules and meta
    """
    try:
        # Extract columns from metadata
        columns = column_meta.get("columns", [])
        if not columns:
            return {
                "success": False,
                "error": "No column information provided",
                "rules": []
            }
        
        # Initialize rules list
        rules = []
        
        # Create field definitions for Pydantic model
        field_definitions = {}
        validators = {}
        validator_count = 0
        
        for column in columns:
            col_name = column.get("name")
            col_type = column.get("type")
            col_stats = column.get("stats", {})
            
            # Skip columns without name or type
            if not col_name or not col_type:
                continue
                
            # Map column type to Python/Pydantic type
            py_type = "str"
            if col_type.lower() in ["integer", "int"]:
                py_type = "int"
            elif col_type.lower() in ["float", "double", "decimal"]:
                py_type = "float"
            elif col_type.lower() in ["boolean", "bool"]:
                py_type = "bool"
            elif col_type.lower() in ["date", "datetime"]:
                py_type = "datetime.datetime"
            
            # Create field with validation
            field_args = {}
            
            # Add constraints based on statistics
            if py_type in ["int", "float"]:
                if "min" in col_stats:
                    field_args["ge"] = col_stats["min"]
                if "max" in col_stats:
                    field_args["le"] = col_stats["max"]
                    
                # Add custom validators for numeric fields
                if "mean" in col_stats and "std" in col_stats:
                    # Create outlier detection validator
                    mean_val = col_stats["mean"]
                    std_val = col_stats["std"]
                    lower_bound = mean_val - 3 * std_val
                    upper_bound = mean_val + 3 * std_val
                    
                    # Add rule for outlier detection
                    rules.append({
                        "name": f"{col_name} Outlier Detection",
                        "description": f"Ensures {col_name} is within 3 standard deviations of the mean",
                        "rule_type": "validation",
                        "condition": f"{col_name} BETWEEN {lower_bound:.2f} AND {upper_bound:.2f}",
                        "severity": "low",
                        "source": "pydantic"
                    })
            
            elif py_type == "str":
                if "max_length" in col_stats:
                    field_args["max_length"] = col_stats["max_length"]
                if "pattern" in col_stats:
                    field_args["regex"] = col_stats["pattern"]
                    
                # Add custom validators for string fields
                if "common_values" in col_stats and len(col_stats["common_values"]) <= 10:
                    # Create enumeration validator
                    allowed_values = col_stats["common_values"]
                    allowed_values_str = ", ".join([f"'{v}'" for v in allowed_values])
                    
                    # Add rule for enumeration check
                    rules.append({
                        "name": f"{col_name} Enumeration Check",
                        "description": f"Ensures {col_name} contains only allowed values",
                        "rule_type": "validation",
                        "condition": f"{col_name} IN ({allowed_values_str})",
                        "severity": "medium",
                        "source": "pydantic"
                    })
                
                # Email validator for email-like fields
                if col_name.lower() in ["email", "email_address", "emailaddress"]:
                    rules.append({
                        "name": f"{col_name} Email Format",
                        "description": f"Ensures {col_name} is a valid email address",
                        "rule_type": "validation",
                        "condition": f"{col_name} MATCHES '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'",
                        "severity": "high",
                        "source": "pydantic"
                    })
            
            # Add field to model definition with nullable option if needed
            if col_stats.get("null_count", 0) > 0:
                field_definitions[col_name] = (f"Optional[{py_type}]", Field(None, **field_args))
            else:
                field_definitions[col_name] = (py_type, Field(**field_args))
                
            # Generate rules based on field definition
            if "ge" in field_args:
                rules.append({
                    "name": f"{col_name} Minimum Value",
                    "description": f"Ensures {col_name} is at least {field_args['ge']}",
                    "rule_type": "validation",
                    "condition": f"{col_name} >= {field_args['ge']}",
                    "severity": "medium",
                    "source": "pydantic"
                })
            
            if "le" in field_args:
                rules.append({
                    "name": f"{col_name} Maximum Value",
                    "description": f"Ensures {col_name} is at most {field_args['le']}",
                    "rule_type": "validation",
                    "condition": f"{col_name} <= {field_args['le']}",
                    "severity": "medium",
                    "source": "pydantic"
                })
        
            if "max_length" in field_args:
                rules.append({
                    "name": f"{col_name} Maximum Length",
                    "description": f"Ensures {col_name} length is at most {field_args['max_length']}",
                    "rule_type": "validation",
                    "condition": f"LENGTH({col_name}) <= {field_args['max_length']}",
                    "severity": "medium",
                    "source": "pydantic"
                })
            
            if "regex" in field_args:
                rules.append({
                    "name": f"{col_name} Pattern Match",
                    "description": f"Ensures {col_name} matches pattern {field_args['regex']}",
                    "rule_type": "validation",
                    "condition": f"{col_name} MATCHES '{field_args['regex']}'",
                    "severity": "medium",
                    "source": "pydantic"
                })
            
            # Add not null rule if column has no null values
            if col_stats.get("null_count", 0) == 0:
                rules.append({
                    "name": f"{col_name} Not Null",
                    "description": f"Ensures {col_name} does not contain null values",
                    "rule_type": "validation",
                    "condition": f"{col_name} IS NOT NULL",
                    "severity": "high",
                    "source": "pydantic"
                })
            
        # Create Pydantic model dynamically
        model_name = f"Dataset{dataset_id}Model"
        model_dict = field_definitions.copy()
        
        # Create the model
        try:
            model = create_model(model_name, **model_dict)
            logger.info(f"Created Pydantic model {model_name} with {len(field_definitions)} fields")
        except Exception as model_error:
            logger.error(f"Error creating Pydantic model: {str(model_error)}")
            # Continue with rule generation even if model creation fails
        
        # Create generated rules in the database
        created_count = await _create_generated_rules(dataset_id, rules)
        
        return {
            "success": True,
            "rules": rules,
            "meta": {
                "total_rules": len(rules),
                "created_rules": created_count,
                "model": model_name,
                "engine": "pydantic"
            }
        }
    except Exception as e:
        logger.error(f"Error generating rules with Pydantic: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate rules with Pydantic: {str(e)}",
            "rules": []
        }

async def _generate_rules_with_greater_expressions(
    dataset_id: str, 
    column_meta: Dict[str, Any], 
    model_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate business rules using Greater Expressions.
    
    Args:
        dataset_id: ID of the dataset to generate rules for
        column_meta: Dictionary containing column information about the dataset
        model_type: Type of model to use for generation
        
    Returns:
        Dictionary containing generated rules and meta
    """
    try:
        # Extract columns from metadata
        columns = column_meta.get("columns", [])
        if not columns:
            return {
                "success": False,
                "error": "No column information provided",
                "rules": []
            }
        
        # Initialize rules list
        rules = []
        
        for column in columns:
            col_name = column.get("name")
            col_type = column.get("type")
            col_stats = column.get("stats", {})
            
            # Skip columns without name or type
            if not col_name or not col_type:
                continue
                
            # Column existence check
            rules.append({
                "name": f"Expect {col_name} to exist",
                "description": f"Validates that column {col_name} exists in the dataset",
                "condition": f"'{col_name}' in df.columns",
                "rule_type": "validation",
                "severity": "high",
                "message": f"Column {col_name} must exist in the dataset",
                "source": "greater_expressions"
            })
            
            # Type-specific validations
            if col_type.lower() in ["int", "integer", "float", "number"]:
                # Numeric validation
                rules.append({
                    "name": f"Expect {col_name} values to be valid numbers",
                    "description": f"Validates that {col_name} contains valid numeric values",
                    "condition": f"pd.to_numeric(df['{col_name}'], errors='coerce').notna().all()",
                    "rule_type": "validation",
                    "severity": "high",
                    "message": f"Column {col_name} must contain valid numeric values",
                    "source": "greater_expressions"
                })
                
                # Statistical validations
                rules.append({
                    "name": f"Expect {col_name} values to be reasonable",
                    "description": f"Validates that {col_name} values are within a reasonable range (not extreme outliers)",
                    "condition": f"(df['{col_name}'] - df['{col_name}'].mean()).abs() <= 3 * df['{col_name}'].std()",
                    "rule_type": "validation",
                    "severity": "medium",
                    "message": f"Column {col_name} contains outlier values that are more than 3 standard deviations from the mean",
                    "source": "greater_expressions"
                })
                
            elif col_type.lower() in ["str", "string", "text"]:
                # String validation
                rules.append({
                    "name": f"Expect {col_name} values to be strings",
                    "description": f"Validates that {col_name} contains string values",
                    "condition": f"df['{col_name}'].apply(lambda x: isinstance(x, str) if pd.notna(x) else True).all()",
                    "rule_type": "validation",
                    "severity": "high",
                    "message": f"Column {col_name} must contain string values",
                    "source": "greater_expressions"
                })
                
                # Non-empty string validation
                rules.append({
                    "name": f"Expect {col_name} values to not be empty strings",
                    "description": f"Validates that {col_name} does not contain empty strings",
                    "condition": f"df[df['{col_name}'].notna()]['{col_name}'].str.strip().str.len().gt(0).all()",
                    "rule_type": "validation",
                    "severity": "medium",
                    "message": f"Column {col_name} must not contain empty strings",
                    "source": "greater_expressions"
                })
                
            elif col_type.lower() in ["date", "datetime"]:
                # Date validation
                rules.append({
                    "name": f"Expect {col_name} values to be valid dates",
                    "description": f"Validates that {col_name} contains valid date values",
                    "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').notna().all()",
                    "rule_type": "validation",
                    "severity": "high",
                    "message": f"Column {col_name} must contain valid date values",
                    "source": "greater_expressions"
                })
                
                # Future date validation
                rules.append({
                    "name": f"Expect {col_name} values to not be in the future",
                    "description": f"Validates that {col_name} does not contain future dates",
                    "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').dt.date.max() <= pd.Timestamp.now().date()",
                    "rule_type": "validation",
                    "severity": "medium",
                    "message": f"Column {col_name} must not contain future dates",
                    "source": "greater_expressions"
                })
            
            # Completeness validation (applicable to all types)
            rules.append({
                "name": f"Expect {col_name} to be at least 95% complete",
                "description": f"Validates that {col_name} has at least 95% non-null values",
                "condition": f"df['{col_name}'].notna().mean() >= 0.95",
                "rule_type": "validation",
                "severity": "medium",
                "message": f"Column {col_name} must be at least 95% complete (non-null)",
                "source": "greater_expressions"
            })
        
        # Create generated rules in the database
        created_count = await _create_generated_rules(dataset_id, rules)
        
        return {
            "success": True,
            "rules": rules,
            "meta": {
                "total_rules": len(rules),
                "created_rules": created_count,
                "engine": "greater_expressions"
            }
        }
    except Exception as e:
        logger.error(f"Error generating rules with Greater Expressions: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate rules with Greater Expressions: {str(e)}",
            "rules": []
        }
            
        # Create generated rules in the database
        created_count = await _create_generated_rules(dataset_id, rules)
        
        return {
            "success": True,
            "rules": rules,
            "meta": {
                "total_rules": len(rules),
                "created_rules": created_count,
                "model": model_name,
                "engine": "pydantic"
            }
        }
    except Exception as e:
        logger.error(f"Error generating rules with Pydantic: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate rules with Pydantic: {str(e)}",
            "rules": []
        }
                    
async def _generate_rules_with_hf(
    dataset_id: str, 
    column_meta: Dict[str, Any], 
    model_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate business rules using Hugging Face models.
    
    Args:
        dataset_id: ID of the dataset to generate rules for
        column_meta: Dictionary containing column information about the dataset
        model_type: Type of model to use for generation (e.g., 'text-classification', 'zero-shot', 'table-qa')
        
    Returns:
        Dictionary containing generated rules and meta
    """
    try:
        import torch
        from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
        
        # Default to zero-shot-classification if no model type specified
        model_type = model_type or "zero-shot-classification"
        
        # Get column information
        columns = column_meta.get("columns", [])
        if not columns:
            return {
                "success": False,
                "error": "No column information provided",
                "rules": []
            }
        
        # Initialize rules list
        rules = []
        
        if model_type == "zero-shot-classification":
            # Use zero-shot classification for rule generation
            classifier = pipeline("zero-shot-classification", 
                                 model="facebook/bart-large-mnli",
                                 device=0 if torch.cuda.is_available() else -1)
            
            # Define candidate labels for different rule types
            validation_labels = [
                "not null", "unique", "positive", "negative", "range check", 
                "format validation", "enumeration check", "length check"
            ]
            
            for column in columns:
                col_name = column.get("name")
                col_type = column.get("type")
                col_stats = column.get("stats", {})
                
                # Skip columns without name or type
                if not col_name or not col_type:
                    continue
                
                # Create a description of the column for the model
                column_description = f"Column '{col_name}' with type {col_type}"
                if col_stats:
                    if "min" in col_stats and "max" in col_stats:
                        column_description += f", range from {col_stats['min']} to {col_stats['max']}"
                    if "unique_count" in col_stats and "total_count" in col_stats:
                        unique_ratio = col_stats["unique_count"] / col_stats["total_count"]
                        column_description += f", {col_stats['unique_count']} unique values out of {col_stats['total_count']} ({unique_ratio:.2%})"
                    if "null_count" in col_stats and "total_count" in col_stats:
                        null_ratio = col_stats["null_count"] / col_stats["total_count"]
                        column_description += f", {col_stats['null_count']} null values ({null_ratio:.2%})"
                
                # Use zero-shot classification to determine appropriate rule types
                result = classifier(column_description, validation_labels)
                
                # Generate rules based on the top predictions
                for label, score in zip(result["labels"], result["scores"]):
                    if score > 0.7:  # Only consider high confidence predictions
                        rule = await _create_rule_from_prediction(col_name, col_type, label, col_stats)
                        if rule:
                            rules.append(rule)
        
        elif model_type == "table-qa":
            # Use table question answering for rule generation
            qa_pipeline = pipeline("table-question-answering", 
                                  model="google/tapas-base-finetuned-wtq")
            
            # Create a simplified table representation
            table_data = {
                "Column": [col.get("name") for col in columns],
                "Type": [col.get("type") for col in columns],
                "Null Count": [col.get("stats", {}).get("null_count", "N/A") for col in columns],
                "Unique Count": [col.get("stats", {}).get("unique_count", "N/A") for col in columns]
            }
            
            # Questions to ask about the data
            questions = [
                "Which columns should not allow null values?",
                "Which columns should be unique?",
                "Which numeric columns should have range validations?",
                "Which string columns should have format validations?"
            ]
            
            for question in questions:
                result = qa_pipeline(table=table_data, query=question)
                if result["aggregated_answers"]:
                    answer = result["aggregated_answers"][0]
                    columns_mentioned = [col for col in columns if col.get("name") in answer]
                    
                    for col in columns_mentioned:
                        if "null" in question.lower():
                            rules.append({
                                "name": f"{col.get('name')} Not Null",
                                "description": f"Ensures {col.get('name')} does not contain null values",
                                "rule_type": "validation",
                                "condition": f"{col.get('name')} IS NOT NULL",
                                "severity": "high",
                                "source": "huggingface"
                            })
                        elif "unique" in question.lower():
                            rules.append({
                                "name": f"{col.get('name')} Uniqueness",
                                "description": f"Ensures {col.get('name')} contains only unique values",
                                "rule_type": "validation",
                                "condition": f"{col.get('name')} IS UNIQUE",
                                "severity": "medium",
                                "source": "huggingface"
                            })
                        elif "range" in question.lower() and col.get("type") in ["integer", "float", "number"]:
                            stats = col.get("stats", {})
                            if "min" in stats and "max" in stats:
                                rules.append({
                                    "name": f"{col.get('name')} Range Check",
                                    "description": f"Ensures {col.get('name')} is within expected range",
                                    "rule_type": "validation",
                                    "condition": f"{col.get('name')} BETWEEN {stats['min']} AND {stats['max']}",
                                    "severity": "medium",
                                    "source": "huggingface"
                                })
                        elif "format" in question.lower() and col.get("type") == "string":
                            rules.append({
                                "name": f"{col.get('name')} Format Validation",
                                "description": f"Ensures {col.get('name')} follows expected format",
                                "rule_type": "validation",
                                "condition": f"{col.get('name')} MATCHES '[A-Za-z0-9]+'",
                                "severity": "medium",
                                "source": "huggingface"
                            })
        
        # Create generated rules in the database
        created_count = await _create_generated_rules(dataset_id, rules)
        
        return {
            "success": True,
            "rules": rules,
            "meta": {
                "total_rules": len(rules),
                "created_rules": created_count,
                "model_type": model_type,
                "engine": "huggingface"
            }
        }
    except ImportError as e:
        logger.error(f"Hugging Face libraries not installed: {str(e)}")
        return {
            "success": False,
            "error": "Hugging Face libraries not installed. Please install transformers and torch.",
            "rules": []
        }
    except Exception as e:
        logger.error(f"Error generating rules with Hugging Face: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate rules with Hugging Face: {str(e)}",
            "rules": []
        }
        
        # Create generated rules in the database
        created_count = await _create_generated_rules(dataset_id, rules)
        
        return {
            "success": True,
            "rules": rules,
            "meta": {
                "total_rules": len(rules),
                "created_rules": created_count,
                "model_type": model_type,
                "engine": "huggingface"
            }
        }
    except ImportError as e:
        logger.error(f"Hugging Face libraries not installed: {str(e)}")
        return {
            "success": False,
            "error": "Hugging Face libraries not installed. Please install transformers and torch.",
            "rules": []
        }
    except Exception as e:
        logger.error(f"Error generating rules with Hugging Face: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate rules with Hugging Face: {str(e)}",
            "rules": []
        }
