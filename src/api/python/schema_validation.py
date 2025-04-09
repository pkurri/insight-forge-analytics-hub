
"""
Schema Validation Module

This module provides functionality for validating data against schemas
using Pydantic. It helps ensure data quality and consistency.

In a production environment, this would be deployed as an API endpoint or microservice.
"""

import pandas as pd
import json
from typing import Dict, List, Any, Union, Optional, Type, get_type_hints
import logging
from pydantic import BaseModel, ValidationError, create_model, validator
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaValidator:
    """Class for validating data against schemas"""
    
    def __init__(self):
        """Initialize the schema validator"""
        logger.info("SchemaValidator initialized")
    
    def validate_dataframe(self, 
                         data: pd.DataFrame, 
                         schema_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a pandas DataFrame against a schema definition
        
        Args:
            data: Pandas DataFrame containing the dataset to validate
            schema_def: Dictionary defining the schema with field types and constraints
            
        Returns:
            Dictionary containing validation results
        """
        try:
            # Generate a Pydantic model from the schema definition
            model = self._create_pydantic_model(schema_def)
            
            # Track validation results
            valid_rows = 0
            invalid_rows = 0
            validation_errors = []
            
            # Validate each row
            for index, row in data.iterrows():
                try:
                    # Convert row to dict and validate
                    row_dict = row.to_dict()
                    model(**row_dict)
                    valid_rows += 1
                except ValidationError as e:
                    invalid_rows += 1
                    
                    # Format error for easier consumption
                    errors = []
                    for error in e.errors():
                        errors.append({
                            "field": ".".join(str(loc) for loc in error["loc"]),
                            "error": error["msg"],
                            "value": str(error.get("input", ""))
                        })
                    
                    validation_errors.append({
                        "row_index": int(index),
                        "errors": errors
                    })
                    
                    # Limit to 100 errors for performance
                    if len(validation_errors) >= 100:
                        break
            
            return {
                "success": True,
                "summary": {
                    "total_rows": len(data),
                    "valid_rows": valid_rows,
                    "invalid_rows": invalid_rows,
                    "validation_rate": (valid_rows / len(data) * 100) if len(data) > 0 else 0
                },
                "errors": validation_errors,
                "schema": schema_def
            }
            
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_pydantic_model(self, schema_def: Dict[str, Any]) -> Type[BaseModel]:
        """Create a Pydantic model from a schema definition"""
        field_types = {}
        validators = {}
        
        for field_name, field_config in schema_def.items():
            # Get field type
            field_type = self._get_python_type(field_config.get("type", "string"))
            
            # Handle required vs optional fields
            if not field_config.get("required", True):
                field_type = Optional[field_type]
                
            # Add field to model
            field_types[field_name] = (field_type, ...)
            
            # Add constraints as validators
            constraints = field_config.get("constraints", {})
            if constraints:
                validator_name = f"validate_{field_name}"
                
                # Create validator function dynamically
                def make_validator(field, constraints):
                    def validate_field(cls, value):
                        if value is None and not field_config.get("required", True):
                            return None
                            
                        if "min" in constraints and value < constraints["min"]:
                            raise ValueError(
                                f"Value must be >= {constraints['min']}"
                            )
                            
                        if "max" in constraints and value > constraints["max"]:
                            raise ValueError(
                                f"Value must be <= {constraints['max']}"
                            )
                            
                        if "min_length" in constraints and len(str(value)) < constraints["min_length"]:
                            raise ValueError(
                                f"Length must be >= {constraints['min_length']}"
                            )
                            
                        if "max_length" in constraints and len(str(value)) > constraints["max_length"]:
                            raise ValueError(
                                f"Length must be <= {constraints['max_length']}"
                            )
                            
                        if "regex" in constraints:
                            import re
                            pattern = constraints["regex"]
                            if not re.match(pattern, str(value)):
                                raise ValueError(
                                    f"Value must match pattern: {pattern}"
                                )
                                
                        if "allowed_values" in constraints and value not in constraints["allowed_values"]:
                            raise ValueError(
                                f"Value must be one of: {constraints['allowed_values']}"
                            )
                            
                        return value
                    
                    return validate_field
                
                validators[validator_name] = validator(field_name)(make_validator(field_name, constraints))
        
        # Create model dynamically
        model_name = schema_def.get("name", "DataModel")
        
        # Create the model class
        model = create_model(
            model_name,
            **field_types
        )
        
        # Add validators to the model
        for name, func in validators.items():
            setattr(model, name, func)
            
        return model
    
    def _get_python_type(self, type_str: str) -> Type:
        """Convert schema type string to Python type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "date": datetime,
            "array": list,
            "object": dict
        }
        
        return type_mapping.get(type_str.lower(), str)
    
    def infer_schema(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Infer a schema from a pandas DataFrame
        
        Args:
            data: Pandas DataFrame to infer schema from
            
        Returns:
            Dictionary containing the inferred schema
        """
        try:
            schema = {
                "name": "InferredSchema",
                "fields": {}
            }
            
            for column in data.columns:
                # Get column type
                dtype = data[column].dtype
                dtype_name = dtype.name
                
                # Determine field type
                if pd.api.types.is_integer_dtype(dtype):
                    field_type = "integer"
                elif pd.api.types.is_float_dtype(dtype):
                    field_type = "number"
                elif pd.api.types.is_bool_dtype(dtype):
                    field_type = "boolean"
                elif pd.api.types.is_datetime64_dtype(dtype):
                    field_type = "date"
                else:
                    field_type = "string"
                
                # Create field definition with constraints
                field_def = {
                    "type": field_type,
                    "required": not data[column].isna().any()
                }
                
                # Add constraints based on data
                constraints = {}
                
                if field_type in ["integer", "number"]:
                    non_null = data[column].dropna()
                    if len(non_null) > 0:
                        constraints["min"] = float(non_null.min())
                        constraints["max"] = float(non_null.max())
                
                elif field_type == "string":
                    non_null = data[column].dropna()
                    if len(non_null) > 0:
                        str_lengths = non_null.astype(str).str.len()
                        constraints["min_length"] = int(str_lengths.min())
                        constraints["max_length"] = int(str_lengths.max())
                        
                        # Check if column might be categorical
                        unique_ratio = len(non_null.unique()) / len(non_null)
                        if unique_ratio < 0.1 and len(non_null.unique()) < 20:
                            constraints["allowed_values"] = non_null.unique().tolist()
                
                if constraints:
                    field_def["constraints"] = constraints
                
                schema["fields"][column] = field_def
            
            return {
                "success": True,
                "schema": schema
            }
            
        except Exception as e:
            logger.error(f"Error inferring schema: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage (would be called via API endpoint in production)
if __name__ == "__main__":
    import json
    
    # Create sample data
    data = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie', None],
        'age': [25, 30, -5, 40],  # -5 is invalid
        'email': ['alice@example.com', 'invalid-email', 'charlie@example.com', 'david@example.com']
    })
    
    # Define schema
    schema = {
        "name": "PersonSchema",
        "fields": {
            "name": {
                "type": "string",
                "required": True,
                "constraints": {
                    "min_length": 2,
                    "max_length": 100
                }
            },
            "age": {
                "type": "integer",
                "required": True,
                "constraints": {
                    "min": 0,
                    "max": 120
                }
            },
            "email": {
                "type": "string",
                "required": True,
                "constraints": {
                    "regex": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
                }
            }
        }
    }
    
    # Validate data
    validator = SchemaValidator()
    results = validator.validate_dataframe(data, schema)
    
    # Output summary
    print(json.dumps(results["summary"], indent=2))
    print(f"Found {len(results['errors'])} validation errors")
    
    # Infer schema
    inferred_schema = validator.infer_schema(data)
    print("\nInferred Schema:")
    print(json.dumps(inferred_schema["schema"], indent=2))
