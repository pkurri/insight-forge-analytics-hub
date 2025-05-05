"""
Business Rules Validators Module

This module provides functions for validating business rule formats and conditions:
- Rule schema validation
- Condition syntax validation
- Rule dependency validation
"""

import logging
import json
import ast
from typing import Dict, List, Any, Optional, Union
import re
import jsonschema
from jsonschema import validate

logger = logging.getLogger(__name__)

# Rule schema definition
RULE_SCHEMA = {
    "type": "object",
    "required": ["name", "dataset_id", "condition"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "dataset_id": {"type": "string"},
        "condition": {"type": ["string", "object"]},
        "rule_type": {"type": "string", "enum": ["validation", "transformation", "enrichment"]},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "source": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "model_generated": {"type": "boolean"},
        "execution_order": {"type": "integer"},
        "active": {"type": "boolean"},
        "metadata": {"type": "object"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
        "execution_count": {"type": "integer"},
        "success_count": {"type": "integer"},
        "success_rate": {"type": "number"},
        "last_executed": {"type": "string"}
    },
    "additionalProperties": True
}

async def validate_rule_format(rule_data: Dict[str, Any]) -> bool:
    """
    Validate the format of a business rule.
    
    Args:
        rule_data: Dictionary containing rule information
        
    Returns:
        True if the rule format is valid, False otherwise
    """
    try:
        # Validate against schema
        validate(instance=rule_data, schema=RULE_SCHEMA)
        
        # Set defaults for optional fields
        rule_data.setdefault("rule_type", "validation")
        rule_data.setdefault("severity", "medium")
        rule_data.setdefault("source", "manual")
        rule_data.setdefault("active", True)
        rule_data.setdefault("model_generated", False)
        rule_data.setdefault("execution_order", 0)
        rule_data.setdefault("tags", [])
        rule_data.setdefault("metadata", {})
        rule_data.setdefault("execution_count", 0)
        rule_data.setdefault("success_count", 0)
        rule_data.setdefault("success_rate", 0.0)
        
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Rule validation error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating rule format: {str(e)}")
        return False

async def validate_rule_condition(condition: Union[str, Dict[str, Any]]) -> bool:
    """
    Validate a rule condition.
    
    Args:
        condition: Rule condition (string or dictionary)
        
    Returns:
        True if the condition is valid, False otherwise
    """
    try:
        # Handle different condition types
        if isinstance(condition, dict):
            # Validate dictionary structure
            return True
        elif isinstance(condition, str):
            # Validate Python syntax for string conditions
            try:
                ast.parse(condition)
                return True
            except SyntaxError:
                # Check if it's a Great Expectations expectation
                if condition.startswith("expect_"):
                    return True
                # Check if it's a JSON string
                try:
                    json.loads(condition)
                    return True
                except json.JSONDecodeError:
                    pass
                    
                logger.error(f"Invalid condition syntax: {condition}")
                return False
        else:
            logger.error(f"Unsupported condition type: {type(condition)}")
            return False
    except Exception as e:
        logger.error(f"Error validating rule condition: {str(e)}")
        return False

async def validate_rule_dependencies(rule: Dict[str, Any], dataset_id: str) -> Dict[str, Any]:
    """
    Validate rule dependencies.
    
    Args:
        rule: Rule dictionary
        dataset_id: ID of the dataset
        
    Returns:
        Dictionary with validation results
    """
    try:
        # Extract dependencies from condition
        dependencies = []
        
        # Check for column references in the condition
        if isinstance(rule["condition"], str):
            # Extract column references using regex
            column_refs = re.findall(r'df\[[\'"](.*?)[\'"]\]', rule["condition"])
            dependencies.extend([{"type": "column", "name": col} for col in column_refs])
            
            # Extract other rule references
            rule_refs = re.findall(r'apply_rule\([\'"](.*)[\'"]\)', rule["condition"])
            dependencies.extend([{"type": "rule", "id": rule_id} for rule_id in rule_refs])
        
        # Import here to avoid circular imports
        from api.repositories import business_rules_repository
        
        # Validate rule dependencies
        missing_deps = []
        for dep in dependencies:
            if dep["type"] == "column":
                # Check if column exists in dataset
                # This would require a dataset service or repository
                pass
            elif dep["type"] == "rule":
                # Check if referenced rule exists
                dep_rule = await business_rules_repository.get_rule(dep["id"])
                if not dep_rule:
                    missing_deps.append(dep)
        
        return {
            "valid": len(missing_deps) == 0,
            "dependencies": dependencies,
            "missing_dependencies": missing_deps
        }
    except Exception as e:
        logger.error(f"Error validating rule dependencies: {str(e)}")
        return {
            "valid": False,
            "dependencies": [],
            "missing_dependencies": [],
            "error": str(e)
        }

async def validate_rule_circular_dependencies(rule_id: str, dataset_id: str) -> Dict[str, Any]:
    """
    Check for circular dependencies in rules.
    
    Args:
        rule_id: ID of the rule to check
        dataset_id: ID of the dataset
        
    Returns:
        Dictionary with validation results
    """
    try:
        # Import here to avoid circular imports
        from api.repositories import business_rules_repository
        
        # Get rule
        rule = await business_rules_repository.get_rule(rule_id)
        if not rule:
            return {"valid": False, "error": "Rule not found"}
            
        # Initialize visited set and path
        visited = set()
        path = []
        
        # DFS to find cycles
        async def dfs(current_id):
            if current_id in path:
                # Found a cycle
                cycle_start = path.index(current_id)
                return False, path[cycle_start:]
                
            if current_id in visited:
                # Already visited, no cycle found
                return True, []
                
            # Mark as visited and add to path
            visited.add(current_id)
            path.append(current_id)
            
            # Get current rule
            current_rule = await business_rules_repository.get_rule(current_id)
            if not current_rule:
                # Rule not found, skip
                path.pop()
                return True, []
                
            # Extract rule references
            if isinstance(current_rule["condition"], str):
                rule_refs = re.findall(r'apply_rule\([\'"](.*)[\'"]\)', current_rule["condition"])
                
                # Check each dependency
                for dep_id in rule_refs:
                    valid, cycle = await dfs(dep_id)
                    if not valid:
                        return False, cycle
            
            # Remove from path
            path.pop()
            return True, []
            
        # Start DFS from the rule
        valid, cycle = await dfs(rule_id)
        
        return {
            "valid": valid,
            "circular_dependencies": cycle if not valid else []
        }
    except Exception as e:
        logger.error(f"Error checking circular dependencies: {str(e)}")
        return {
            "valid": False,
            "circular_dependencies": [],
            "error": str(e)
        }
