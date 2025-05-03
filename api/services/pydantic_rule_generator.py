"""
Pydantic Rule Generator Module

Generates advanced business rules using Pydantic models. Rules are generic and adapt to any loaded data.
"""
from typing import Dict, Any, List
from pydantic import create_model, ValidationError
import logging

logger = logging.getLogger(__name__)

def generate_rules(dataset_id: str, column_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate validation rules using dynamic Pydantic models for each column.
    Returns a list of rule dicts describing the checks.
    """
    rules = []
    for col, meta in column_metadata.items():
        rule = {
            "column": col,
            "type": meta.get("type"),
            "nullable": meta.get("nullable", True),
            "description": f"Pydantic validation for {col}"
        }
        # Add range/type constraints if available
        if "min" in meta or "max" in meta:
            rule["range"] = {k: meta[k] for k in ("min", "max") if k in meta}
        rules.append(rule)
    return rules
